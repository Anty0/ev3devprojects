import logging
import os
import sys

from ev3dev.auto import OUTPUT_A, OUTPUT_B, OUTPUT_C
from odict.pyodict import odict

LOG_TMP = ''


class LogSteam:
    def flush(self):
        sys.stdout.flush()
        pass

    def write(self, msg):
        global LOG_TMP
        LOG_TMP += msg
        sys.stdout.write(msg)
        pass

root = logging.getLogger()
root.setLevel(logging.DEBUG)

# Enable logging output
ch = logging.StreamHandler(LogSteam())
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

log = logging.getLogger(__name__)

# Other
ENABLE_SOUNDS = True
DATA_DIR = os.curdir + os.sep + 'data'

# Server
SERVER_PORT = 8000
SERVER_HTML_DIR = DATA_DIR + os.sep + 'html'
SERVER_DATA_DIR = DATA_DIR + os.sep + 'html_data'

# Robot
ROBOT_MOTOR_WHEELS_LEFT_PORT = OUTPUT_B
ROBOT_MOTOR_WHEELS_RIGHT_PORT = OUTPUT_C
ROBOT_MOTOR_WHEELS_DIAMETER = 4.3
ROBOT_MOTOR_WHEELS_WIDTH = 2.1
ROBOT_MOTOR_WHEELS_OFFSET = 10  # TODO: measure
ROBOT_MOTOR_WHEELS_GEAR_RATIO = 1

ROBOT_MOTOR_SCANNER_PORT = OUTPUT_A
ROBOT_MOTOR_SCANNER_GEAR_RATIO = 20 / 12

# Line follower
LINE_FOLLOWER_TARGET_CYCLE_TIME = 0.01
LINE_FOLLOWER_TARGET_POWER = 100
LINE_FOLLOWER_REGULATE_TARGET_POWER_CHANGE = True
LINE_FOLLOWER_TARGET_REFLECT = 55
LINE_FOLLOWER_AUTO_LEARN_CONSTANTS = False  # TODO: add support
LINE_FOLLOWER_REG_STEER_P = float(1)  # Proportional gain. Start value 1
LINE_FOLLOWER_REG_STEER_I = float(0)  # Integral gain. Start value 0
LINE_FOLLOWER_REG_STEER_D = float(0)  # Derivative gain. Start value 0
LINE_FOLLOWER_LINE_SIDE = -1  # -1 == left; 1 == right
LINE_FOLLOWER_OBSTACLE_AVOID = False
LINE_FOLLOWER_OBSTACLE_AVOID_SIDE = -1  # -1 == left; 1 == right
LINE_FOLLOWER_OBSTACLE_MIN_DISTANCE = 50
LINE_FOLLOWER_COLLISION_AVOID = False
LINE_FOLLOWER_SHARP_TURN_DETECT = False
LINE_FOLLOWER_SHARP_TURN_ROTATE_SIDE = -1  # -1 == left; 1 == right
LINE_FOLLOWER_STOP_ON_LINE_END = False
config_values = odict()
config_values['AUTO_LEARN_CONSTANTS'] = {
    'display_name': 'Try auto-learn constants (beta)',
    'type': 'bool',
    'default_value': LINE_FOLLOWER_AUTO_LEARN_CONSTANTS
}
config_values['REG_STEER_P'] = {
    'display_name': 'Regulator STEER-P',
    'type': 'float',
    'default_value': LINE_FOLLOWER_REG_STEER_P
}
config_values['REG_STEER_I'] = {
    'display_name': 'Regulator STEER-I',
    'type': 'float',
    'default_value': LINE_FOLLOWER_REG_STEER_I
}
config_values['REG_STEER_D'] = {
    'display_name': 'Regulator STEER-D',
    'type': 'float',
    'default_value': LINE_FOLLOWER_REG_STEER_D
}
config_values['PAUSE_POWER'] = {
    'display_name': 'Pause',
    'type': 'bool',
    'default_value': False
}
config_values['REGULATE_TARGET_POWER_CHANGE'] = {
    'display_name': 'Regulate target power change',
    'type': 'bool',
    'default_value': LINE_FOLLOWER_REGULATE_TARGET_POWER_CHANGE
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
config_values['OBSTACLE_MIN_DISTANCE'] = {
    'display_name': 'Minimal distance from obstacle',
    'type': 'int',
    'default_value': LINE_FOLLOWER_OBSTACLE_MIN_DISTANCE
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
config_values['STOP_ON_LINE_END'] = {
    'display_name': 'Stop on path end',
    'type': 'bool',
    'default_value': LINE_FOLLOWER_STOP_ON_LINE_END
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
