from ev3dev.auto import *

from config import *

LEFT_MOTOR = LargeMotor(ROBOT_MOTOR_WHEELS_LEFT_PORT)
RIGHT_MOTOR = LargeMotor(ROBOT_MOTOR_WHEELS_RIGHT_PORT)
HAS_WHEELS = LEFT_MOTOR.connected and RIGHT_MOTOR.connected


def reset_wheels():
    if HAS_WHEELS:
        LEFT_MOTOR.reset()
        RIGHT_MOTOR.reset()
        LEFT_MOTOR.stop_action = 'brake'
        RIGHT_MOTOR.stop_action = 'brake'


reset_wheels()

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
    reset_wheels()

    if HAS_SCANNER_MOTOR and SCANNER_MOTOR.position != 0:
        SCANNER_MOTOR.stop_action = 'brake'
        SCANNER_MOTOR.run_to_abs_pos(speed_sp=SCANNER_MOTOR.max_speed / 10, position_sp=0)
        while 'running' in SCANNER_MOTOR.state:
            pass
        SCANNER_MOTOR.reset()
        SCANNER_MOTOR.stop_action = 'brake'

        if HAS_COLOR_SENSOR:
            COLOR_SENSOR.mode = 'COL-REFLECT'
