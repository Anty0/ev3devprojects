#!/usr/bin/env python3

import config as _config
from hardware import *
from utils import utils
from utils.behaviour import Behaviour, MultiBehaviour, BehaviourController
from utils.regulator import *
from utils.robot_program import *


class CollisionAvoidBehaviour(Behaviour, ControllerConfigWrapper):
    def __init__(self, controller):
        Behaviour.__init__(self)
        ControllerConfigWrapper.__init__(self, controller)

        self._start_positions = []
        self._power_regulator = PercentRegulator(const_p=1, const_i=3, const_d=2,  # TODO: to config
                                                 getter_target=lambda: -self._get_target_distance())

    def _get_target_distance(self):
        self.get_config_value('OBSTACLE_MIN_DISTANCE') * 0.8

    def should_take_control(self):
        if not self.get_config_value('COLLISION_AVOID'):
            return False

        min_distance = self.get_config_value('OBSTACLE_MIN_DISTANCE')
        cycle_time = 0.1
        change = 100 - min_distance
        last_distance_val = SCANNER.value_scan(0)
        last_time = time.time()
        while last_distance_val < min_distance:
            distance_val = SCANNER.value_scan(0)
            if distance_val < min_distance * 0.65:
                return True

            change = abs(distance_val - last_distance_val) + change / 2
            last_distance_val = distance_val
            if change < 5:
                return False

            last_time = utils.wait_to_cycle_time(last_time, cycle_time)

        return False

    def reset_regulation(self):
        self._power_regulator.reset()

    def on_take_control(self):
        self._power_regulator.reset()
        self._start_positions = PILOT.get_positions()
        PILOT.run_direct()

    def on_loose_control(self):
        PILOT.stop()
        SCANNER.rotate_scanner_to_pos(0)

    def handle_loop(self):
        cycle_time = 0.05  # TODO: to config
        wait_time = 2  # TODO: to config
        last_time = time.time()
        while not self.controller.stop:
            distance_val = SCANNER.value_scan(0)
            power = self._power_regulator.regulate(-distance_val)
            PILOT.update_duty_cycle(0, utils.crop_m(power, max_out=0))

            if distance_val > self._get_target_distance():
                PILOT.stop()

                last_time = time.time()
                distance_val = SCANNER.value_scan(0)
                while distance_val > self._get_target_distance():
                    if self.controller.stop:
                        return

                    if time.time() - last_time < wait_time:
                        time.sleep(cycle_time)
                    else:
                        problem = False
                        for i in [-1, 1]:
                            side_distance_val = SCANNER.value_scan(35 * i)

                            if side_distance_val < self._get_target_distance():
                                SCANNER.rotate_scanner_to_pos(0)
                                problem = True

                        if problem:
                            continue

                        SCANNER.rotate_scanner_to_pos(0)

                        target_speed = self.get_config_value('TARGET_POWER') / 100 * PILOT.get_max_speed_unit()
                        PILOT.restore_positions(self._start_positions, speed_unit=target_speed)

                        distance_val = SCANNER.value_scan(0)
                        while distance_val > self._get_target_distance():
                            if self.controller.stop:
                                return

                            if not PILOT.is_running():
                                PILOT.stop()
                                return
                            distance_val = SCANNER.value_scan(0)

                        PILOT.stop()
                        break

                    distance_val = SCANNER.value_scan(0)

                PILOT.run_direct()
                last_time = time.time()

            last_time = utils.wait_to_cycle_time(last_time, cycle_time)
        pass


class ObstacleAvoidBehaviour(Behaviour, ControllerConfigWrapper):
    def __init__(self, controller):
        Behaviour.__init__(self)
        ControllerConfigWrapper.__init__(self, controller)

    def should_take_control(self):
        return self.get_config_value('OBSTACLE_AVOID') \
               and SCANNER.value_get() < self.get_config_value('OBSTACLE_MIN_DISTANCE')

    def on_take_control(self):
        pass

    def on_loose_control(self):
        PILOT.stop()
        SCANNER.rotate_scanner_to_pos(0)

    def handle_loop(self):
        wait_time = 0.05

        min_reflect = self.controller.get_min_reflex()
        max_reflect = self.controller.get_max_reflex()
        target_reflect = self.get_config_value('TARGET_REFLECT')

        target_power = self.get_config_value('TARGET_POWER')
        target_speed = target_power / 100 * PILOT.get_max_speed_unit()

        min_distance = self.get_config_value('OBSTACLE_MIN_DISTANCE')
        obstacle_width = self.get_config_value('OBSTACLE_WIDTH')
        obstacle_height = self.get_config_value('OBSTACLE_HEIGHT')
        side = self.get_config_value('OBSTACLE_AVOID_SIDE')
        course = 80 * side
        scanner_pos = 90 * side

        PILOT.run_percent_drive_to_angle_deg(90, course, speed_unit=target_speed)
        if obstacle_width is None or obstacle_height is None:
            SCANNER.rotate_scanner_to_pos(scanner_pos)
        PILOT.wait_to_stop()

        if obstacle_width == 0 or obstacle_height == 0:
            for i in range(2):
                PILOT.run_percent_drive_forever(0, speed_unit=target_speed)
                while SCANNER.value_get() < min_distance:
                    time.sleep(wait_time)
                PILOT.run_percent_drive_to_angle_deg(90, -course, speed_unit=target_speed)
                PILOT.wait_to_stop()
        else:
            PILOT.run_percent_drive_to_distance((obstacle_width / 2) - (ROBOT_WIDTH / 3), 0, speed_unit=target_speed)
            PILOT.wait_to_stop()
            PILOT.run_percent_drive_to_angle_deg(90, -course, speed_unit=target_speed)
            PILOT.wait_to_stop()
            PILOT.run_percent_drive_to_distance(obstacle_height, 0)
            PILOT.wait_to_stop()
            PILOT.run_percent_drive_to_angle_deg(90, -course, speed_unit=target_speed)
            PILOT.wait_to_stop()

        PILOT.run_percent_drive_forever(0, speed_unit=target_speed)
        SCANNER.rotate_scanner_to_pos(0)

        while 100 * (COLOR_SENSOR.value() - min_reflect) / (max_reflect - min_reflect) > target_reflect:
            time.sleep(wait_time)

        PILOT.run_percent_drive_forever(course, speed_unit=target_speed)

        while 100 * (COLOR_SENSOR.value() - min_reflect) / (max_reflect - min_reflect) <= target_reflect:
            time.sleep(wait_time)

        time.sleep(wait_time * 4)

        while 100 * (COLOR_SENSOR.value() - min_reflect) / (max_reflect - min_reflect) > target_reflect:
            time.sleep(wait_time)

        PILOT.stop()


class ObstacleDetectionBehaviour(MultiBehaviour, ControllerConfigWrapper):
    def __init__(self, controller):
        ControllerConfigWrapper.__init__(self, controller)
        MultiBehaviour.__init__(self, [
            CollisionAvoidBehaviour(controller),
            ObstacleAvoidBehaviour(controller)
        ])

    def take_control(self) -> bool:
        if not SCANNER.is_connected() or not SCANNER.has_motor() or SCANNER.is_running() \
                or (not self.get_config_value('OBSTACLE_AVOID') and not self.get_config_value('COLLISION_AVOID')):
            return False

        if SCANNER.angle_get() == 0:
            return SCANNER.value_get() < self.get_config_value('OBSTACLE_MIN_DISTANCE')
        else:
            SCANNER.rotate_scanner_to_pos(0)
            return False


class LineFollowBehaviour(Behaviour, ControllerConfigWrapper):
    def __init__(self, controller):
        Behaviour.__init__(self)
        ControllerConfigWrapper.__init__(self, controller)

        self._last_time = time.time()
        self._last_power = 0

        self._steer_regulator = PercentRegulator(getter_p=lambda: self.get_config_value('REG_STEER_P'),
                                                 getter_i=lambda: self.get_config_value('REG_STEER_I'),
                                                 getter_d=lambda: self.get_config_value('REG_STEER_D'),
                                                 getter_target=lambda: self.get_config_value('TARGET_REFLECT'))

    def reset_regulation(self):
        self._steer_regulator.reset()

    def on_take_control(self):
        self._last_power = 0
        self.reset_regulation()
        PILOT.run_direct()
        self._last_time = time.time()

    def on_loose_control(self):
        PILOT.stop()

    def should_take_control(self) -> bool:
        return True

    def _get_target_power(self):
        if self.get_config_value('PAUSE_POWER') or self.controller.stop:
            return 0
        return self.get_config_value('TARGET_POWER')

    def _next_power(self, cycle_time):
        target_power = self._get_target_power()
        if self.get_config_value('REGULATE_TARGET_POWER_CHANGE'):
            diff = target_power - self._last_power
            change = 2 * cycle_time
            if diff != 0:
                if change <= abs(diff):
                    self._last_power = target_power
                else:
                    self._last_power += change * (diff / abs(diff))
        else:
            self._last_power = target_power
        return self._last_power

    def _test_sharp_turn(self, min_reflect, max_reflect, target_power, target_cycle_time) -> bool:
        if not self.get_config_value('SHARP_TURN_DETECT') or not self._steer_regulator.last_derivative > 25:
            # TODO: test and add to config
            return False

        side = self.get_config_value('SHARP_TURN_ROTATE_SIDE')
        target_reflect = self.get_config_value('TARGET_REFLECT')
        PILOT.update_duty_cycle(50 * side, target_power)

        while 100 * (COLOR_SENSOR.value() - min_reflect) / (max_reflect - min_reflect) <= target_reflect:
            time.sleep(target_cycle_time)

        time.sleep(target_cycle_time)

        while 100 * (COLOR_SENSOR.value() - min_reflect) / (max_reflect - min_reflect) > target_reflect:
            time.sleep(target_cycle_time)

        self.reset_regulation()
        self._last_time = time.time()
        return True

    def _test_stop_on_line_end(self) -> bool:
        if not self.get_config_value('STOP_ON_LINE_END') or not self._steer_regulator.last_derivative < -25:
            # TODO: test and add to config
            return False

        self.controller.force_loose_control()
        self.controller.request_exit()
        return True

    def handle_loop(self):
        min_reflect = self.controller.get_min_reflex()
        max_reflect = self.controller.get_max_reflex()
        line_side = self.get_config_value('LINE_SIDE')
        target_cycle_time = self.get_config_value('TARGET_CYCLE_TIME')
        target_power = self._next_power(target_cycle_time)

        read_val = COLOR_SENSOR.value()
        read_percent = 100 * (read_val - min_reflect) / (max_reflect - min_reflect)
        course = utils.crop_r(self._steer_regulator.regulate(read_percent) * line_side)

        if self._test_sharp_turn(min_reflect, max_reflect, target_power, target_cycle_time) \
                or self._test_stop_on_line_end():
            return

        PILOT.update_duty_cycle(course, target_power)

        self._last_time = utils.wait_to_cycle_time(self._last_time, target_cycle_time)


class LineFollowController(SimpleRobotProgramController, BehaviourController):
    def __init__(self, robot_program, config=None):
        SimpleRobotProgramController.__init__(self, robot_program, config=config)
        BehaviourController.__init__(self, robot_program, [
            ObstacleDetectionBehaviour(self),
            LineFollowBehaviour(self)
        ])

    def get_min_reflex(self):
        result = self.get_private_config_value('MIN_REFLECT')
        return result if result is not None else self.get_config_value('MIN_REFLECT')

    def get_max_reflex(self):
        result = self.get_private_config_value('MAX_REFLECT')
        return result if result is not None else self.get_config_value('MAX_REFLECT')

    @staticmethod
    def _scan_min_max_reflect(reflect):
        read = COLOR_SENSOR.value()
        reflect[0] = min(reflect[0], read)
        reflect[1] = max(reflect[1], read)

    def on_start(self):
        reflect = [None, None]
        if self.get_config_value('DETECT_REFLECT'):
            reflect = [100, 0]

            PILOT.run_percent_drive_to_angle_deg(45, 200, 10)
            PILOT.repeat_while_running(lambda: self._scan_min_max_reflect(reflect))

            PILOT.run_percent_drive_to_angle_deg(90, -200, 10)
            PILOT.repeat_while_running(lambda: self._scan_min_max_reflect(reflect))

            PILOT.run_percent_drive_to_angle_deg(45, 200, 10)
            PILOT.repeat_while_running(lambda: self._scan_min_max_reflect(reflect))

        self.set_private_config_value('MIN_REFLECT', reflect[0])
        self.set_private_config_value('MAX_REFLECT', reflect[1])

    def on_exit(self):
        reset_hardware()

    def stop_loop(self):
        last_behaviour = self.last_behaviour
        return super().stop_loop() and (not isinstance(last_behaviour, LineFollowBehaviour)
                                        or last_behaviour.last_power < 5)

    def on_config_change(self):
        super().on_config_change()
        last_behaviour = self.last_behaviour
        if isinstance(last_behaviour, LineFollowBehaviour):
            last_behaviour.reset_regulation()

    def on_config_value_change(self, name, new_value):
        super().on_config_value_change(name, new_value)
        last_behaviour = self.last_behaviour
        if (name == 'REG_STEER_I' or name == 'REG_STEER_D') \
                and isinstance(last_behaviour, LineFollowBehaviour):
            last_behaviour.reset_regulation()


class LineFollowRobotProgram(RobotProgram):
    def __init__(self):
        super().__init__('LineFollower', _config.LINE_FOLLOWER_CONFIG_VALUES)

    def execute(self, config=None) -> LineFollowController:
        if not PILOT.is_connected() or not HAS_COLOR_SENSOR:
            raise Exception('LineFollower requires wheels and color sensor at last.')
        return LineFollowController(self, config)


def run():
    controller = LineFollowRobotProgram().execute()
    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass

    controller.request_exit()
    controller.wait_to_exit()


if __name__ == '__main__':
    run()
