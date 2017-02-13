#!/usr/bin/env python3

import threading

import config as _config
from hardware import *
from robot_program import *


class LineFollowController(SimpleRobotProgramController):
    def __init__(self, robot_program, config=None):
        super().__init__(robot_program, config)

        self.power_regulator = Regulator(const_p=0.05, const_d=0, const_i=0,
                                         getter_target=lambda: self.get_config_value('TARGET_POWER')
                                         if not self.get_config_value('PAUSE_POWER') else 0)

        self.steer_regulator = Regulator(getter_p=lambda: self.get_config_value('REG_STEER_P'),
                                         getter_d=lambda: self.get_config_value('REG_STEER_D'),
                                         getter_i=lambda: self.get_config_value('REG_STEER_I'),
                                         getter_target=lambda: self.get_config_value('TARGET_REFLECT'))
        self.last_power = 0

        self.stop = False
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        if self.get_config_value('DETECT_REFLECT'):
            min_reflect = 100
            max_reflect = 0

            def scan_reflect():
                global min_reflect, max_reflect
                while 'running' in LEFT_MOTOR.state or 'running' in RIGHT_MOTOR.state:
                    read = COLOR_SENSOR.value()
                    min_reflect = min(min_reflect, read)
                    max_reflect = max(max_reflect, read)

            LEFT_MOTOR.run_to_rel_pos(speed_sp=200, position_sp=150)
            RIGHT_MOTOR.run_to_rel_pos(speed_sp=200, position_sp=-150)
            scan_reflect()

            LEFT_MOTOR.run_to_rel_pos(position_sp=-300)
            RIGHT_MOTOR.run_to_rel_pos(position_sp=300)
            scan_reflect()

            LEFT_MOTOR.run_to_rel_pos(position_sp=150)
            RIGHT_MOTOR.run_to_rel_pos(position_sp=-150)
            scan_reflect()

            LEFT_MOTOR.stop()
            RIGHT_MOTOR.stop()

            self.set_private_config_value('MIN_REFLECT', min_reflect)
            self.set_private_config_value('MAX_REFLECT', max_reflect)
        else:
            self.set_private_config_value('MIN_REFLECT', None)
            self.set_private_config_value('MAX_REFLECT', None)

        def next_power():
            self.last_power += self.power_regulator.regulate(self.last_power)
            return self.last_power

        def get_min_reflex():
            result = self.get_private_config_value('MIN_REFLECT')
            return result if result is not None else self.get_config_value('MIN_REFLECT')

        def get_max_reflex():
            result = self.get_private_config_value('MAX_REFLECT')
            return result if result is not None else self.get_config_value('MAX_REFLECT')

        last_time = time.time()
        while not self.stop:
            min_reflect = get_min_reflex()
            max_reflect = get_max_reflex()
            line_side = self.get_config_value('LINE_SIDE')
            target_power = next_power()
            target_cycle_time = self.get_config_value('TARGET_CYCLE_TIME')

            read_val = COLOR_SENSOR.value()
            read_percent = 100 * (read_val - min_reflect) / (max_reflect - min_reflect)
            course = min(100, max(-100, self.steer_regulator.regulate(read_percent) * line_side)) / 2

            power_left = target_power + course
            power_right = target_power - course
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
            sleep_time = target_cycle_time - (new_time - last_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
            elif sleep_time < -target_cycle_time * 5:
                log.warn('Regulation is getting late. It\'s late %s seconds. Use bigger cycle time.' % sleep_time)
            last_time += target_cycle_time

        reset_hardware()

    def on_config_change(self):
        super().on_config_change()
        self.steer_regulator.reset()

    def on_config_value_change(self, name, new_value):
        super().on_config_value_change(name, new_value)
        if name == 'REG_STEER_I' or name == 'REG_STEER_D':
            self.steer_regulator.reset()

    def stop(self):
        self.stop = True

    def wait_to_exit(self):
        while self.thread.is_alive():
            time.sleep(0.1)


class LineFollowRobotProgram(RobotProgram):
    def __init__(self):
        super().__init__('LineFollower', _config.LINE_FOLLOWER_CONFIG_VALUES)

    def execute(self, config=None) -> RobotProgramController:
        if not HAS_WHEELS or not HAS_COLOR_SENSOR:
            raise Exception('LineFollower requires wheels and color sensor at last.')
        return LineFollowController(config)


def run():
    controller = LineFollowRobotProgram().execute()
    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass

    controller.stop()
    controller.wait_to_exit()


if __name__ == '__main__':
    run()
