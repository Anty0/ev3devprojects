from ev3dev.auto import LargeMotor, MediumMotor, ColorSensor

from config import *
from utils.pilot import Pilot
from utils.scanner import Scanner, ScannerPropulsion
from utils.wheel import Wheel

LEFT_WHEEL = Wheel(LargeMotor(ROBOT_MOTOR_WHEEL_LEFT_PORT), ROBOT_MOTOR_WHEEL_LEFT_GEAR_RATIO,
                   ROBOT_MOTOR_WHEEL_LEFT_DIAMETER, ROBOT_MOTOR_WHEEL_LEFT_WIDTH, ROBOT_MOTOR_WHEEL_LEFT_OFFSET)
RIGHT_WHEEL = Wheel(LargeMotor(ROBOT_MOTOR_WHEEL_RIGHT_PORT), ROBOT_MOTOR_WHEEL_RIGHT_GEAR_RATIO,
                    ROBOT_MOTOR_WHEEL_RIGHT_DIAMETER, ROBOT_MOTOR_WHEEL_RIGHT_WIDTH, ROBOT_MOTOR_WHEEL_RIGHT_OFFSET)
PILOT = Pilot([LEFT_WHEEL, RIGHT_WHEEL])

COLOR_SENSOR = ColorSensor()
HAS_COLOR_SENSOR = COLOR_SENSOR.connected
if HAS_COLOR_SENSOR:
    COLOR_SENSOR.mode = 'COL-REFLECT'

SCANNER_PROPULSION = ScannerPropulsion(MediumMotor(ROBOT_MOTOR_SCANNER_PORT), ROBOT_MOTOR_SCANNER_GEAR_RATIO)
SCANNER = Scanner(SCANNER_PROPULSION)


def reset_hardware():
    PILOT.reset()
    SCANNER.reset()
    if HAS_COLOR_SENSOR:
        COLOR_SENSOR.mode = 'COL-REFLECT'
