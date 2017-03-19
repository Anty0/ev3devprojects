import time

from config import ROBOT_MOTOR_SCANNER_GEAR_RATIO
from hardware import SCANNER_MOTOR, INFRARED_SENSOR, PILOT
from utils.regulator import PercentRegulator
from utils.utils import crop_r, wait_to_cycle_time

TARGET_POWER = 50
MAX_SCANNER_POS = abs(45 * ROBOT_MOTOR_SCANNER_GEAR_RATIO)
INFRARED_SENSOR.mode = INFRARED_SENSOR.MODE_IR_SEEK

regulator = PercentRegulator(const_p=0.15, const_i=0.03, const_d=0.12, const_target=50)

try:
    print('Started')
    SCANNER_MOTOR.run_direct(duty_cycle_sp=0)
    PILOT.run_direct()
    last_time = time.time()
    while True:
        angle = INFRARED_SENSOR.value(0)
        distance = INFRARED_SENSOR.value(1)
        motor_pos = SCANNER_MOTOR.position

        input_val = (angle * -1 + 25) * 2
        if abs(motor_pos) > MAX_SCANNER_POS:
            input_val += (abs(motor_pos) - MAX_SCANNER_POS) / ROBOT_MOTOR_SCANNER_GEAR_RATIO \
                         * (motor_pos / abs(motor_pos))
        SCANNER_MOTOR.duty_cycle_sp = crop_r(regulator.regulate(input_val) * ROBOT_MOTOR_SCANNER_GEAR_RATIO)

        if distance > 18:
            PILOT.update_duty_cycle(crop_r(motor_pos / ROBOT_MOTOR_SCANNER_GEAR_RATIO * 2), TARGET_POWER)
        else:
            PILOT.update_duty_cycle(0, 0)

        last_time = wait_to_cycle_time('BeaconFollow', last_time, 0.04)
finally:
    PILOT.stop()
    SCANNER_MOTOR.stop()
    SCANNER_MOTOR.run_to_abs_pos(position_sp=0, speed_sp=SCANNER_MOTOR.max_speed / 10)
