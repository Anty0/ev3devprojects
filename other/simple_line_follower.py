#!/usr/bin/env python3

import time

from ev3dev.auto import OUTPUT_B, OUTPUT_C, LargeMotor, ColorSensor, UltrasonicSensor

ROBOT_MOTOR_WHEELS_LEFT_PORT = OUTPUT_C
ROBOT_MOTOR_WHEELS_RIGHT_PORT = OUTPUT_B

TARGET_POWER = 100
TARGET_REFLECT = 55
REG_STEER_P = float(1)  # Proportional gain. Start value 1
REG_STEER_I = float(0)  # Integral gain. Start value 0
REG_STEER_D = float(0)  # Derivative gain. Start value 0
LINE_SIDE = -1
CYCLE_TIME = 0.05

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

ULTRASONIC_SENSOR = UltrasonicSensor()
assert ULTRASONIC_SENSOR.connected
ULTRASONIC_SENSOR.mode = 'US-DIST-CM'
DISTANCE_SENSOR = ULTRASONIC_SENSOR
MAX_DISTANCE = 255

try:
    last_error = 0
    last_integral = 0

    LEFT_MOTOR.run_direct(duty_cycle_sp=0)
    RIGHT_MOTOR.run_direct(duty_cycle_sp=0)
    last_time = time.time()
    while True:
        input_val = COLOR_SENSOR.value()

        error = (TARGET_REFLECT - input_val) * 2

        integral = float(0.5) * last_integral + error
        last_integral = integral

        derivative = error - last_error
        last_error = error

        course = REG_STEER_P * error + REG_STEER_I * integral + REG_STEER_D * derivative

        power_left = TARGET_POWER + course
        power_right = TARGET_POWER - course
        diff = 0
        if power_left > 100:
            diff += power_left - 100
        elif power_left < 0:
            diff -= power_left
        if power_right > 100:
            diff -= power_right - 100
        elif power_right < 0:
            diff += power_right
        power_left -= diff
        power_right += diff

        LEFT_MOTOR.duty_cycle_sp = int(power_left)
        RIGHT_MOTOR.duty_cycle_sp = int(power_right)

        new_time = time.time()
        sleep_time = CYCLE_TIME - (new_time - last_time)
        if sleep_time > 0:
            time.sleep(sleep_time)
        elif sleep_time < -CYCLE_TIME * 5:
            print('Regulation is getting late. It\'s late %s seconds. Use bigger cycle time.' % sleep_time)
        last_time += CYCLE_TIME
except KeyboardInterrupt:
    pass
finally:
    reset_wheels()
