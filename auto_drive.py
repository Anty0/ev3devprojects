#!/usr/bin/env python3

import threading

import math

import config as _config
from hardware import *
from robot_program import *


class AutoDriveController(SimpleRobotProgramController):
    def __init__(self, robot_program, config=None):
        super().__init__(robot_program, config)

        self.stop = False
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        scan_results = [MAX_DISTANCE, MAX_DISTANCE, MAX_DISTANCE]
        scan_integrals = [0, 0, 0]

        scan_result_tmp = [MAX_DISTANCE, 1]

        def rotate_scanner(target):
            SCANNER_MOTOR.run_to_abs_pos(speed_sp=SCANNER_MOTOR.max_speed / 5,
                                         position_sp=target * _config.ROBOT_MOTOR_SCANNER_GEAR_RATIO)

        def get_actual_scanner_pos(max_side_degrees):
            scanner_position = SCANNER_MOTOR.position
            straight_degrees = max_side_degrees / 3
            if scanner_position < -straight_degrees:
                return 0
            if scanner_position > straight_degrees:
                return 2
            return 1

        def write_tmp_result(result, scanner_pos):
            if scanner_pos != scan_result_tmp[1]:
                scan_results[scan_result_tmp[1]] = scan_result_tmp[0]
                scan_integrals[scan_result_tmp[1]] = scan_result_tmp[0] + scan_integrals[scan_result_tmp[1]] / 2
                scan_result_tmp[0] = MAX_DISTANCE
                scan_result_tmp[1] = scanner_pos
                update_drive()

            scan_result_tmp[0] = min(scan_result_tmp[0], result)

            if scan_result_tmp[0] < scan_results[scan_result_tmp[1]]:
                scan_results[scan_result_tmp[1]] = scan_result_tmp[0]
                update_drive()

        def update_drive():
            results_left_ratio = (scan_results[2] / scan_results[0]) if scan_results[0] != 0 else math.inf
            results_right_ratio = (scan_results[0] / scan_results[2]) if scan_results[2] != 0 else math.inf

            speed_mul = (min(scan_results[0], scan_results[1], scan_results[2]) * 4 - MAX_DISTANCE * 0.7) / MAX_DISTANCE
            left_speed = results_left_ratio * speed_mul * 100
            right_speed = results_right_ratio * speed_mul * 100

            slow_speed_mul = (MAX_DISTANCE * 0.7 + scan_results[1] * 0.3) / MAX_DISTANCE
            if scan_results[2] > scan_results[0]:
                right_speed *= slow_speed_mul
            else:
                left_speed *= slow_speed_mul

            if speed_mul < 0:
                left_speed, right_speed = right_speed, left_speed

            motor_speed = self.get_config_value('MOTOR_SPEED') / 100
            left_speed = min(max(left_speed, -100), 100) * motor_speed
            right_speed = min(max(right_speed, -100), 100) * motor_speed

            min_motor_power = self.get_config_value('MOTOR_POWER_MIN')
            if abs(left_speed) < min_motor_power and abs(right_speed) < min_motor_power:
                if abs(left_speed) < abs(right_speed):
                    mul = min_motor_power / right_speed
                    left_speed *= mul
                    right_speed *= mul
                else:
                    if right_speed == 0:
                        if left_speed == 0:
                            left_speed = -min_motor_power
                            right_speed = -min_motor_power
                        else:
                            left_speed *= min_motor_power / left_speed
                    else:
                        mul = min_motor_power / left_speed
                        left_speed *= mul
                        right_speed *= mul

            LEFT_MOTOR.duty_cycle_sp = int(left_speed)
            RIGHT_MOTOR.duty_cycle_sp = int(right_speed)

        side_degrees = self.get_config_value('MOTOR_SCANNER_SIDE_DEGREES')
        rotate_scanner(side_degrees)
        while not self.stop and 'running' in SCANNER_MOTOR.state:
            pass

        rotate_scanner(-side_degrees)
        while not self.stop and 'running' in SCANNER_MOTOR.state:
            write_tmp_result(DISTANCE_SENSOR.value(), get_actual_scanner_pos(side_degrees))
        next_positive = True

        LEFT_MOTOR.run_direct()
        RIGHT_MOTOR.run_direct()
        while not self.stop:
            side_degrees = self.get_config_value('MOTOR_SCANNER_SIDE_DEGREES')
            scanner_target = side_degrees if next_positive else -side_degrees
            next_positive = not next_positive
            rotate_scanner(scanner_target)
            while 'running' in SCANNER_MOTOR.state:
                write_tmp_result(DISTANCE_SENSOR.value(), get_actual_scanner_pos(side_degrees))

        reset_hardware()

    def on_config_change(self):
        super().on_config_change()

    def on_config_value_change(self, name, new_value):
        super().on_config_value_change(name, new_value)

    def request_exit(self):
        self.stop = True

    def wait_to_exit(self):
        while self.thread.is_alive():
            time.sleep(0.1)


class AutoDriveRobotProgram(RobotProgram):
    def __init__(self):
        super().__init__('AutoDrive', _config.AUTO_DRIVER_CONFIG_VALUES)

    def execute(self, config=None) -> RobotProgramController:
        if not HAS_WHEELS or not HAS_SCANNER_MOTOR or not HAS_DISTANCE_SENSOR:
            raise Exception('AutoDrive requires wheels and rotating scanner.')
        return AutoDriveController(self, config)


def run():
    controller = AutoDriveRobotProgram().execute()
    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass

    controller.request_exit()
    controller.wait_to_exit()


if __name__ == '__main__':
    run()
