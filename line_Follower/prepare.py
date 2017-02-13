#!/usr/bin/env python3

from ev3dev.auto import *

# ------Input--------
print('Setting input values')
POWER = 100
TARGET = 55  # 65  # None = center
KP = float(2.5)  # float(5)  # 0.65  # Proportional gain. Start value 1
KD = float(8)  # float(30)  # 1  # Derivative gain. Start value 0
KI = float(0.15)  # float(0.15)  # 0.02  # Integral gain. Start value 0
DIRECTION = -1
MIN_REFLECT = None  # None = autodetect
MAX_REFLECT = None  # None = autodetect
STOP_ON_PATH_END = False
# -------------------

print('Connecting motors')
LEFT_MOTOR = LargeMotor(OUTPUT_B)
RIGHT_MOTOR = LargeMotor(OUTPUT_C)
assert LEFT_MOTOR.connected
assert RIGHT_MOTOR.connected
LEFT_MOTOR.reset()
RIGHT_MOTOR.reset()

print('Connecting sensors')
# ir = InfraredSensor(); 	assert ir.connected
# ts = TouchSensor();    	assert ts.connected
COLOR_SENSOR = ColorSensor()
assert COLOR_SENSOR.connected

print('Setting color sensor mode')
COLOR_SENSOR.mode = 'COL-REFLECT'


def scanReflect():
    global MIN_REFLECT, MAX_REFLECT
    while 'running' in LEFT_MOTOR.state or 'running' in RIGHT_MOTOR.state:
        read = COLOR_SENSOR.value()
        MIN_REFLECT = min(MIN_REFLECT, read)
        MAX_REFLECT = max(MAX_REFLECT, read)


def detectMinMaxReflect():
    print('Scanning min and max reflection...')
    global MIN_REFLECT, MAX_REFLECT
    MIN_REFLECT = 100
    MAX_REFLECT = 0

    LEFT_MOTOR.run_to_rel_pos(speed_sp=POWER * 2, position_sp=150)
    RIGHT_MOTOR.run_to_rel_pos(speed_sp=POWER * 2, position_sp=-150)
    scanReflect()

    LEFT_MOTOR.run_to_rel_pos(position_sp=-300)
    RIGHT_MOTOR.run_to_rel_pos(position_sp=300)
    scanReflect()

    LEFT_MOTOR.run_to_rel_pos(position_sp=150)
    RIGHT_MOTOR.run_to_rel_pos(position_sp=-150)
    scanReflect()

    LEFT_MOTOR.reset()
    RIGHT_MOTOR.reset()
    print('Min reflect: ' + str(MIN_REFLECT))
    print('Max reflect: ' + str(MAX_REFLECT))


if MIN_REFLECT is None or MAX_REFLECT is None:
    detectMinMaxReflect()


def reset():
    print('Stopping motors')
    LEFT_MOTOR.reset()
    RIGHT_MOTOR.reset()
