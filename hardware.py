from ev3dev.auto import LargeMotor, MediumMotor, ColorSensor, InfraredSensor, UltrasonicSensor, INPUT_3, INPUT_4

from config import *
from utils.pilot import Pilot
from utils.position import Position2D
from utils.scanner import Scanner, ScannerPropulsion, ScannerHead
from utils.simulation.controller import Controller, RobotInfo, Map
from utils.simulation.hardware import SimLargeMotor, SimMediumMotor, \
    SimColorSensor, SimInfraredSensor, SimUltrasonicSensor
from utils.simulation.interface import EV3LargeMotorInterface, EV3MediumMotorInterface, \
    EV3ColorSensorInterface, EV3InfraredSensorInterface
from utils.simulation.simulator import build_ev3_simulator
from utils.wheel import Wheel

CONTROLLER = Controller(RobotInfo(), Map())

if SIMULATION_MODE:
    DEVICES_INTERFACES = [
        EV3LargeMotorInterface(Position2D(ROBOT_MOTOR_WHEEL_LEFT_OFFSET, 0, 0), ROBOT_MOTOR_WHEEL_LEFT_PORT),
        EV3LargeMotorInterface(Position2D(ROBOT_MOTOR_WHEEL_RIGHT_OFFSET, 0, 0), ROBOT_MOTOR_WHEEL_RIGHT_PORT),
        EV3MediumMotorInterface(Position2D(0, 0, 90), ROBOT_MOTOR_SCANNER_PORT),
        EV3InfraredSensorInterface(Position2D(0, 10.5, 0), INPUT_4),
        EV3ColorSensorInterface(Position2D(0, 7.5, 0), INPUT_3)
    ]
    SIMULATED_ENVIRONMENT = build_ev3_simulator(CONTROLLER, Position2D(ROBOT_BRICK_POSITION_X,
                                                                       ROBOT_BRICK_POSITION_Y, 0),
                                                *DEVICES_INTERFACES)

    LEFT_MOTOR = SimLargeMotor(SIMULATED_ENVIRONMENT, ROBOT_MOTOR_WHEEL_LEFT_PORT)
    RIGHT_MOTOR = SimLargeMotor(SIMULATED_ENVIRONMENT, ROBOT_MOTOR_WHEEL_RIGHT_PORT)

    COLOR_SENSOR = SimColorSensor(SIMULATED_ENVIRONMENT)

    SCANNER_MOTOR = SimMediumMotor(SIMULATED_ENVIRONMENT, ROBOT_MOTOR_SCANNER_PORT)
    SCANNER_HEAD = ScannerHead(SimInfraredSensor(SIMULATED_ENVIRONMENT), SimUltrasonicSensor(SIMULATED_ENVIRONMENT))
else:
    LEFT_MOTOR = LargeMotor(ROBOT_MOTOR_WHEEL_LEFT_PORT)
    RIGHT_MOTOR = LargeMotor(ROBOT_MOTOR_WHEEL_RIGHT_PORT)

    COLOR_SENSOR = ColorSensor()

    SCANNER_MOTOR = MediumMotor(ROBOT_MOTOR_SCANNER_PORT)
    SCANNER_HEAD = ScannerHead(InfraredSensor(), UltrasonicSensor())

LEFT_WHEEL = Wheel(LEFT_MOTOR, ROBOT_MOTOR_WHEEL_LEFT_GEAR_RATIO, ROBOT_MOTOR_WHEEL_LEFT_DIAMETER,
                   ROBOT_MOTOR_WHEEL_LEFT_WIDTH, ROBOT_MOTOR_WHEEL_LEFT_OFFSET)
RIGHT_WHEEL = Wheel(RIGHT_MOTOR, ROBOT_MOTOR_WHEEL_RIGHT_GEAR_RATIO, ROBOT_MOTOR_WHEEL_RIGHT_DIAMETER,
                    ROBOT_MOTOR_WHEEL_RIGHT_WIDTH, ROBOT_MOTOR_WHEEL_RIGHT_OFFSET)
PILOT = Pilot([LEFT_WHEEL, RIGHT_WHEEL])

HAS_COLOR_SENSOR = COLOR_SENSOR.connected
if HAS_COLOR_SENSOR:
    COLOR_SENSOR.mode = 'COL-REFLECT'

SCANNER_PROPULSION = ScannerPropulsion(SCANNER_MOTOR, ROBOT_MOTOR_SCANNER_GEAR_RATIO)
SCANNER = Scanner(SCANNER_PROPULSION, SCANNER_HEAD)

CONTROLLER.register_leds()  # TODO: create info class
CONTROLLER.register_sensors()  # TODO: create info class
CONTROLLER.register_wheels(LEFT_WHEEL, RIGHT_WHEEL)


def reset_hardware():
    PILOT.reset()
    SCANNER.reset()
    if HAS_COLOR_SENSOR:
        COLOR_SENSOR.mode = 'COL-REFLECT'
