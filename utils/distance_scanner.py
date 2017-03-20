import time

from ev3dev.auto import Motor, InfraredSensor, UltrasonicSensor

from utils.value_reader import ValueReader


class DistanceScannerPropulsion:
    def __init__(self, motor: Motor, gear_ratio: float):
        self.motor = motor
        self.connected = motor.connected

        self.gear_ratio = gear_ratio
        self.motor_tacho_ratio = motor.count_per_rot / 360 if motor.connected else 1
        self.total_ratio = self.gear_ratio * self.motor_tacho_ratio

    def reset(self):
        if not self.connected:
            return
        self.motor.stop_action = Motor.STOP_ACTION_BRAKE
        self.rotate_to_pos(0, speed=self.motor.max_speed / 10)
        self.wait_to_stop()
        self.rotate_to_pos(0, speed=self.motor.max_speed / 10)
        self.wait_to_stop()
        self.motor.reset()
        self.motor.stop_action = Motor.STOP_ACTION_BRAKE
        self.motor.ramp_up_sp = self.motor.max_speed / 2
        self.motor.ramp_down_sp = self.motor.max_speed / 2

    @property
    def is_running(self):
        return Motor.STATE_RUNNING in self.motor.state

    def angle_get(self):
        return self.motor.position / self.total_ratio

    def rotate_to_pos(self, angle, speed=None):  # TODO: own regulator and method as target
        self.motor.run_to_abs_pos(speed_sp=self.motor.max_speed if speed is None else speed * self.total_ratio,
                                  position_sp=angle * self.total_ratio)

    def repeat_while_running(self, method):
        while self.is_running:
            method()

    def wait_to_stop(self):
        self.repeat_while_running(lambda: time.sleep(0.05))


class DistanceScannerHead:
    def __init__(self, ir_sensor=None, ultrasonic_sensor=None):
        if ir_sensor is None:
            ir_sensor = InfraredSensor()
        if ultrasonic_sensor is None:
            ultrasonic_sensor = UltrasonicSensor()

        if ultrasonic_sensor.connected:
            ultrasonic_sensor.mode = UltrasonicSensor.MODE_US_DIST_CM
            self.distance_sensor = ultrasonic_sensor
            self.value_reader = ValueReader(ultrasonic_sensor)

            def reset():
                self.distance_sensor.mode = UltrasonicSensor.MODE_US_DIST_CM
                self.value_reader.reload()

            self.has_distance_sensor = True
            self.max_distance = 255 if ultrasonic_sensor.driver_name is not 'lego-ev3-us' else 2550
            self.to_cm_mul = 1 if ultrasonic_sensor.driver_name is not 'lego-ev3-us' else 0.1
        elif ir_sensor.connected:
            ir_sensor.mode = InfraredSensor.MODE_IR_PROX
            self.distance_sensor = ir_sensor
            self.value_reader = ValueReader(ir_sensor)

            def reset():
                self.distance_sensor.mode = InfraredSensor.MODE_IR_PROX
                self.value_reader.reload()

            self.has_distance_sensor = True
            self.max_distance = 100
            self.to_cm_mul = 0.7
        else:
            self.distance_sensor = None
            self.value_reader = None

            def reset():
                pass

            self.has_distance_sensor = False
            self.max_distance = -1
            self.to_cm_mul = 0

        self.reset = reset

    def value_get(self, percent=True, force_new=False):
        if percent:
            return self.value_reader.value(force_new=force_new) / self.max_distance * 100
        return self.value_reader.value(force_new=force_new) * self.to_cm_mul


class DistanceScanner:
    def __init__(self, scanner_propulsion: DistanceScannerPropulsion, scanner_head: DistanceScannerHead):
        self._scanner_propulsion = scanner_propulsion
        self._scanner_head = scanner_head
        self.reset()

    def reset(self):
        self._scanner_head.reset()
        self._scanner_propulsion.reset()

    def rotate_scanner_to_pos(self, angle, speed=None):
        self._scanner_propulsion.rotate_to_pos(angle, speed)

    @property
    def is_connected(self):
        return self._scanner_head.has_distance_sensor

    @property
    def has_motor(self):
        return self._scanner_propulsion.connected

    @property
    def is_running(self):
        return self._scanner_propulsion.is_running

    @property
    def value_max(self):
        return self._scanner_head.max_distance * self._scanner_head.to_cm_mul

    def repeat_while_scanner_running(self, method):
        self._scanner_propulsion.repeat_while_running(method)

    def wait_to_scanner_stop(self):
        self._scanner_propulsion.wait_to_stop()

    def value_get(self, percent=True, force_new=False):
        return self._scanner_head.value_get(percent, force_new)

    def angle_get(self):
        return self._scanner_propulsion.angle_get()

    def value_scan(self, angle=0, percent=True):
        if self.angle_get() != angle:
            self.rotate_scanner_to_pos(angle)
            self.wait_to_scanner_stop()
        return self.value_get(percent, True)

    def value_scan_continuous(self, to_angle, value_handler, percent=True):
        self.rotate_scanner_to_pos(to_angle)
        self._scanner_head.value_reader.pause()
        self.repeat_while_scanner_running(lambda: value_handler(self.value_get(percent, True), self.angle_get()))
        self._scanner_head.value_reader.resume()
