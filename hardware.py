from ev3dev.auto import Sound, Motor, LargeMotor, MediumMotor, Sensor, ColorSensor, InfraredSensor, UltrasonicSensor, \
    INPUT_3, INPUT_4

from config import *
from utils.distance_scanner import DistanceScanner, DistanceScannerPropulsion, DistanceScannerHead
from utils.pilot import Pilot
from utils.position import Position2D
from utils.simulation.controller import Controller, RobotInfo, Map
from utils.simulation.hardware import SimLargeMotor, SimMediumMotor, \
    SimColorSensor, SimInfraredSensor, SimUltrasonicSensor
from utils.simulation.interface import EV3LargeMotorInterface, EV3MediumMotorInterface, \
    EV3ColorSensorInterface, EV3InfraredSensorInterface
from utils.simulation.simulator import get_base_ev3_devices, build_simulator
from utils.value_reader import ValueReader
from utils.wheel import Wheel

DEVICES_INTERFACES = [
                         EV3LargeMotorInterface(Position2D(ROBOT_MOTOR_WHEEL_LEFT_OFFSET_X, 0, 0),
                                                ROBOT_MOTOR_WHEEL_LEFT_PORT),
                         EV3LargeMotorInterface(Position2D(ROBOT_MOTOR_WHEEL_RIGHT_OFFSET_X, 0, 0),
                                                ROBOT_MOTOR_WHEEL_RIGHT_PORT),
                         EV3MediumMotorInterface(Position2D(0, 0, 90), ROBOT_MOTOR_SCANNER_PORT),
                         EV3InfraredSensorInterface(Position2D(ROBOT_SENSOR_DISTANCE_OFFSET_X,
                                                               ROBOT_SENSOR_DISTANCE_OFFSET_Y, 0), INPUT_4),
                         EV3ColorSensorInterface(
                             Position2D(ROBOT_SENSOR_COLOR_OFFSET_X, ROBOT_SENSOR_COLOR_OFFSET_Y, 0), INPUT_3)
                     ] + get_base_ev3_devices(Position2D(ROBOT_BRICK_OFFSET_X, ROBOT_BRICK_OFFSET_Y, 0))

CONTROLLER = Controller(RobotInfo(*DEVICES_INTERFACES), Map())

if SIMULATION_MODE:
    SIM_ENV = build_simulator(CONTROLLER, *DEVICES_INTERFACES)

    LEFT_MOTOR = SimLargeMotor(SIM_ENV, ROBOT_MOTOR_WHEEL_LEFT_PORT)
    RIGHT_MOTOR = SimLargeMotor(SIM_ENV, ROBOT_MOTOR_WHEEL_RIGHT_PORT)

    COLOR_SENSOR = SimColorSensor(SIM_ENV)

    SCANNER_MOTOR = SimMediumMotor(SIM_ENV, ROBOT_MOTOR_SCANNER_PORT)
    INFRARED_SENSOR = SimInfraredSensor(SIM_ENV)
    ULTRASONIC_SENSOR = SimUltrasonicSensor(SIM_ENV)

    CONTROLLER.prepare_devices(SIM_ENV)
else:
    LEFT_MOTOR = LargeMotor(ROBOT_MOTOR_WHEEL_LEFT_PORT)
    RIGHT_MOTOR = LargeMotor(ROBOT_MOTOR_WHEEL_RIGHT_PORT)

    COLOR_SENSOR = ColorSensor()

    SCANNER_MOTOR = MediumMotor(ROBOT_MOTOR_SCANNER_PORT)
    INFRARED_SENSOR = InfraredSensor()
    ULTRASONIC_SENSOR = UltrasonicSensor()

    CONTROLLER.prepare_devices()

LEFT_WHEEL = Wheel(LEFT_MOTOR, ROBOT_MOTOR_WHEEL_LEFT_GEAR_RATIO, ROBOT_MOTOR_WHEEL_LEFT_DIAMETER,
                   ROBOT_MOTOR_WHEEL_LEFT_WIDTH, ROBOT_MOTOR_WHEEL_LEFT_OFFSET_X)
RIGHT_WHEEL = Wheel(RIGHT_MOTOR, ROBOT_MOTOR_WHEEL_RIGHT_GEAR_RATIO, ROBOT_MOTOR_WHEEL_RIGHT_DIAMETER,
                    ROBOT_MOTOR_WHEEL_RIGHT_WIDTH, ROBOT_MOTOR_WHEEL_RIGHT_OFFSET_X)
PILOT = Pilot(LEFT_WHEEL, RIGHT_WHEEL)

HAS_COLOR_SENSOR = COLOR_SENSOR.connected
if HAS_COLOR_SENSOR:
    COLOR_SENSOR.mode = ColorSensor.MODE_COL_REFLECT
    COLOR_SENSOR_READER = ValueReader(COLOR_SENSOR)
else:
    COLOR_SENSOR_READER = None

SCANNER_PROPULSION = DistanceScannerPropulsion(SCANNER_MOTOR, ROBOT_MOTOR_SCANNER_GEAR_RATIO)
SCANNER_HEAD = DistanceScannerHead(INFRARED_SENSOR, ULTRASONIC_SENSOR)
SCANNER = DistanceScanner(SCANNER_PROPULSION, SCANNER_HEAD)

SOUND = Sound


def reset_hardware():
    if HAS_COLOR_SENSOR:
        COLOR_SENSOR_READER.mode(ColorSensor.MODE_COL_REFLECT)
    PILOT.reset()
    SCANNER.reset()


def generate_hardware_status_obj():
    def motor_status(motor: Motor):
        return {'position': motor.position, 'speed': motor.speed, 'state': motor.state}

    def sensor_status(sensor: Sensor):
        return {'mode': sensor.mode, 'values': [sensor.value(n) for n in range(sensor.num_values)]}

    config_status = {
        'simulated': SIMULATION_MODE
    }

    wheels_status = {}
    for wheel in (LEFT_WHEEL, RIGHT_WHEEL):
        wheels_status[wheel.motor.address] = motor_status(wheel.motor) if wheel.motor.connected else None

    scanner_status = {
        'motor': motor_status(SCANNER_PROPULSION.motor) if SCANNER_PROPULSION.connected else None,
        'head': sensor_status(SCANNER_HEAD.distance_sensor) if SCANNER_HEAD.has_distance_sensor else None
    }

    sensors_status = {}
    for sensor in [COLOR_SENSOR]:
        sensors_status[sensor.address] = sensor_status(sensor) if sensor.connected else None
    return {
        'config': config_status,
        'wheels': wheels_status,
        'scanner': scanner_status,
        'sensors': sensors_status
    }
