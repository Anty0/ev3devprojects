import threading
import time

from hardware import SCANNER, SCANNER_MOTOR, reset_hardware
from utils.robot_program import RobotProgram, SimpleRobotProgramController, run_program


class CalibrateScannerController(SimpleRobotProgramController):
    STOP_POSITION_OFFSET = -222  # TODO: to config
    RUN_RETRIES = 3  # TODO: to config

    def __init__(self, robot_program, config=None):
        super().__init__(robot_program, config)

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        positions = []
        for i in range(self.RUN_RETRIES):
            SCANNER_MOTOR.run_forever(speed_sp=-35)
            time.sleep(1)
            while 'stalled' not in SCANNER_MOTOR.state:
                time.sleep(0.01)
            SCANNER_MOTOR.stop()
            positions.append(SCANNER_MOTOR.position)

            if i < self.RUN_RETRIES - 1:
                SCANNER_MOTOR.run_to_rel_pos(speed_sp=60, position_sp=80)
                while 'running' in SCANNER_MOTOR.state:
                    time.sleep(0.05)

        min_pos = 0
        max_pos = 0
        for i in range(1, len(positions)):
            if positions[i] < positions[min_pos]:
                min_pos = i
            if positions[i] > positions[max_pos]:
                max_pos = i
        positions.remove(positions[min_pos])
        positions.remove(positions[max_pos])

        total = 0
        for position in positions:
            total += position
        position = total / len(positions)

        zero_position = position - self.STOP_POSITION_OFFSET
        SCANNER_MOTOR.run_to_abs_pos(speed_sp=60, position_sp=zero_position)
        SCANNER_MOTOR.wait_until(SCANNER_MOTOR.STATE_RUNNING)
        SCANNER_MOTOR.reset()

        reset_hardware()

    def on_config_change(self):
        super().on_config_change()

    def on_config_value_change(self, name, new_value):
        super().on_config_value_change(name, new_value)

    def request_exit(self):
        pass

    def wait_to_exit(self):
        while self._thread.is_alive():
            time.sleep(0.05)


class CalibrateScannerRobotProgram(RobotProgram):
    def __init__(self):
        super().__init__('ScannerCalibration', {})

    def execute(self, config=None) -> CalibrateScannerController:
        if not SCANNER.is_connected or not SCANNER.has_motor:
            raise Exception('ScannerCalibration requires rotating scanner.')
        return CalibrateScannerController(self, config)


def run():
    config = {}
    run_program(CalibrateScannerRobotProgram(), config)


if __name__ == '__main__':
    run()
