import logging
import os
import sys
from collections import OrderedDict

from ev3dev.auto import OUTPUT_A, OUTPUT_B, OUTPUT_C

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
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

log = logging.getLogger(__name__)

# Other
SIMULATION_MODE = '--simulate' in sys.argv or '-s' in sys.argv
ENABLE_SOUNDS = not SIMULATION_MODE
DATA_DIR = os.curdir + os.sep + 'data'


# Server
SERVER_PORT = 8000
SERVER_HTML_DIR = DATA_DIR + os.sep + 'html'
SERVER_DATA_DIR = DATA_DIR + os.sep + 'html_data'


# Robot
ROBOT_WIDTH = 15
ROBOT_LENGTH = 23
ROBOT_HEIGHT = 16
ROBOT_WEIGHT = 0  # TODO: measure

ROBOT_BRICK_OFFSET_X = 0
ROBOT_BRICK_OFFSET_Y = -5

ROBOT_MOTOR_WHEEL_LEFT_PORT = OUTPUT_B
ROBOT_MOTOR_WHEEL_LEFT_DIAMETER = 4.3
ROBOT_MOTOR_WHEEL_LEFT_WIDTH = 2.1
ROBOT_MOTOR_WHEEL_LEFT_GEAR_RATIO = 1  # -12/36
ROBOT_MOTOR_WHEEL_LEFT_OFFSET_X = -6.5

ROBOT_MOTOR_WHEEL_RIGHT_PORT = OUTPUT_C
ROBOT_MOTOR_WHEEL_RIGHT_DIAMETER = 4.3
ROBOT_MOTOR_WHEEL_RIGHT_WIDTH = 2.1
ROBOT_MOTOR_WHEEL_RIGHT_GEAR_RATIO = 1  # -12/36
ROBOT_MOTOR_WHEEL_RIGHT_OFFSET_X = 6.5

ROBOT_MOTOR_SCANNER_PORT = OUTPUT_A
ROBOT_MOTOR_SCANNER_GEAR_RATIO = 20 / 12

ROBOT_SENSOR_COLOR_OFFSET_X = 0
ROBOT_SENSOR_COLOR_OFFSET_Y = 7.5

ROBOT_SENSOR_DISTANCE_OFFSET_X = 0
ROBOT_SENSOR_DISTANCE_OFFSET_Y = 10.5

# Line follower
LINE_FOLLOWER_TARGET_CYCLE_TIME = 0.1
LINE_FOLLOWER_TARGET_POWER = 20
LINE_FOLLOWER_POWER_ADAPTATION = True
LINE_FOLLOWER_REGULATE_TARGET_POWER_CHANGE = True
LINE_FOLLOWER_TARGET_REFLECT = 55
LINE_FOLLOWER_AUTO_LEARN_CONSTANTS = False  # TODO: add support
LINE_FOLLOWER_REG_STEER_P = float(0.3)  # Proportional gain. Start value 1
LINE_FOLLOWER_REG_STEER_I = float(0)  # Integral gain. Start value 0
LINE_FOLLOWER_REG_STEER_D = float(0)  # Derivative gain. Start value 0
LINE_FOLLOWER_LINE_SIDE = -1  # -1 == left; 1 == right
LINE_FOLLOWER_OBSTACLE_AVOID = False
LINE_FOLLOWER_OBSTACLE_AVOID_SIDE = -1  # -1 == left; 1 == right
LINE_FOLLOWER_OBSTACLE_MIN_DISTANCE = 25
LINE_FOLLOWER_OBSTACLE_WIDTH = 0  # 0 = automatic detection
LINE_FOLLOWER_OBSTACLE_HEIGHT = 0  # 0 = automatic detection
LINE_FOLLOWER_COLLISION_AVOID = False
LINE_FOLLOWER_SHARP_TURN_DETECT = False
LINE_FOLLOWER_SHARP_TURN_ROTATE_SIDE = -1  # -1 == left; 1 == right
LINE_FOLLOWER_STOP_ON_LINE_END = False

config_values = OrderedDict()
config_values['AUTO_LEARN_CONSTANTS'] = {
    'category': 'Steer regulation',
    'display_name': 'Try auto-learn constants (beta)',
    'type': 'bool',
    'default_value': LINE_FOLLOWER_AUTO_LEARN_CONSTANTS
}
config_values['REG_STEER_P'] = {
    'category': 'Steer regulation',
    'display_name': 'Regulator STEER-P',
    'type': 'float',
    'default_value': LINE_FOLLOWER_REG_STEER_P
}
config_values['REG_STEER_I'] = {
    'category': 'Steer regulation',
    'display_name': 'Regulator STEER-I',
    'type': 'float',
    'default_value': LINE_FOLLOWER_REG_STEER_I
}
config_values['REG_STEER_D'] = {
    'category': 'Steer regulation',
    'display_name': 'Regulator STEER-D',
    'type': 'float',
    'default_value': LINE_FOLLOWER_REG_STEER_D
}
config_values['PAUSE_POWER'] = {
    'category': 'Power',
    'display_name': 'Pause',
    'type': 'bool',
    'default_value': False
}
config_values['TARGET_POWER'] = {
    'category': 'Power',
    'display_name': 'Target power',
    'type': 'int',
    'default_value': LINE_FOLLOWER_TARGET_POWER
}
config_values['POWER_ADAPTATION'] = {
    'category': 'Power',
    'display_name': 'Power adaptation',
    'type': 'bool',
    'default_value': LINE_FOLLOWER_POWER_ADAPTATION
}
config_values['REGULATE_TARGET_POWER_CHANGE'] = {
    'category': 'Power',
    'display_name': 'Regulate target power change',
    'type': 'bool',
    'default_value': LINE_FOLLOWER_REGULATE_TARGET_POWER_CHANGE
}
config_values['TARGET_REFLECT'] = {
    'category': 'Color sensor',
    'display_name': 'Target reflection',
    'type': 'int',
    'default_value': LINE_FOLLOWER_TARGET_REFLECT
}
config_values['DETECT_REFLECT'] = {
    'category': 'Color sensor',
    'display_name': 'Auto detect min/max reflection',
    'type': 'bool',
    'default_value': True
}
config_values['MIN_REFLECT'] = {
    'category': 'Color sensor',
    'display_name': 'Minimal reflection',
    'type': 'int',
    'default_value': 0
}
config_values['MAX_REFLECT'] = {
    'category': 'Color sensor',
    'display_name': 'Maximal reflection',
    'type': 'int',
    'default_value': 100
}
config_values['OBSTACLE_AVOID'] = {
    'category': 'Obstacle',
    'display_name': 'Obstacle avoid',
    'type': 'bool',
    'default_value': LINE_FOLLOWER_OBSTACLE_AVOID
}
config_values['OBSTACLE_AVOID_SIDE'] = {
    'category': 'Obstacle',
    'display_name': 'Obstacle avoid side',
    'type': 'enum',
    'enum_options': {
        'left': -1,
        'right': 1
    },
    'default_value': LINE_FOLLOWER_OBSTACLE_AVOID_SIDE
}
config_values['OBSTACLE_MIN_DISTANCE'] = {
    'category': 'Obstacle',
    'display_name': 'Minimal distance from obstacle',
    'type': 'int',
    'default_value': LINE_FOLLOWER_OBSTACLE_MIN_DISTANCE
}
config_values['OBSTACLE_WIDTH'] = {
    'category': 'Obstacle',
    'display_name': 'Width of obstacle',
    'type': 'float',
    'default_value': LINE_FOLLOWER_OBSTACLE_WIDTH
}
config_values['OBSTACLE_HEIGHT'] = {
    'category': 'Obstacle',
    'display_name': 'Height of obstacle',
    'type': 'float',
    'default_value': LINE_FOLLOWER_OBSTACLE_HEIGHT
}
config_values['COLLISION_AVOID'] = {
    'category': 'Collision',
    'display_name': 'Robot collision avoid',
    'type': 'bool',
    'default_value': LINE_FOLLOWER_COLLISION_AVOID
}
config_values['SHARP_TURN_DETECT'] = {
    'category': 'Sharp turn',
    'display_name': 'Detect sharp turn',
    'type': 'bool',
    'default_value': LINE_FOLLOWER_SHARP_TURN_DETECT
}
config_values['SHARP_TURN_ROTATE_SIDE'] = {
    'category': 'Sharp turn',
    'display_name': 'Sharp turn side',
    'type': 'enum',
    'enum_options': {
        'left': -1,
        'right': 1
    },
    'default_value': LINE_FOLLOWER_SHARP_TURN_ROTATE_SIDE
}
config_values['LINE_SIDE'] = {
    'category': 'Other',
    'display_name': 'Line side',
    'type': 'enum',
    'enum_options': {
        'left': -1,
        'right': 1
    },
    'default_value': LINE_FOLLOWER_LINE_SIDE
}
config_values['STOP_ON_LINE_END'] = {
    'category': 'Other',
    'display_name': 'Stop on path end',
    'type': 'bool',
    'default_value': LINE_FOLLOWER_STOP_ON_LINE_END
}
config_values['TARGET_CYCLE_TIME'] = {
    'category': 'Other',
    'display_name': 'Target cycle time',
    'type': 'float',
    'default_value': LINE_FOLLOWER_TARGET_CYCLE_TIME
}
LINE_FOLLOWER_CONFIG_VALUES = config_values

# Auto driver
AUTO_DRIVER_MOTOR_SPEED = 40
AUTO_DRIVER_MOTOR_POWER_MIN = 20
AUTO_DRIVER_MOTOR_SCANNER_SIDE_DEGREES = 90

config_values = OrderedDict()
config_values['MOTOR_SPEED'] = {
    'display_name': 'Target motor power',
    'type': 'int',
    'default_value': AUTO_DRIVER_MOTOR_SPEED
}
config_values['MOTOR_POWER_MIN'] = {
    'display_name': 'Minimal motor power',
    'type': 'int',
    'default_value': AUTO_DRIVER_MOTOR_POWER_MIN
}
config_values['MOTOR_SCANNER_SIDE_DEGREES'] = {
    'display_name': 'Scanner left/right rotation degrees',
    'type': 'int',
    'default_value': AUTO_DRIVER_MOTOR_SCANNER_SIDE_DEGREES
}
AUTO_DRIVER_CONFIG_VALUES = config_values
