import time

from ev3dev.auto import OUTPUT_A, OUTPUT_B, OUTPUT_C, LargeMotor, MediumMotor

from utils import utils
from utils.pilot import Pilot
from utils.regulator import PercentRegulator
from utils.scanner import Scanner, ScannerPropulsion
from utils.wheel import Wheel

LEFT_MOTOR = LargeMotor(OUTPUT_B)
RIGHT_MOTOR = LargeMotor(OUTPUT_C)

LEFT_MOTOR.reset()
RIGHT_MOTOR.reset()

PILOT = Pilot([
    Wheel(LEFT_MOTOR, 1, 4.3, 2.1, -6.5),
    Wheel(RIGHT_MOTOR, 1, 4.3, 2.1, 6.5)
])

SCANNER = Scanner(ScannerPropulsion(MediumMotor(OUTPUT_A), 20 / 12))

power_regulator = PercentRegulator(const_p=1, const_i=3, const_d=2, const_target=-40)

try:
    PILOT.run_direct()
    last_time = time.time()
    while True:
        distance_val = SCANNER.value_scan(0)
        power = utils.crop_m(power_regulator.regulate(-distance_val), min_out=-30, max_out=0)
        PILOT.update_duty_cycle(0, power)

        last_time = utils.wait_to_cycle_time(last_time, 0.05)
except KeyboardInterrupt:
    pass
finally:
    PILOT.stop()
