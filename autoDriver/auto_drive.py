#!/usr/bin/env python3

from ev3dev.auto import *

print('Setting input values')
MIN_MOTOR_SPEED = 20
LEFT_MOTOR_PORT = OUTPUT_B
RIGHT_MOTOR_PORT = OUTPUT_C
SCANNER_MOTOR_PORT = OUTPUT_A
SCANNER_MOTOR_GEAR_RATIO = 20 / 12

print('Initializing...')
LEFT_MOTOR = LargeMotor(LEFT_MOTOR_PORT)
RIGHT_MOTOR = LargeMotor(RIGHT_MOTOR_PORT)
assert LEFT_MOTOR.connected
assert RIGHT_MOTOR.connected
LEFT_MOTOR.reset()
RIGHT_MOTOR.reset()

SCANNER_MOTOR = MediumMotor(SCANNER_MOTOR_PORT)
assert SCANNER_MOTOR.connected
# SCANNER_MOTOR.reset()
SCANNER_MOTOR.stop_action = 'brake'

IR_SENSOR = InfraredSensor()
ULTRASONIC_SENSOR = UltrasonicSensor()
assert IR_SENSOR.connected or ULTRASONIC_SENSOR.connected
if ULTRASONIC_SENSOR.connected:
    ULTRASONIC_SENSOR.mode = 'US-DIST-CM'
    DISTANCE_SENSOR = ULTRASONIC_SENSOR
    MAX_DISTANCE = 255
else:
    IR_SENSOR.mode = 'IR-PROX'
    DISTANCE_SENSOR = IR_SENSOR
    MAX_DISTANCE = 100


def run():
    scan_results = [MAX_DISTANCE, MAX_DISTANCE, MAX_DISTANCE]
    scan_integrals = [0, 0, 0]

    scan_result_tmp = [MAX_DISTANCE, 1]

    def rotateScanner(target):
        SCANNER_MOTOR.run_to_abs_pos(speed_sp=SCANNER_MOTOR.max_speed / 5,
                                     position_sp=target * SCANNER_MOTOR_GEAR_RATIO)

    def getActualScannerPos():
        scanner_position = SCANNER_MOTOR.position
        if scanner_position < -30:
            return 0
        if scanner_position > 30:
            return 2
        return 1

    def writeTmpResult(result, scanner_pos):
        if scanner_pos != scan_result_tmp[1]:
            scan_results[scan_result_tmp[1]] = scan_result_tmp[0]
            scan_integrals[scan_result_tmp[1]] = scan_result_tmp[0] + scan_integrals[scan_result_tmp[1]] / 2
            scan_result_tmp[0] = MAX_DISTANCE
            scan_result_tmp[1] = scanner_pos
            updateDrive()

        scan_result_tmp[0] = min(scan_result_tmp[0], result)

        if scan_result_tmp[0] < scan_results[scan_result_tmp[1]]:
            scan_results[scan_result_tmp[1]] = scan_result_tmp[0]
            updateDrive()

    def updateDrive():
        results_left_ratio = scan_results[2] / (scan_results[0] if scan_results[0] != 0 else 0.1)
        results_right_ratio = scan_results[0] / (scan_results[2] if scan_results[2] != 0 else 0.1)

        speed_mul = (scan_results[1] * 4 - MAX_DISTANCE * 0.7) / MAX_DISTANCE
        # if abs(speed_mul) < 0.25:
        #     if speed_mul == 0:
        #         speed_mul = -0.25
        #     else:
        #         speed_mul *= 0.25 / abs(speed_mul)
        left_speed = results_left_ratio * speed_mul * 100
        right_speed = results_right_ratio * speed_mul * 100

        slow_speed_mul = (MAX_DISTANCE * 0.7 + scan_results[1] * 0.3) / MAX_DISTANCE
        if scan_results[2] > scan_results[0]:
            right_speed *= slow_speed_mul
        else:
            left_speed *= slow_speed_mul

        if speed_mul < 0:
            left_speed, right_speed = right_speed, left_speed

        left_speed = min(max(left_speed, -100), 100) * 0.4
        right_speed = min(max(right_speed, -100), 100) * 0.4

        if abs(left_speed) < MIN_MOTOR_SPEED and abs(right_speed) < MIN_MOTOR_SPEED:
            if abs(left_speed) < abs(right_speed):
                mul = MIN_MOTOR_SPEED / right_speed
                left_speed *= mul
                right_speed *= mul
            else:
                if right_speed == 0:
                    if left_speed == 0:
                        left_speed = -MIN_MOTOR_SPEED
                        right_speed = -MIN_MOTOR_SPEED
                    else:
                        left_speed *= MIN_MOTOR_SPEED / left_speed
                else:
                    mul = MIN_MOTOR_SPEED / left_speed
                    left_speed *= mul
                    right_speed *= mul

        LEFT_MOTOR.duty_cycle_sp = left_speed
        RIGHT_MOTOR.duty_cycle_sp = right_speed

    try:
        rotateScanner(90)
        while 'running' in SCANNER_MOTOR.state:
            pass

        rotateScanner(-90)
        while 'running' in SCANNER_MOTOR.state:
            writeTmpResult(DISTANCE_SENSOR.value(), getActualScannerPos())
        next_positive = True

        LEFT_MOTOR.run_direct()
        RIGHT_MOTOR.run_direct()
        while True:
            scanner_target = 90 if next_positive else -90
            next_positive = not next_positive
            rotateScanner(scanner_target)
            while 'running' in SCANNER_MOTOR.state:
                writeTmpResult(DISTANCE_SENSOR.value(), getActualScannerPos())
    except KeyboardInterrupt:
        pass

    LEFT_MOTOR.stop()
    RIGHT_MOTOR.stop()


print('Running...')
run()

print('Exiting...')
LEFT_MOTOR.reset()
RIGHT_MOTOR.reset()

SCANNER_MOTOR.run_to_abs_pos(speed_sp=SCANNER_MOTOR.max_speed / 10, position_sp=0)
while 'running' in SCANNER_MOTOR.state:
    pass
SCANNER_MOTOR.stop_action = 'coast'
SCANNER_MOTOR.stop()
# SCANNER_MOTOR.reset()
