from ev3dev.auto import *

from utils import utils
from utils.regulator import ValueRegulator

SPEED = 360
LEFT_MOTOR = LargeMotor(OUTPUT_B)
RIGHT_MOTOR = LargeMotor(OUTPUT_C)

print('Running...')
try:
    start_time = time.time()
    start_pos = LEFT_MOTOR.position
    regulator = ValueRegulator(const_p=1, const_i=0.1, const_d=2,
                               getter_target=lambda: SPEED * (time.time() - start_time) + start_pos)

    LEFT_MOTOR.run_direct(duty_cycle_sp=0)
    last_time = time.time()
    while True:
        LEFT_MOTOR.duty_cycle_sp = utils.crop_r(regulator.regulate(LEFT_MOTOR.position))
        last_time = utils.wait_to_cycle_time(last_time, 0.05)
except KeyboardInterrupt:
    pass

LEFT_MOTOR.stop()
