#!/usr/bin/env python3

import time

from ev3dev.auto import OUTPUT_B, OUTPUT_C, LargeMotor, ColorSensor

ROBOT_MOTOR_WHEELS_LEFT_PORT = OUTPUT_C
ROBOT_MOTOR_WHEELS_RIGHT_PORT = OUTPUT_B

TARGET_POWER = 80
TARGET_REFLECT = 55
REG_STEER_P = float(3)  # Proportional gain. Start value 1
REG_STEER_I = float(0.05)  # Integral gain. Start value 0
REG_STEER_D = float(30)  # Derivative gain. Start value 0
# REG_STEER_D_SMALL = float(3)
MIN_VAL = 8
MAX_VAL = 72
LINE_SIDE = 1
CYCLE_TIME = 0.01

LEFT_MOTOR = LargeMotor(ROBOT_MOTOR_WHEELS_LEFT_PORT)
RIGHT_MOTOR = LargeMotor(ROBOT_MOTOR_WHEELS_RIGHT_PORT)
assert LEFT_MOTOR.connected and RIGHT_MOTOR.connected


def reset_wheels():
    LEFT_MOTOR.reset()
    RIGHT_MOTOR.reset()
    LEFT_MOTOR.stop_action = 'brake'
    RIGHT_MOTOR.stop_action = 'brake'


reset_wheels()

COLOR_SENSOR = ColorSensor()
assert COLOR_SENSOR.connected
COLOR_SENSOR.mode = 'COL-REFLECT'

try:
    last_error = 0
    last_integral = 0

    LEFT_MOTOR.run_direct(duty_cycle_sp=0)
    RIGHT_MOTOR.run_direct(duty_cycle_sp=0)
    last_time = time.time()
    while True:
        input_val = (COLOR_SENSOR.value() - MIN_VAL) / (MAX_VAL - MIN_VAL) * 100

        error = (TARGET_REFLECT - input_val) * 2

        integral = float(0.5) * last_integral + error
        last_integral = integral

        derivative = error - last_error
        last_error = error

        course = REG_STEER_P * error + REG_STEER_I * integral + REG_STEER_D * derivative
        course = course / 100 * TARGET_POWER

        if course > 0:
            power_left = TARGET_POWER
            power_right = TARGET_POWER - abs(course)
        elif course < 0:
            power_left = TARGET_POWER - abs(course)
            power_right = TARGET_POWER
        else:
            power_left = TARGET_POWER
            power_right = TARGET_POWER

        LEFT_MOTOR.duty_cycle_sp = min(100, max(power_left, 0))
        RIGHT_MOTOR.duty_cycle_sp = min(100, max(power_right, 0))

        new_time = time.time()
        sleep_time = CYCLE_TIME - (new_time - last_time)
        if sleep_time > 0:
            time.sleep(sleep_time)
        # elif sleep_time < -CYCLE_TIME * 5:
        #     print('Regulation is getting late. It\'s late %s seconds. Use bigger cycle time.' % sleep_time)
        last_time += CYCLE_TIME
except KeyboardInterrupt:
    pass
finally:
    reset_wheels()
