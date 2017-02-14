from ev3dev.auto import *

from config import *

LEFT_MOTOR = LargeMotor(ROBOT_MOTOR_WHEELS_LEFT_PORT)
RIGHT_MOTOR = LargeMotor(ROBOT_MOTOR_WHEELS_RIGHT_PORT)
HAS_WHEELS = LEFT_MOTOR.connected and RIGHT_MOTOR.connected
if HAS_WHEELS:
    LEFT_MOTOR.reset()
    RIGHT_MOTOR.reset()

COLOR_SENSOR = ColorSensor()
HAS_COLOR_SENSOR = COLOR_SENSOR.connected
if HAS_COLOR_SENSOR:
    COLOR_SENSOR.mode = 'COL-REFLECT'

SCANNER_MOTOR = MediumMotor(ROBOT_MOTOR_SCANNER_PORT)
HAS_SCANNER_MOTOR = SCANNER_MOTOR.connected
if HAS_SCANNER_MOTOR:
    SCANNER_MOTOR.stop_action = 'brake'

IR_SENSOR = InfraredSensor()
ULTRASONIC_SENSOR = UltrasonicSensor()
if ULTRASONIC_SENSOR.connected:
    ULTRASONIC_SENSOR.mode = 'US-DIST-CM'
    DISTANCE_SENSOR = ULTRASONIC_SENSOR
    HAS_DISTANCE_SENSOR = True
    MAX_DISTANCE = 255
elif IR_SENSOR.connected:
    IR_SENSOR.mode = 'IR-PROX'
    DISTANCE_SENSOR = IR_SENSOR
    HAS_DISTANCE_SENSOR = True
    MAX_DISTANCE = 100
else:
    DISTANCE_SENSOR = None
    HAS_DISTANCE_SENSOR = False
    MAX_DISTANCE = -1


def reset_hardware():
    if HAS_WHEELS:
        LEFT_MOTOR.reset()
        RIGHT_MOTOR.reset()

    if HAS_SCANNER_MOTOR and SCANNER_MOTOR.position != 0:
        SCANNER_MOTOR.run_to_abs_pos(speed_sp=SCANNER_MOTOR.max_speed / 10, position_sp=0)
        while 'running' in SCANNER_MOTOR.state:
            pass
        SCANNER_MOTOR.stop_action = 'coast'
        SCANNER_MOTOR.stop()
        SCANNER_MOTOR.stop_action = 'brake'


class Regulator:
    def __init__(self, const_p=None, const_d=None, const_i=None, const_target=None,
                 getter_p=None, getter_d=None, getter_i=None, getter_target=None):
        self.const_p = const_p
        self.const_d = const_d
        self.const_i = const_i
        self.const_target = const_target

        self.getter_p = getter_p
        self.getter_d = getter_d
        self.getter_i = getter_i
        self.getter_target = getter_target

        self.tmp_error = 0
        self.integral = 0

    def reset(self):
        self.tmp_error = 0
        self.integral = 0

    def get_p(self):
        result = self.getter_p() if self.getter_p is not None else None
        return result if result is not None else self.const_p

    def get_d(self):
        result = self.getter_d() if self.getter_d is not None else None
        return result if result is not None else self.const_d

    def get_i(self):
        result = self.getter_i() if self.getter_i is not None else None
        return result if result is not None else self.const_i

    def get_target(self):
        result = self.getter_target() if self.getter_target is not None else None
        return result if result is not None else self.const_target

    def regulate(self, input_val):
        input_val = min(100, max(-100, input_val))
        target = self.get_target()
        max_positive_error = abs(100 - target) * 0.6
        max_negative_error = abs(-target) * 0.6

        error = target - input_val
        max_error = max_negative_error if error < 0 else max_positive_error
        error *= 100 / max_error

        derivative, self.tmp_error = error - self.tmp_error, error

        integral = float(0.5) * self.integral + error
        self.integral = integral

        return self.get_p() * error + self.get_d() * derivative + self.get_i() * integral
