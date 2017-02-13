#!/usr/bin/env python3

import threading

import config as _config
from hardware import *
from robot_program import *


class AutoDriveController(SimpleRobotProgramController):
    def __init__(self, robot_program):
        super().__init__(robot_program)

        self.stop = False
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        while not self.stop:
            pass
        pass

    def on_config_change(self):
        super().on_config_change()

    def on_config_value_change(self, name, new_value):
        super().on_config_value_change(name, new_value)

    def stop(self):
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
        return AutoDriveController(config)


def run():
    controller = AutoDriveRobotProgram().execute()
    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass

    controller.stop()
    controller.wait_to_exit()


if __name__ == '__main__':
    run()
