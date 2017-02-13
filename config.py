import logging
import sys

from ev3dev.auto import OUTPUT_A, OUTPUT_B, OUTPUT_C
from odict.pyodict import odict

root = logging.getLogger()
root.setLevel(logging.DEBUG)

# Enable logging output
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

log = logging.getLogger(__name__)

# Server
SERVER_PORT = 8000

# Robot
ROBOT_MOTOR_LEFT_PORT = OUTPUT_B
ROBOT_MOTOR_RIGHT_PORT = OUTPUT_C
ROBOT_MOTOR_SCANNER_PORT = OUTPUT_A
ROBOT_MOTOR_SCANNER_GEAR_RATIO = 20 / 12

# Line follower
LINE_FOLLOWER_TARGET_CYCLE_TIME = 0.01
LINE_FOLLOWER_TARGET_POWER = 100
LINE_FOLLOWER_TARGET_REFLECT = 55  # 65  # None = center
LINE_FOLLOWER_REG_STEER_P = float(1)  # Proportional gain. Start value 1
LINE_FOLLOWER_REG_STEER_D = float(0)  # Derivative gain. Start value 0
LINE_FOLLOWER_REG_STEER_I = float(0)  # Integral gain. Start value 0
LINE_FOLLOWER_LINE_SIDE = -1  # -1 == left; 1 == right
LINE_FOLLOWER_OBSTACLE_AVOID = False  # TODO: add support
LINE_FOLLOWER_OBSTACLE_AVOID_SIDE = -1  # -1 == left; 1 == right
LINE_FOLLOWER_COLLISION_AVOID = False  # TODO: add support
LINE_FOLLOWER_SHARP_TURN_DETECT = False  # TODO: add support
LINE_FOLLOWER_SHARP_TURN_ROTATE_SIDE = -1  # -1 == left; 1 == right
LINE_FOLLOWER_STOP_ON_PATH_END = False  # TODO: add support
config_values = odict()
config_values['REG_STEER_P'] = {
    'display_name': 'Regulator STEER-P',
    'type': 'float',
    'default_value': LINE_FOLLOWER_REG_STEER_P
}
config_values['REG_STEER_D'] = {
    'display_name': 'Regulator STEER-D',
    'type': 'float',
    'default_value': LINE_FOLLOWER_REG_STEER_D
}
config_values['REG_STEER_I'] = {
    'display_name': 'Regulator STEER-I',
    'type': 'float',
    'default_value': LINE_FOLLOWER_REG_STEER_I
}
config_values['PAUSE_POWER'] = {
    'display_name': 'Pause',
    'type': 'bool',
    'default_value': False
}
config_values['TARGET_POWER'] = {
    'display_name': 'Target power',
    'type': 'int',
    'default_value': LINE_FOLLOWER_TARGET_POWER
}
config_values['TARGET_REFLECT'] = {
    'display_name': 'Target reflect',
    'type': 'int',
    'default_value': LINE_FOLLOWER_TARGET_REFLECT
}
config_values['TARGET_CYCLE_TIME'] = {
    'display_name': 'Target cycle time',
    'type': 'float',
    'default_value': LINE_FOLLOWER_TARGET_CYCLE_TIME
}
config_values['LINE_SIDE'] = {
    'display_name': 'Line side',
    'type': 'int',  # TODO: add enum support and use it here
    'default_value': LINE_FOLLOWER_LINE_SIDE
}
config_values['DETECT_REFLECT'] = {
    'display_name': 'Auto detect reflection',
    'type': 'bool',
    'default_value': True
}
config_values['MIN_REFLECT'] = {
    'display_name': 'Minimal reflect',
    'type': 'int',
    'default_value': 0
}
config_values['MAX_REFLECT'] = {
    'display_name': 'Maximal reflect',
    'type': 'int',
    'default_value': 100
}
config_values['OBSTACLE_AVOID'] = {
    'display_name': 'Obstacle avoid',
    'type': 'bool',
    'default_value': LINE_FOLLOWER_OBSTACLE_AVOID
}
config_values['OBSTACLE_AVOID_SIDE'] = {
    'display_name': 'Obstacle avoid side',
    'type': 'int',  # TODO: add enum support and use it here
    'default_value': LINE_FOLLOWER_OBSTACLE_AVOID_SIDE
}
config_values['COLLISION_AVOID'] = {
    'display_name': 'Robot collision avoid',
    'type': 'bool',
    'default_value': LINE_FOLLOWER_COLLISION_AVOID
}
config_values['SHARP_TURN_DETECT'] = {
    'display_name': 'Detect sharp turn',
    'type': 'bool',
    'default_value': LINE_FOLLOWER_SHARP_TURN_DETECT
}
config_values['SHARP_TURN_ROTATE_SIDE'] = {
    'display_name': 'Sharp turn side',
    'type': 'int',  # TODO: add enum support and use it here
    'default_value': LINE_FOLLOWER_SHARP_TURN_ROTATE_SIDE
}
config_values['STOP_ON_PATH_END'] = {
    'display_name': 'Stop on path end',
    'type': 'bool',
    'default_value': LINE_FOLLOWER_STOP_ON_PATH_END
}
LINE_FOLLOWER_CONFIG_VALUES = config_values

# Auto driver
AUTO_DRIVER_MOTOR_SCANNER_SIDE_DEGREES = 100
AUTO_DRIVER_MOTOR_POWER_MIN = 20
AUTO_DRIVER_MOTOR_SPEED = 40
config_values = odict()
config_values['MOTOR_SCANNER_SIDE_DEGREES'] = {
    'display_name': 'One left/right rotation degrees',
    'type': 'int',
    'default_value': AUTO_DRIVER_MOTOR_SCANNER_SIDE_DEGREES
}
config_values['MOTOR_POWER_MIN'] = {
    'display_name': 'Min motor power',
    'type': 'int',
    'default_value': AUTO_DRIVER_MOTOR_POWER_MIN
}
config_values['MOTOR_SPEED'] = {
    'display_name': 'Target motor power',
    'type': 'int',
    'default_value': AUTO_DRIVER_MOTOR_SPEED
}
AUTO_DRIVER_CONFIG_VALUES = config_values
