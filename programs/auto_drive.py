#!/usr/bin/env python3

import math
import threading
import time

from config import AUTO_DRIVER_CONFIG_VALUES
from hardware import PILOT, SCANNER, reset_hardware
from utils.robot_program import RobotProgram, SimpleRobotProgramController
from utils.utils import crop_r


class AutoDriveController(SimpleRobotProgramController):
    def __init__(self, robot_program, config=None):
        super().__init__(robot_program, config)

        self.stop = False
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        scan_results = [100, 100, 100]
        scan_integrals = [0, 0, 0]

        scan_result_tmp = [100, 1]

        side_degrees = self.get_config_value('MOTOR_SCANNER_SIDE_DEGREES')

        def scanner_pos_to_side(scanner_position):
            straight_degrees = side_degrees / 3
            if scanner_position < -straight_degrees:
                return 0
            if scanner_position > straight_degrees:
                return 2
            return 1

        def write_tmp_result(result, scanner_pos):
            if scanner_pos != scan_result_tmp[1]:
                scan_results[scan_result_tmp[1]] = scan_result_tmp[0]
                scan_integrals[scan_result_tmp[1]] = scan_result_tmp[0] + scan_integrals[scan_result_tmp[1]] / 2
                scan_result_tmp[0] = 100
                scan_result_tmp[1] = scanner_pos
                update_drive()

            scan_result_tmp[0] = min(scan_result_tmp[0], result)

            if scan_result_tmp[0] < scan_results[scan_result_tmp[1]]:
                scan_results[scan_result_tmp[1]] = scan_result_tmp[0]
                update_drive()

        def update_drive():
            results_left_ratio = (scan_results[2] / scan_results[0]) if scan_results[0] != 0 else math.inf
            results_right_ratio = (scan_results[0] / scan_results[2]) if scan_results[2] != 0 else math.inf

            min_scan_result = min(scan_results[0], scan_results[1], scan_results[2])
            speed_mul = (min_scan_result * 4 - 100 * 0.7) / 100
            left_speed = results_left_ratio * speed_mul * 100
            right_speed = results_right_ratio * speed_mul * 100

            slow_speed_mul = (100 * 0.7 + scan_results[1] * 0.3) / 100
            if scan_results[2] > scan_results[0]:
                right_speed *= slow_speed_mul
            else:
                left_speed *= slow_speed_mul

            if speed_mul < 0:
                left_speed, right_speed = right_speed, left_speed

            motor_speed = self.get_config_value('MOTOR_SPEED') / 100
            left_speed = crop_r(left_speed) * motor_speed
            right_speed = crop_r(right_speed) * motor_speed

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

            PILOT.update_duty_cycle_raw([left_speed, right_speed])  # TODO: rework to course

        def value_handler(val, angle):
            write_tmp_result(val, scanner_pos_to_side(angle))

        SCANNER.rotate_scanner_to_pos(side_degrees)
        SCANNER.wait_to_scanner_stop()

        SCANNER.value_scan_continuous(-side_degrees, value_handler)
        next_positive = True

        PILOT.run_direct()
        while not self.stop:
            side_degrees = self.get_config_value('MOTOR_SCANNER_SIDE_DEGREES')
            scanner_target = side_degrees if next_positive else -side_degrees
            next_positive = not next_positive
            SCANNER.value_scan_continuous(scanner_target, value_handler)

        reset_hardware()

    def on_config_change(self):
        super().on_config_change()

    def on_config_value_change(self, name, new_value):
        super().on_config_value_change(name, new_value)

    def request_exit(self):
        self.stop = True

    def wait_to_exit(self):
        while self.thread.is_alive():
            time.sleep(0)


class AutoDriveRobotProgram(RobotProgram):
    def __init__(self):
        super().__init__('AutoDrive', AUTO_DRIVER_CONFIG_VALUES)

    def execute(self, config=None) -> AutoDriveController:
        if not PILOT.is_connected() or not SCANNER.is_connected() or not SCANNER.has_motor():
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
