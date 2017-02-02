#!/usr/bin/env python3

import sys
from time import sleep, time as get_time

import prepare as const


def steering(course, power):
    sys.stdout.write('\r' + str(course))
    if course >= 0:
        if course > 100:
            power_right = 0
            power_left = power
        else:
            power_left = power
            power_right = power - ((power * course) / 100)
    else:
        if course < -100:
            power_left = 0
            power_right = power
        else:
            power_right = power
            power_left = power + ((power * course) / 100)
    return int(power_left), int(power_right)


def run():
    try:
        max_error = min(abs(100 - const.TARGET), abs(const.TARGET - 100)) * 0.8
        max_change = max_error * 0.3
        last_error = error = integral = 0
        const.LEFT_MOTOR.run_direct()
        const.RIGHT_MOTOR.run_direct()
        time = get_time()
        while True:
            ref_read = const.COLOR_SENSOR.value()
            error = const.TARGET - (100 * (ref_read - const.MIN_REFLECT) / (const.MAX_REFLECT - const.MIN_REFLECT))

            if const.STOP_ON_PATH_END and error > max_error and abs(last_error - error) > max_change:
                print('Detected path end')
                break

            derivative = error - last_error
            last_error = error

            integral = float(0.5) * integral + error
            course = (const.KP * error + const.KD * derivative + const.KI * integral) * const.DIRECTION

            powers = steering(course, const.POWER)
            const.LEFT_MOTOR.duty_cycle_sp = powers[0]
            const.RIGHT_MOTOR.duty_cycle_sp = powers[1]

            new_time = get_time()
            sleep_time = 0.01 - (new_time - time)
            if sleep_time > 0:
                sleep(sleep_time)
            time = new_time

    except KeyboardInterrupt:
        pass
    const.reset()
    print()


print('Running...')
run()
