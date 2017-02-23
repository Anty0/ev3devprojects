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

pilot.run_forever(speeds_tacho=[-1050, 1050])  # Still ok
try:
    pilot.wait_to_stop()
except KeyboardInterrupt as e:
    raise e
finally:
    pilot.stop()

time.sleep(10)

pilot.run_timed(5, speeds_tacho=[-1050, 1050])
try:
    pilot.wait_to_stop()
except KeyboardInterrupt as e:
    raise e
finally:
    pilot.stop()

time.sleep(10)

pilot.run_drive_forever(None, 5)
try:
    pilot.wait_to_stop()
except KeyboardInterrupt as e:
    raise e
finally:
    pilot.stop()

time.sleep(10)

pilot.run_percent_drive_forever(0, -5)
try:
    pilot.wait_to_stop()
except KeyboardInterrupt as e:
    raise e
finally:
    pilot.stop()

time.sleep(10)

pilot.run_drive_forever(5, 5)
try:
    pilot.wait_to_stop()
except KeyboardInterrupt as e:
    raise e
finally:
    pilot.stop()

time.sleep(10)

pilot.run_percent_drive_forever(-50, -5)
try:
    pilot.wait_to_stop()
except KeyboardInterrupt as e:
    raise e
finally:
    pilot.stop()

time.sleep(10)

pilot.run_percent_drive_to_angle_deg(90, 100, 5)
try:
    pilot.wait_to_stop()
except KeyboardInterrupt as e:
    raise e
finally:
    pilot.stop()

time.sleep(10)

pilot.run_percent_drive_to_distance(15, 0, -5)
try:
    pilot.wait_to_stop()
except KeyboardInterrupt as e:
    raise e
finally:
    pilot.stop()
