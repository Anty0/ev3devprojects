import time

from ev3dev.auto import OUTPUT_B, OUTPUT_C, LargeMotor

from utils.regulator import ValueRegulator
from utils.utils import crop_r, wait_to_cycle_time

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
        LEFT_MOTOR.duty_cycle_sp = crop_r(regulator.regulate(LEFT_MOTOR.position))
        last_time = wait_to_cycle_time(__name__, last_time, 0.05)
except KeyboardInterrupt:
    pass

LEFT_MOTOR.stop()
