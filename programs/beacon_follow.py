import threading
import time

from config import ROBOT_MOTOR_SCANNER_GEAR_RATIO, BEACON_FOLLOWER_CONFIG_VALUES
from hardware import PILOT, SCANNER, SCANNER_MOTOR, INFRARED_SENSOR, reset_hardware
from utils.regulator import PercentRegulator
from utils.robot_program import RobotProgram, SimpleRobotProgramController, run_program
from utils.utils import crop_r, wait_to_cycle_time


class BeaconFollowController(SimpleRobotProgramController):
    def __init__(self, robot_program, config=None):
        super().__init__(robot_program, config)

        self.scanner_position_regulator = PercentRegulator(const_p=0.15, const_i=0.03, const_d=0.12, const_target=50)

        self._stop = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        self.scanner_position_regulator.reset()
        INFRARED_SENSOR.mode = INFRARED_SENSOR.MODE_IR_SEEK

        SCANNER_MOTOR.run_direct(duty_cycle_sp=0)
        PILOT.run_direct()
        last_time = time.time()
        while not self._stop:
            max_scanner_pos = self.get_config_value('MAX_SCANNER_POS')
            target_power = self.get_config_value('TARGET_POWER')

            angle = INFRARED_SENSOR.value(0)
            distance = INFRARED_SENSOR.value(1)
            motor_pos = SCANNER_MOTOR.position

            input_val = (angle * -1 + 25) * 2
            if abs(motor_pos) > max_scanner_pos:
                input_val += (abs(motor_pos) - max_scanner_pos) / ROBOT_MOTOR_SCANNER_GEAR_RATIO \
                             * (motor_pos / abs(motor_pos))
            SCANNER_MOTOR.duty_cycle_sp = crop_r(
                self.scanner_position_regulator.regulate(input_val) * ROBOT_MOTOR_SCANNER_GEAR_RATIO)

            if distance > 18:
                PILOT.update_duty_cycle(crop_r((motor_pos / ROBOT_MOTOR_SCANNER_GEAR_RATIO + angle) * 2, 200),
                                        mul_duty_cycle=(target_power / 100) * (distance / 100))
            else:
                PILOT.update_duty_cycle(0, target_duty_cycle=0, mul_duty_cycle=0)

            last_time = wait_to_cycle_time('BeaconFollow', last_time, 0.04)

        reset_hardware()

    def on_config_change(self):
        super().on_config_change()
        self.scanner_position_regulator.reset()

    def on_config_value_change(self, name, new_value):
        super().on_config_value_change(name, new_value)
        if name == 'MAX_SCANNER_POS':
            self.scanner_position_regulator.reset()

    def request_exit(self):
        self._stop = True

    def wait_to_exit(self):
        while self._thread.is_alive():
            time.sleep(0.05)


class BeaconFollowRobotProgram(RobotProgram):
    def __init__(self):
        super().__init__('BeaconFollow', BEACON_FOLLOWER_CONFIG_VALUES)

    def execute(self, config=None) -> BeaconFollowController:
        if not PILOT.is_connected or not SCANNER.is_connected or not SCANNER.has_motor:
            raise Exception('BeaconFollow requires wheels and rotating scanner.')
        return BeaconFollowController(self, config)


def run():
    config = {}
    run_program(BeaconFollowRobotProgram(), config)


if __name__ == '__main__':
    run()
