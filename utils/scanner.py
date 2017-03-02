import time

from ev3dev.auto import Motor, InfraredSensor, UltrasonicSensor


class ScannerPropulsion:
    def __init__(self, motor: Motor, gear_ratio: float):
        self.motor = motor
        self.connected = motor.connected

        self.gear_ratio = gear_ratio
        self.motor_tacho_ratio = motor.count_per_rot / 360 if motor.connected else 1
        self.total_ratio = self.gear_ratio * self.motor_tacho_ratio


class ScannerHead:
    def __init__(self, ir_sensor=None, ultrasonic_sensor=None):
        if ir_sensor is None:
            ir_sensor = InfraredSensor()
        if ultrasonic_sensor is None:
            ultrasonic_sensor = UltrasonicSensor()

        if ultrasonic_sensor.connected:
            ultrasonic_sensor.mode = 'US-DIST-CM'
            self.distance_sensor = ultrasonic_sensor
            self.has_distance_sensor = True
            self.max_distance = 255 if ultrasonic_sensor.driver_name is not 'lego-ev3-us' else 2550
        elif ir_sensor.connected:
            ir_sensor.mode = 'IR-PROX'
            self.distance_sensor = ir_sensor
            self.has_distance_sensor = True
            self.max_distance = 100
        else:
            self.distance_sensor = None
            self.has_distance_sensor = False
            self.max_distance = -1


class Scanner:
    def __init__(self, scanner_propulsion: ScannerPropulsion, scanner_head: ScannerHead):
        self._scanner_propulsion = scanner_propulsion
        if self._scanner_propulsion.connected:
            self._scanner_propulsion.motor.stop_action = 'brake'
        self._scanner_head = scanner_head

    def reset(self):
        if self._scanner_propulsion.connected:
            self._scanner_propulsion.motor.stop_action = 'brake'
            self.rotate_scanner_to_pos(0, speed=self._scanner_propulsion.motor.max_speed / 10)
            self.wait_to_scanner_stop()
            self._scanner_propulsion.motor.reset()

    def rotate_scanner_to_pos(self, angle, speed=None):  # TODO: own regulator and method as target
        motor = self._scanner_propulsion.motor
        motor.run_to_abs_pos(speed_sp=
                             motor.max_speed / 5 if speed is None else speed * self._scanner_propulsion.total_ratio,
                             position_sp=angle * self._scanner_propulsion.total_ratio)

    def is_connected(self):
        return self._scanner_head.has_distance_sensor

    def has_motor(self):
        return self._scanner_propulsion.connected

    def is_running(self):
        return 'running' in self._scanner_propulsion.motor.state

    def value_max(self):
        return self._scanner_head.max_distance

    def repeat_while_scanner_running(self, method):
        while self.is_running():
            method()

    def wait_to_scanner_stop(self):
        self.repeat_while_scanner_running(lambda: time.sleep(0))

    def value_get(self, percent=True):
        if percent:
            return self._scanner_head.distance_sensor.value() / self._scanner_head.max_distance * 100
        return self._scanner_head.distance_sensor.value()

    def angle_get(self):
        return self._scanner_propulsion.motor.position / self._scanner_propulsion.total_ratio

    def value_scan(self, angle=0, percent=True):
        if self.angle_get() != angle:
            self.rotate_scanner_to_pos(angle)
            self.wait_to_scanner_stop()
        return self.value_get(percent)

    def value_scan_continuous(self, to_angle, value_handler, percent=True):
        self.rotate_scanner_to_pos(to_angle)
        self.repeat_while_scanner_running(lambda: value_handler(self.value_get(percent), self.angle_get()))
