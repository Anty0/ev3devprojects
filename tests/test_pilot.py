from ev3dev.auto import OUTPUT_B, OUTPUT_C, LargeMotor

from utils.pilot import Pilot
from utils.wheel import Wheel

LEFT_MOTOR = LargeMotor(OUTPUT_B)
RIGHT_MOTOR = LargeMotor(OUTPUT_C)

pilot = Pilot([
    Wheel(LEFT_MOTOR, -12 / 36, 4.3, 2.1, -6.5),
    Wheel(RIGHT_MOTOR, -12 / 36, 4.3, 2.1, 6.5)
])

pilot.run_forever(speeds_tacho=[50, -50])  # [-1050, 1050] Still ok
try:
    pilot.wait_to_stop()
except KeyboardInterrupt as e:
    pass
finally:
    pilot.stop()

# time.sleep(10)
#
# pilot.run_timed(10, speeds_tacho=[-50, 50])
# try:
#     pilot.wait_to_stop()
# except KeyboardInterrupt as e:
#     raise e
# finally:
#     pilot.stop()
#
# time.sleep(10)
#
# pilot.run_drive_forever(None, 1)
# try:
#     pilot.wait_to_stop()
# except KeyboardInterrupt as e:
#     pass
# finally:
#     pilot.stop()
#
# time.sleep(10)
#
# pilot.run_percent_drive_forever(0, -1)
# try:
#     pilot.wait_to_stop()
# except KeyboardInterrupt as e:
#     pass
# finally:
#     pilot.stop()
#
# time.sleep(10)
#
# pilot.run_drive_forever(5, 1)
# try:
#     pilot.wait_to_stop()
# except KeyboardInterrupt as e:
#     pass
# finally:
#     pilot.stop()
#
# time.sleep(10)
#
# pilot.run_drive_forever(-5, 1)
# try:
#     pilot.wait_to_stop()
# except KeyboardInterrupt as e:
#     pass
# finally:
#     pilot.stop()
#
# time.sleep(10)
#
# pilot.run_percent_drive_forever(-50, -1)
# try:
#     pilot.wait_to_stop()
# except KeyboardInterrupt as e:
#     pass
# finally:
#     pilot.stop()
#
# time.sleep(10)
#
# pilot.run_percent_drive_to_angle_deg(30, 80, 2)
# try:
#     pilot.wait_to_stop()
# except KeyboardInterrupt as e:
#     raise e
# finally:
#     pilot.stop()
#
# time.sleep(10)
#
# pilot.run_percent_drive_to_angle_deg(30, -90, 2)
# try:
#     pilot.wait_to_stop()
# except KeyboardInterrupt as e:
#     raise e
# finally:
#     pilot.stop()
#
# time.sleep(10)
#
# pilot.run_percent_drive_to_distance(15, 0, -2)
# try:
#     pilot.wait_to_stop()
# except KeyboardInterrupt as e:
#     raise e
# finally:
#     pilot.stop()
