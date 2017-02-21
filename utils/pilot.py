import logging
import math

from ev3dev.auto import *

from utils import utils
from utils.coordinator import Action, CycleThreadCoordinator
from utils.regulator import ValueRegulator

log = logging.getLogger(__name__)


class Wheel:
    def __init__(self, motor: Motor, gear_ratio: float, diameter: float,
                 width: float, offset: float):
        self.motor = motor
        self.diameter = diameter
        self.width = width
        self.offset = offset

        self.gear_ratio = gear_ratio
        self.motor_tacho_ratio = motor.count_per_rot / 360
        self.wheel_total_ratio = self.gear_ratio * self.motor_tacho_ratio
        self.wheel_degrees_to_cm_ratio = math.pi * self.diameter / 360


_REG_SPEED_P = 1
_REG_SPEED_I = 0.1
_REG_SPEED_D = 2

_REG_ERROR_P = 0.3
_REG_ERROR_I = 0.1
_REG_ERROR_D = 0.4

_CYCLE_TIME = 0.05


class MotorAction(Action):
    def __init__(self, motor, speed, max_duty_cycle=100):
        self.motor = motor
        self.speed = speed
        self.max_duty_cycle = max_duty_cycle

        self.start_time = time.time()
        self.start_position = self.motor.position
        self._speed_regulator = ValueRegulator(const_p=_REG_SPEED_P, const_i=_REG_SPEED_I, const_d=_REG_ERROR_D,
                                               getter_target=lambda: self.speed * (time.time() - self.start_time)
                                                                     + self.start_position)
        self._error_regulator = ValueRegulator(const_p=_REG_ERROR_P, const_i=_REG_ERROR_I,
                                               const_d=_REG_ERROR_I, const_target=0)

    def actual_progress(self):
        return (self.motor.position - self.start_position) / self.speed if self.speed != 0 else None

    def on_start(self):
        self._speed_regulator.reset()
        self._error_regulator.reset()

        self.start_time = time.time()
        self.start_position = self.motor.position
        self.motor.run_direct(duty_cycle_sp=0)

    def handle_loop(self, progress_error):
        duty_cycle = utils.crop_r(self._speed_regulator.regulate(self.motor.position), self.max_duty_cycle)
        duty_cycle += self._error_regulator.regulate(-progress_error * self.speed)
        self.motor.duty_cycle_sp = utils.crop_r(duty_cycle, self.max_duty_cycle)

    def on_stop(self):
        self.motor.stop()


class DriveCoordinator(CycleThreadCoordinator):
    def __init__(self, motor_actions, time_len=None, angle=None, distance=None):
        CycleThreadCoordinator.__init__(self, motor_actions, _CYCLE_TIME)
        self.setDaemon(True)

        self.time_len = time_len
        self.angle = angle
        self.distance = distance

        self.start_time = time.time()

    def on_start(self):
        CycleThreadCoordinator.on_start(self)
        self.start_time = time.time()

    def handle_loop(self):
        # TODO: add angle and distance target reached detection
        # if self.angle is not None:
        #     min_wheel, max_wheel = self.wheels[self.min_speed_pos], self.wheels[self.max_speed_pos]
        #     min_position, max_position = _calc_position(self.min_speed_pos), _calc_position(self.max_speed_pos)
        #     # TODO:implement
        #
        # if self.distance is not None:
        #     if self.distance == 0:
        #         self._do_stop()
        #         continue
        #
        #     min_wheel, max_wheel = self.wheels[self.min_speed_pos], self.wheels[self.max_speed_pos]
        #     min_position, max_position = _calc_position(self.min_speed_pos), _calc_position(self.max_speed_pos)
        #     if min_position == max_position or min_wheel.offset == max_wheel.offset:
        #         distance = max_position * max_wheel.wheel_total_ratio \
        #                    * max_wheel.wheel_degrees_to_cm_ratio
        #     else:
        #         offset_diff = abs(max_wheel.offset - min_wheel.offset)
        #         distance = (((max_position - min_position) / offset_diff * min_wheel.offset) + min_position)
        #         distance *= max_wheel.wheel_total_ratio * max_wheel.wheel_degrees_to_cm_ratio
        #
        #     if distance != 0 and abs(distance) > abs(self.distance) \
        #             and distance / abs(distance) == self.distance / abs(self.distance):
        #         self._do_stop()
        #         continue
        CycleThreadCoordinator.handle_loop(self)

    def _is_stop_loop(self):
        return CycleThreadCoordinator._is_stop_loop(self) \
               or (self.time_len is not None and time.time() - self.start_time >= self.time_len)

    def on_stop(self):
        CycleThreadCoordinator.on_stop(self)


# class _Driver(Thread):
#     def __init__(self, wheels, speeds, time_len=None, angle=None, distance=None, max_duty_cycle=100):
#         Thread.__init__(self)
#         self.setDaemon(True)
#         self.request_stop = False
#
#         self.wheels = wheels
#         self.speeds = speeds
#         self.min_speed_pos = self.max_speed_pos = 0
#         for i in range(1, len(self.speeds)):
#             if self.speeds[i] > self.speeds[self.max_speed_pos]:
#                 self.max_speed_pos = i
#             if self.speeds[i] < self.speeds[self.min_speed_pos]:
#                 self.min_speed_pos = i
#
#         self.time_len = time_len
#         self.angle = angle
#         self.distance = distance
#         self.max_duty_cycle = max_duty_cycle
#
#     def run(self):
#         start_positions = []
#         speed_regulators = []
#         error_regulators = []
#         for i in range(len(self.wheels)):
#             wheel = self.wheels[i]
#             if 'running' in wheel.motor.state:
#                 wheel.motor.stop()
#             start_positions.append(wheel.motor.position)
#             speed_regulators.append(PercentRegulator(const_p=_REG_SPEED_P, const_i=_REG_SPEED_I, const_d=_REG_ERROR_D,
#                                               const_target=self.speeds[i]))
#             error_regulators.append(PercentRegulator(const_p=_REG_ERROR_P, const_i=_REG_ERROR_I, const_d=_REG_ERROR_I,
#                                               const_target=0))
#
#         def _calc_position(i):
#             return self.wheels[i].motor.position - start_positions[i]
#
#         start_time = time.time()
#         last_time = start_time
#
#         for wheel in self.wheels:
#             wheel.motor.run_direct(duty_cycle_sp=0)
#
#         while not self.request_stop:
#             for i in range(len(self.wheels)):
#                 wheel = self.wheels[i]
#                 duty_cycle_diff = speed_regulators[i].regulate(wheel.motor.speed)
#                 target_speed = self.speeds[i]
#                 position = _calc_position(i)
#                 pos_error = 0
#                 for j in range(len(self.wheels)):
#                     if i == j:
#                         continue
#                     pos_error += (_calc_position(j) - position) / self.speeds[j] * target_speed
#                 duty_cycle_diff += error_regulators[i].regulate(pos_error)
#                 wheel.motor.duty_cycle_sp = min(100, max(-100, wheel.motor.duty_cycle_sp + duty_cycle_diff))
#
#             if self.angle is not None:
#                 min_wheel, max_wheel = self.wheels[self.min_speed_pos], self.wheels[self.max_speed_pos]
#                 min_position, max_position = _calc_position(self.min_speed_pos), _calc_position(self.max_speed_pos)
#                 # TODO:implement
#
#             if self.distance is not None:
#                 if self.distance == 0:
#                     self._do_stop()
#                     continue
#
#                 min_wheel, max_wheel = self.wheels[self.min_speed_pos], self.wheels[self.max_speed_pos]
#                 min_position, max_position = _calc_position(self.min_speed_pos), _calc_position(self.max_speed_pos)
#                 if min_position == max_position or min_wheel.offset == max_wheel.offset:
#                     distance = max_position * max_wheel.wheel_total_ratio \
#                                * max_wheel.wheel_degrees_to_cm_ratio
#                 else:
#                     offset_diff = abs(max_wheel.offset - min_wheel.offset)
#                     distance = (((max_position - min_position) / offset_diff * min_wheel.offset) + min_position)
#                     distance *= max_wheel.wheel_total_ratio * max_wheel.wheel_degrees_to_cm_ratio
#
#                 if distance != 0 and abs(distance) > abs(self.distance) \
#                         and distance / abs(distance) == self.distance / abs(self.distance):
#                     self._do_stop()
#                     continue
#
#             if self.time_len is not None and time.time() - start_time > self.time_len:
#                 self._do_stop()
#                 continue
#             last_time = utils.wait_to_cycle_time(last_time, _CYCLE_TIME)
#
#         for wheel in self.wheels:
#             wheel.motor.stop()
#
#     def stop(self):
#         self._do_stop()
#
#     def _do_stop(self):
#         self.request_stop = True
#
#     def wait_to_stop(self):
#         while self.is_alive():
#             time.sleep(0.05)


class Pilot:
    def __init__(self, wheels: array):
        self._running_coordinator = None
        self.wheels = wheels
        if len(self.wheels) == 0:
            self.max_speed = 0
        else:
            self.max_speed = self.wheels[0].motor.max_speed
            for wheel in wheels:
                self.max_speed = min(wheel.motor.max_speed, self.max_speed)

    def _stop_coordinator(self):
        if self._running_coordinator is not None:
            self._running_coordinator.stop()
            if self._running_coordinator.is_alive():
                self._running_coordinator.join()
            self._running_coordinator = None

    def reset(self):
        self._stop_coordinator()
        for wheel in self.wheels:
            wheel.motor.reset()

    def stop(self):
        self._stop_coordinator()
        for wheel in self.wheels:
            wheel.motor.stop()

    def run_timed(self, time_len, speeds=None, max_duty_cycle=100):  # TODO: add async=false param
        if speeds is None:
            speeds = []
            for i in range(len(self.wheels)):
                speeds.append(self.max_speed)
        elif len(speeds) != len(self.wheels):
            raise Exception()  # TODO: exception text

        actions = []
        for i in range(len(speeds)):
            actions.append(MotorAction(self.wheels[i].motor, speeds[i], max_duty_cycle))

        self._stop_coordinator()
        self._running_coordinator = DriveCoordinator(actions, time_len=time_len)
        self._running_coordinator.start()

    def run_forever(self, speeds=None, max_duty_cycle=100):
        self.run_timed(None, speeds, max_duty_cycle)

    def run_drive_forever(self, course, max_speed=None, max_duty_cycle=100):
        pass

    def run_drive_to_angle(self, angle, course, max_speed=None, max_duty_cycle=100):
        pass

    def run_drive_to_distance(self, distance, course, max_speed=None, max_duty_cycle=100):
        pass

    def run_drive_timed(self, time_len, course, max_speed=None, max_duty_cycle=100):
        pass

    def run_direct(self, course=0, max_duty_cycle=0):
        for wheel in self.wheels:
            wheel.motor.run_direct(duty_cycle_sp=0)

    def update_duty_cycle_sp(self, course, max_duty_cycle=100):
        pass

    def set_stop_action(self, stop_action):
        for wheel in self.wheels:
            wheel.stop_action = stop_action

    def get_positions(self):
        positions = []
        for wheel in self.wheels:
            positions.append(wheel.motor.position)
        return positions

    def get_states(self):
        states = []
        for wheel in self.wheels:
            states.append(wheel.motor.state)
        return states

    def repeat_while_running(self, method, cond_and=None, cond_or=None):
        pass

    def wait_to_stop(self, cond_and=None, cond_or=None):
        while True:
            coordinator = self._running_coordinator
            if coordinator is not None and coordinator.is_alive():
                coordinator.join()
                continue

            running = False
            for wheel in self.wheels:
                if 'running' in wheel.motor.state:
                    running = True
                    break

            if (not running or (cond_and is not None and not cond_and())) and (cond_or is None or not cond_or()):
                break

            time.sleep(0.05)
