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
        self.total_ratio = self.gear_ratio * self.motor_tacho_ratio
        self.unit_ratio = 360 / (math.pi * self.diameter)


_REG_SPEED_P = 1
_REG_SPEED_I = 0.1
_REG_SPEED_D = 2

_REG_ERROR_P = 0.3
_REG_ERROR_I = 0.1
_REG_ERROR_D = 0.4

_CYCLE_TIME = 0.05


class MotorAction(Action):
    def __init__(self, wheel, speed, max_duty_cycle=100):
        self.wheel = wheel
        self._motor = wheel.motor
        self._speed = speed
        self._max_duty_cycle = utils.crop_r(max_duty_cycle, 100)

        self._elapsed_time = time.time()
        self._start_position = self._motor.position
        self._speed_regulator = ValueRegulator(const_p=_REG_SPEED_P, const_i=_REG_SPEED_I, const_d=_REG_ERROR_D,
                                               getter_target=lambda: self._speed * (time.time() - self._elapsed_time)
                                                                     + self._start_position)
        # self._error_regulator = ValueRegulator(const_p=_REG_ERROR_P, const_i=_REG_ERROR_I,
        #                                        const_d=_REG_ERROR_I, const_target=0)

    def actual_progress(self):
        return (self._motor.position - self._start_position) / self._speed if self._speed != 0 else None

    def traveled_tacho_counts(self):
        return self._motor.position - self._start_position

    def traveled_units(self):
        return self.traveled_tacho_counts() / self.wheel.wheel_unit_ratio / self.wheel.wheel_total_ratio

    def on_start(self):
        self._speed_regulator.reset()
        # self._error_regulator.reset()

        self._start_position = self._motor.position
        self._motor.run_direct(duty_cycle_sp=0)

    def handle_loop(self, elapsed_time, progress_error):
        self._elapsed_time = elapsed_time
        duty_cycle = utils.crop_r(self._speed_regulator.regulate(self._motor.position), self._max_duty_cycle)
        # duty_cycle += self._error_regulator.regulate(-progress_error * self.speed)
        self._motor.duty_cycle_sp = utils.crop_r(duty_cycle, self._max_duty_cycle)

    def on_stop(self):
        self._motor.stop()


class DriveCoordinator(CycleThreadCoordinator):
    def __init__(self, motor_actions, time_len=None, angle_deg=None, distance_unit=None):
        CycleThreadCoordinator.__init__(self, motor_actions, diff_limit=10, cycle_time=_CYCLE_TIME)
        # TODO: test diff_limit
        self.setDaemon(True)

        self._time_len = time_len
        self._angle_deg = angle_deg
        self._distance_unit = distance_unit

        if len(motor_actions) == 0:
            self.stop()
        else:
            self._min_action = self._max_action = motor_actions[0].wheel
            for motor_action in motor_actions:
                if motor_action.wheel.offset < self._min_action.wheel.offset:
                    self._min_action = motor_action
                if motor_action.wheel.offset > self._max_action.wheel.offset:
                    self._max_action = motor_action

    def _is_stop_loop(self):
        return CycleThreadCoordinator._is_stop_loop(self) \
               or self._check_time() \
               or self._check_distance() \
               or self._check_angle()

    def _check_time(self) -> bool:
        return self._time_len is not None and time.time() - self._start_time >= self._time_len

    def _check_distance(self) -> bool:
        if self._distance_unit is None:
            return False

        if self._distance_unit == 0:
            return True

        distance_unit = 0
        for action in self._actions:
            distance_unit += action.traveled_units()
        distance_unit /= len(self._actions)

        return abs(distance_unit) > abs(self._distance_unit)

    def _check_angle(self) -> bool:
        if self._angle_deg is None or self._min_action.wheel.offset == self._max_action.wheel.offset:
            return False

        if self._angle_deg == 0:
            return True

        min_action = self._min_action
        max_action = self._max_action
        min_traveled = min_action.traveled_units()
        max_traveled = max_action.traveled_units()

        if max_traveled == 0:
            if min_traveled == 0:
                return False
            min_action, max_action = max_action, min_action
            min_traveled, max_traveled = max_traveled, min_traveled

        ratio = min_traveled / max_traveled
        radius = (min_action.wheel.offset - ratio * max_action.wheel.offset) / (ratio - 1)
        min_radius = radius + min_action.wheel.offset
        max_radius = radius + max_action.wheel.offset

        if abs(min_radius) > abs(max_radius):
            circuit = min_radius * math.pi
            angle_deg = circuit / min_traveled
        else:
            circuit = max_radius * math.pi
            angle_deg = circuit / max_traveled

        return abs(angle_deg) > abs(self._angle_deg)


class Pilot:
    def __init__(self, wheels: array):
        self._running_coordinator = None
        self._wheels = []
        self._has_wheels = False

        self._max_speed_tacho = 0
        self._max_speed_deg = 0
        self._max_speed_unit = 0

        self._max_offset = 0

        self.set_wheels(wheels)

    def is_connected(self):
        return self._has_wheels

    def set_wheels(self, wheels: array):
        self.stop()
        self.wait_to_stop()

        self._wheels = wheels

        if len(wheels) == 0:
            self._has_wheels = False
        else:
            self._has_wheels = True
            for wheel in wheels:
                if not wheel.motor.connected:
                    self._has_wheels = False
                    break

        self._refresh_max_speed()
        self._refresh_max_offset()
        self.reset()

    def get_max_speed_tacho(self):
        return self._max_speed_tacho

    def get_max_speed_deg(self):
        return self._max_speed_deg

    def get_max_speed_unit(self):
        return self._max_speed_unit

    def _refresh_max_speed(self):
        if len(self._wheels) == 0:
            self._max_speed_tacho = 0
        else:
            self._max_speed_tacho = self._wheels[0].motor.max_speed
            self._max_speed_deg = self._max_speed_tacho / self._wheels[0].wheel_total_ratio
            self._max_speed_unit = self._max_speed_deg / self._wheels[0].wheel_unit_ratio
            for wheel in self._wheels:
                max_speed_tacho = wheel.motor.max_speed
                self._max_speed_tacho = min(max_speed_tacho, self._max_speed_tacho)
                max_speed_deg = max_speed_tacho / wheel.wheel_total_ratio
                self._max_speed_deg = min(max_speed_deg, self._max_speed_deg)
                max_speed_unit = max_speed_deg / wheel.wheel_unit_ratio
                self._max_speed_unit = min(max_speed_unit, self._max_speed_unit)

    def _refresh_max_offset(self):
        if len(self._wheels) == 0:
            self._max_offset = 0
        else:
            self._max_offset = abs(self._wheels[0].offset)
            for wheel in self._wheels:
                self._max_offset = max(self._max_offset, abs(wheel.offset))

    def _stop_coordinator(self):
        if self._running_coordinator is not None:
            self._running_coordinator.stop()
            if self._running_coordinator.is_alive():
                self._running_coordinator.join()
            self._running_coordinator = None

    def reset(self):
        self._stop_coordinator()
        for wheel in self._wheels:
            wheel.motor.reset()
            wheel.motor.stop_action = 'brake'

    def stop(self):
        self._stop_coordinator()
        for wheel in self._wheels:
            wheel.motor.stop()

    def _course_percent_to_speeds(self, course_percent, max_speed):
        duty_cycles = []

        if course_percent == 0:
            for i in range(len(self._wheels)):
                duty_cycles.append(max_speed)
            return duty_cycles

        if max_speed == 0:
            for i in range(len(self._wheels)):
                duty_cycles.append(0)
            return duty_cycles

        max_pos = self._max_offset * (1 if course_percent > 0 else -1)
        for wheel in self._wheels:
            effect = abs(wheel.offset - max_pos) / (2 * self._max_offset)
            duty_cycles.append(max_speed - (course_percent * effect / 100 * max_speed))

        return duty_cycles

    def _course_r_to_speeds(self, course_r, speed, max_speed):
        if course_r is 0:
            course_r = 0.0001
        no_warn = False
        if speed is None:
            speed = max_speed
            no_warn = True

        speeds = []
        max_found_speed = 0
        if course_r is None:
            max_found_speed = max_speed
            for i in range(len(self._wheels)):
                speeds.append(max_speed)
        else:
            center_way_circuit = course_r * math.pi
            one_unit_speed = speed / center_way_circuit
            for i in range(len(self._wheels)):
                wheel = self._wheels[i]
                wheel_way_circuit = (course_r + wheel.offset) * math.pi
                wheel_speed_unit = one_unit_speed * wheel_way_circuit
                max_found_speed = max(max_found_speed, abs(wheel_speed_unit))
                speeds.append(wheel_speed_unit)

        if max_found_speed > max_speed:
            if not no_warn:
                log.warning('Can\'t use drive speed ' + str(speed) + ', '
                            + 'it requires wheel speed ' + str(max_found_speed) + ', '
                            + 'but wheel max wheel speed is ' + str(max_speed) + '. '
                            + 'Drive will be slower.')
            change = self._max_speed_unit / max_found_speed
            for i in range(len(speeds)):
                speeds[i] *= change
            max_found_speed *= change
        return speeds

    def _generate_max_speeds_tacho(self):
        speeds_tacho = []
        for i in range(len(self._wheels)):
            speeds_tacho.append(self._max_speed_tacho)
        return speeds_tacho

    def _generate_max_speeds_deg(self):
        speeds_deg = []
        for i in range(len(self._wheels)):
            speeds_deg.append(self._max_speed_deg)
        return speeds_deg

    def _generate_max_speeds_unit(self):
        speeds_unit = []
        for i in range(len(self._wheels)):
            speeds_unit.append(self._max_speed_unit)
        return speeds_unit

    def _validate_len(self, data_array):
        if len(data_array) != len(self._wheels):
            raise Exception('len(data_array) != len(wheels)')

    def _speeds_unit_to_deg(self, speeds_unit):
        speeds_deg = []
        for i in range(len(speeds_unit)):
            speeds_deg.append(speeds_unit[i] * self._wheels[i].wheel_unit_ratio)
        return speeds_deg

    def _speed_deg_to_tacho(self, speeds_deg):
        speeds_tacho = []
        for i in range(len(speeds_deg)):
            speeds_tacho.append(speeds_deg[i] * self._wheels[i].wheel_total_ratio)
        return speeds_deg

    def _raw_run_unit(self, time_len=None, angle_deg=None, distance_unit=None, speeds_unit=None, max_duty_cycle=100,
                      async=False):
        if speeds_unit is None:
            speeds_tacho = self._generate_max_speeds_tacho()
        else:
            self._validate_len(speeds_unit)
            speeds_tacho = self._speed_deg_to_tacho(self._speeds_unit_to_deg(speeds_unit))

        self._raw_run_tacho_ready(time_len, angle_deg, distance_unit, speeds_tacho, max_duty_cycle, async)

    def _raw_run_deg(self, time_len=None, angle_deg=None, distance_unit=None, speeds_deg=None, max_duty_cycle=100,
                     async=False):
        if speeds_deg is None:
            speeds_tacho = self._generate_max_speeds_tacho()
        else:
            self._validate_len(speeds_deg)
            speeds_tacho = self._speed_deg_to_tacho(speeds_deg)

        self._raw_run_tacho_ready(time_len, angle_deg, distance_unit, speeds_tacho, max_duty_cycle, async)

    def _raw_run_tacho(self, time_len=None, angle_deg=None, distance_unit=None,
                       speeds_tacho=None, max_duty_cycle=100, async=False):
        if speeds_tacho is None:
            speeds_tacho = self._generate_max_speeds_tacho()
        else:
            self._validate_len(speeds_tacho)

        self._raw_run_tacho_ready(time_len, angle_deg, distance_unit, speeds_tacho, max_duty_cycle, async)

    def _raw_run_tacho_ready(self, time_len, angle_deg, distance_unit, speeds_tacho, max_duty_cycle, async):
        if async:
            self._stop_coordinator()
            for i in range(len(speeds_tacho)):
                wheel = self._wheels[i]
                if time_len is not None:
                    wheel.motor.run_timed(speed_sp=speeds_tacho[i], time_sp=int(time_len * 1000))
                elif angle_deg is not None:
                    raise Exception('Unsupported')  # TODO: support
                elif distance_unit is not None:
                    raise Exception('Unsupported')  # TODO: support
                else:
                    wheel.motor.run_forever(speed_sp=speeds_tacho[i])
        else:
            actions = []
            for i in range(len(speeds_tacho)):
                actions.append(MotorAction(self._wheels[i].motor, speeds_tacho[i], max_duty_cycle))

            self._stop_coordinator()
            self._running_coordinator = DriveCoordinator(actions, time_len, angle_deg, distance_unit)
            self._running_coordinator.start()

    def _raw_run_drive_unit(self, time_len=None, angle_deg=None, distance_unit=None,
                            course_r=None, speed_unit=None, max_duty_cycle=100, async=False):
        self._raw_run_unit(time_len=time_len, angle_deg=angle_deg, distance_unit=distance_unit,
                           speeds_unit=self._course_r_to_speeds(course_r, speed_unit, self._max_speed_unit),
                           max_duty_cycle=max_duty_cycle, async=async)

    def _raw_run_percent_drive_unit(self, time_len=None, angle_deg=None, distance_unit=None,
                                    course_percent=None, speed_unit=None, max_duty_cycle=100, async=False):
        self._raw_run_unit(time_len=time_len, angle_deg=angle_deg, distance_unit=distance_unit,
                           speeds_unit=self._course_percent_to_speeds
                           (course_percent, min(speed_unit, self._max_speed_unit)),
                           max_duty_cycle=max_duty_cycle, async=async)

    def run_timed(self, time_len: float, speeds_tacho: array = None, max_duty_cycle: int = 100, async: bool = False):
        self._raw_run_tacho(time_len=time_len, speeds_tacho=speeds_tacho,
                            max_duty_cycle=max_duty_cycle, async=async)

    def run_forever(self, speeds_tacho: array = None, max_duty_cycle: int = 100, async: bool = False):
        self._raw_run_tacho(speeds_tacho=speeds_tacho, max_duty_cycle=max_duty_cycle, async=async)

    def run_deg_timed(self, time_len: float, speeds_deg: array = None, max_duty_cycle: int = 100, async: bool = False):
        self._raw_run_deg(time_len=time_len, speeds_deg=speeds_deg,
                          max_duty_cycle=max_duty_cycle, async=async)

    def run_deg_forever(self, speeds_deg: array = None, max_duty_cycle: int = 100, async: bool = False):
        self._raw_run_deg(speeds_deg=speeds_deg, max_duty_cycle=max_duty_cycle, async=async)

    def run_unit_timed(self, time_len: float, speeds_unit: array = None, max_duty_cycle: int = 100,
                       async: bool = False):
        self._raw_run_unit(time_len=time_len, speeds_unit=speeds_unit,
                           max_duty_cycle=max_duty_cycle, async=async)

    def run_unit_forever(self, speeds_unit: array = None, max_duty_cycle: int = 100, async: bool = False):
        self._raw_run_unit(speeds_unit=speeds_unit, max_duty_cycle=max_duty_cycle, async=async)

    def run_drive_forever(self, course_r: float, speed_unit: float = None, max_duty_cycle: int = 100,
                          async: bool = False):
        self._raw_run_drive_unit(course_r=course_r, speed_unit=speed_unit, max_duty_cycle=max_duty_cycle, async=async)

    def run_drive_timed(self, time_len: float, course_r: float, speed_unit: float = None,
                        max_duty_cycle: int = 100, async: bool = False):
        self._raw_run_drive_unit(time_len=time_len, course_r=course_r, speed_unit=speed_unit,
                                 max_duty_cycle=max_duty_cycle, async=async)

    def run_drive_to_angle_deg(self, angle_deg: float, course_r: float, speed_unit: float = None,
                               max_duty_cycle: int = 100, async: bool = False):
        self._raw_run_drive_unit(angle_deg=angle_deg, course_r=course_r, speed_unit=speed_unit,
                                 max_duty_cycle=max_duty_cycle, async=async)

    def run_drive_to_distance(self, distance_unit: float, course_r: float, speed_unit: float = None,
                              max_duty_cycle: int = 100, async: bool = False):
        self._raw_run_drive_unit(distance_unit=distance_unit, course_r=course_r, speed_unit=speed_unit,
                                 max_duty_cycle=max_duty_cycle, async=async)

    def run_percent_drive_forever(self, course_percent: float, speed_unit: float = None,
                                  max_duty_cycle: int = 100, async: bool = False):
        self._raw_run_percent_drive_unit(course_percent=course_percent, speed_unit=speed_unit,
                                         max_duty_cycle=max_duty_cycle, async=async)

    def run_percent_drive_timed(self, time_len: float, course_percent: float, speed_unit: float = None,
                                max_duty_cycle: int = 100, async: bool = False):
        self._raw_run_percent_drive_unit(time_len=time_len, course_percent=course_percent, speed_unit=speed_unit,
                                         max_duty_cycle=max_duty_cycle, async=async)

    def run_percent_drive_to_angle_deg(self, angle_deg: float, course_percent: float, speed_unit: float = None,
                                       max_duty_cycle: int = 100, async: bool = False):
        self._raw_run_percent_drive_unit(angle_deg=angle_deg, course_percent=course_percent, speed_unit=speed_unit,
                                         max_duty_cycle=max_duty_cycle, async=async)

    def run_percent_drive_to_distance(self, distance_unit: float, course_percent: float, speed_unit: float = None,
                                      max_duty_cycle: int = 100, async: bool = False):
        self._raw_run_percent_drive_unit(distance_unit=distance_unit, course_percent=course_percent,
                                         speed_unit=speed_unit, max_duty_cycle=max_duty_cycle, async=async)

    def run_direct(self, course_percent: float = 0, max_duty_cycle: int = 0):
        duty_cycles = self._course_percent_to_speeds(course_percent, max_duty_cycle)
        for i in range(len(self._wheels)):
            self._wheels[i].motor.run_direct(duty_cycle_sp=duty_cycles[i])

    def update_duty_cycle_sp(self, course_percent: float, max_duty_cycle: int = 100):
        duty_cycles = self._course_percent_to_speeds(course_percent, max_duty_cycle)
        for i in range(len(self._wheels)):
            self._wheels[i].motor.duty_cycle_sp = duty_cycles[i]

    def set_stop_action(self, stop_action: str):
        for wheel in self._wheels:
            wheel.stop_action = stop_action

    def restore_positions(self, positions: array, speed_unit=None):
        if speed_unit is None:
            speed_unit = self._max_speed_unit
        speed_tacho = self._speed_deg_to_tacho(self._speeds_unit_to_deg(speed_unit))

        changes = []
        max_change = 0
        for i in range(len(positions)):
            change = positions[i] - self._wheels[i].motor.position
            changes.append(change)
            max_change = max(max_change, abs(change))

        self._validate_len(positions)
        for i in range(len(positions)):
            wheel_speed_tacho = speed_tacho / max_change * changes[i]
            self._wheels[i].motor.run_to_abs_pos(speed_sp=wheel_speed_tacho, position_sp=positions[i])

    def get_positions(self):
        positions = []
        for wheel in self._wheels:
            positions.append(wheel.motor.position)
        return positions

    def get_states(self):
        states = []
        for wheel in self._wheels:
            states.append(wheel.motor.state)
        return states

    def is_running(self):
        coordinator = self._running_coordinator
        if coordinator is not None and coordinator.is_alive():
            return True

        for wheel in self._wheels:
            if 'running' in wheel.motor.state:
                return True

        return False

    def repeat_while_running(self, method, cond_and=None, cond_or=None):
        while (self.is_running() and (cond_and is None or cond_and())) or (cond_or is not None and cond_or()):
            method()

    def wait_to_stop(self, cond_and=None, cond_or=None):
        self.repeat_while_running(lambda: time.sleep(0.05), cond_and, cond_or)
