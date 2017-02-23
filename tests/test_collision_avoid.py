from ev3dev.auto import *

from utils import utils
from utils.pilot import Pilot, Wheel
from utils.regulator import PercentRegulator
from utils.scanner import Scanner, ScannerPropulsion

LEFT_MOTOR = LargeMotor(OUTPUT_B)
RIGHT_MOTOR = LargeMotor(OUTPUT_C)

LEFT_MOTOR.reset()
RIGHT_MOTOR.reset()

PILOT = Pilot([
    Wheel(LEFT_MOTOR, 1, 4.3, 2.1, -6.5),
    Wheel(RIGHT_MOTOR, 1, 4.3, 2.1, 6.5)
])

SCANNER = Scanner(ScannerPropulsion(MediumMotor(OUTPUT_A), 20 / 12))

power_regulator = PercentRegulator(const_p=1, const_i=0, const_d=3, const_target=40)

try:
    PILOT.run_direct()
    last_time = time.time()
    while True:
        distance_val = SCANNER.value_scan(0)
        power = power_regulator.regulate(distance_val)
        PILOT.update_duty_cycle_sp(0, power if power < 0 else 0)

        last_time = utils.wait_to_cycle_time(last_time, 0.05)
except KeyboardInterrupt:
    pass
finally:
    PILOT.stop()
