import time

from ev3dev.auto import Motor, InfraredSensor, UltrasonicSensor


class ScannerPropulsion:
    def __init__(self, motor: Motor, gear_ratio: float):
        self.motor = motor

        self.gear_ratio = gear_ratio
        self.motor_tacho_ratio = motor.count_per_rot / 360 if motor.connected else 1
        self.total_ratio = self.gear_ratio * self.motor_tacho_ratio


class Scanner:
    def __init__(self, scanner_propulsion: ScannerPropulsion):
        self._scanner_propulsion = scanner_propulsion
        self._has_scanner_motor = scanner_propulsion.motor.connected
        if self._has_scanner_motor:
            self._scanner_propulsion.motor.stop_action = 'brake'

        ir_sensor = InfraredSensor()
        ultrasonic_sensor = UltrasonicSensor()
        if ultrasonic_sensor.connected:
            ultrasonic_sensor.mode = 'US-DIST-CM'
            self._distance_sensor = ultrasonic_sensor
            self._has_distance_sensor = True
            self._max_distance = 255
        elif ir_sensor.connected:
            ir_sensor.mode = 'IR-PROX'
            self._distance_sensor = ir_sensor
            self._has_distance_sensor = True
            self._max_distance = 100
        else:
            self._distance_sensor = None
            self._has_distance_sensor = False
            self._max_distance = -1

    def reset(self):
        if self._has_scanner_motor:
            self._scanner_propulsion.motor.stop_action = 'brake'
            self.rotate_scanner_to_pos(0, speed=self._scanner_propulsion.motor.max_speed / 10)
            self.wait_to_scanner_stop()
            self._scanner_propulsion.motor.reset()

    def rotate_scanner_to_pos(self, angle, speed=None):  # TODO: own regulator and method as target
        motor = self._scanner_propulsion.motor
        motor.run_to_abs_pos(speed_sp=motor.max_speed / 5 if speed is None else
        speed * self._scanner_propulsion.total_ratio,
                             position_sp=angle * self._scanner_propulsion.total_ratio)

    def is_connected(self):
        return self._has_distance_sensor

    def has_motor(self):
        return self._has_scanner_motor

    def is_running(self):
        return 'running' in self._scanner_propulsion.motor.state

    def value_max(self):
        return self._max_distance

    def repeat_while_scanner_running(self, method):
        while self.is_running():
            method()

    def wait_to_scanner_stop(self):
        self.repeat_while_scanner_running(lambda: time.sleep(0.05))

    def value_get(self, percent=True):
        if percent:
            return self._distance_sensor.value() / self._max_distance * 100
        return self._distance_sensor.value()

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
