from ev3dev.auto import *

from utils.pilot import Pilot, Wheel

LEFT_MOTOR = LargeMotor(OUTPUT_B)
RIGHT_MOTOR = LargeMotor(OUTPUT_C)

LEFT_MOTOR.reset()
RIGHT_MOTOR.reset()

pilot = Pilot([
    Wheel(LEFT_MOTOR, 1, 4.3, 2.1, -6.5),
    Wheel(RIGHT_MOTOR, 1, 4.3, 2.1, 6.5)
])

pilot.run_forever([-1050, 1050])  # Still ok
try:
    pilot.wait_to_stop()
except KeyboardInterrupt as e:
    raise e
finally:
    pilot.stop()
