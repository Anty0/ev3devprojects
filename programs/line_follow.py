#!/usr/bin/env python3

import config as _config
from ..hardware import *
from ..utils.behaviour import Behaviour, MultiBehaviour, BehaviourController
from ..utils.regulator import *
from ..utils.robot_program import *


class CollisionAvoidBehaviour(Behaviour, ControllerConfigWrapper):
    def __init__(self, controller):
        Behaviour.__init__(self)
        ControllerConfigWrapper.__init__(self, controller)

        self.power_regulator = Regulator(const_p=1, const_i=0, const_d=3,  # TODO: to config
                                         getter_target=self._get_target_distance)

    def _get_target_distance(self):
        self.get_config_value('OBSTACLE_MIN_DISTANCE') * 0.8

    def take_control(self):
        if not self.get_config_value('COLLISION_AVOID'):
            return False

        min_distance = self.get_config_value('OBSTACLE_MIN_DISTANCE')
        target_cycle_time = 0.1  # TODO: to config
        change = MAX_DISTANCE - min_distance
        last_distance_val = DISTANCE_SENSOR.value()
        last_time = time.time()
        while last_distance_val < min_distance:
            distance_val = DISTANCE_SENSOR.value()
            if distance_val < min_distance * 0.65:
                return True

            change = abs(distance_val - last_distance_val) + change / 2
            last_distance_val = distance_val
            if change < 5:
                return False

            new_time = time.time()
            sleep_time = target_cycle_time - (new_time - last_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
            elif sleep_time < -target_cycle_time * 5:
                log.warn('Obstacle avoid detection is getting late. It\'s late %s seconds.'
                         ' Use bigger cycle time.' % sleep_time)
            last_time += target_cycle_time
            pass

        return False

    def reset_regulation(self):
        self.power_regulator.reset()

    def on_take_control(self):
        self.power_regulator.reset()
        LEFT_MOTOR.position = RIGHT_MOTOR.position = 0
        LEFT_MOTOR.run_direct(duty_cycle_sp=0)
        RIGHT_MOTOR.run_direct(duty_cycle_sp=0)

    def on_loose_control(self):
        LEFT_MOTOR.stop()
        RIGHT_MOTOR.stop()
        SCANNER_MOTOR.run_to_abs_pos(speed_sp=SCANNER_MOTOR.max_speed / 5, position_sp=0)
        pass

    def handle_loop(self):
        target_cycle_time = 0.1  # TODO: to config
        target_wait_time = 2  # TODO: to config
        last_time = time.time()
        while not self.controller.stop:
            distance_val = DISTANCE_SENSOR.value()
            power = self.power_regulator.regulate(distance_val)
            LEFT_MOTOR.duty_cycle_sp = RIGHT_MOTOR.duty_cycle_sp = power if power < 0 else 0
            if distance_val > self._get_target_distance():
                LEFT_MOTOR.stop()
                RIGHT_MOTOR.stop()

                last_time = time.time()
                distance_val = DISTANCE_SENSOR.value()
                while distance_val > self._get_target_distance():
                    if self.controller.stop:
                        return

                    if time.time() - last_time < target_wait_time:
                        time.sleep(target_cycle_time)
                    else:
                        for i in [-1, 1]:
                            SCANNER_MOTOR.run_to_abs_pos(speed_sp=SCANNER_MOTOR.max_speed / 5,
                                                         position_sp=35 * ROBOT_MOTOR_SCANNER_GEAR_RATIO * i)

                            while 'running' in SCANNER_MOTOR.state:
                                time.sleep(target_cycle_time)

                            side_distance_val = DISTANCE_SENSOR.value()

                            if side_distance_val < self._get_target_distance():
                                SCANNER_MOTOR.run_to_abs_pos(speed_sp=SCANNER_MOTOR.max_speed / 5, position_sp=0)
                                continue

                        SCANNER_MOTOR.run_to_abs_pos(speed_sp=SCANNER_MOTOR.max_speed / 5, position_sp=0)

                        target_speed = self.get_config_value('TARGET_POWER') / 100 * LEFT_MOTOR.max_speed
                        LEFT_MOTOR.run_to_abs_pos(speed_sp=target_speed, position_sp=0)
                        RIGHT_MOTOR.run_to_abs_pos(speed_sp=target_speed, position_sp=0)
                        distance_val = DISTANCE_SENSOR.value()
                        while distance_val > self._get_target_distance():
                            if self.controller.stop:
                                return

                            if 'running' not in LEFT_MOTOR.state and 'running' not in RIGHT_MOTOR.state:
                                return
                            distance_val = DISTANCE_SENSOR.value()
                        LEFT_MOTOR.stop()
                        RIGHT_MOTOR.stop()
                        break

                    distance_val = DISTANCE_SENSOR.value()

                LEFT_MOTOR.run_direct(duty_cycle_sp=0)
                RIGHT_MOTOR.run_direct(duty_cycle_sp=0)
                last_time = time.time()

            new_time = time.time()
            sleep_time = target_cycle_time - (new_time - last_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
            elif sleep_time < -target_cycle_time * 5:
                log.warn('Obstacle avoid detection is getting late. It\'s late %s seconds.'
                         ' Use bigger cycle time.' % sleep_time)
            last_time += target_cycle_time
        pass


class ObstacleAvoidBehaviour(Behaviour, ControllerConfigWrapper):
    def __init__(self, controller):
        Behaviour.__init__(self)
        ControllerConfigWrapper.__init__(self, controller)

    def take_control(self):
        return self.get_config_value('OBSTACLE_AVOID') \
               and DISTANCE_SENSOR.value() < self.get_config_value('OBSTACLE_MIN_DISTANCE')

    def on_take_control(self):
        pass

    def on_loose_control(self):
        LEFT_MOTOR.stop()
        RIGHT_MOTOR.stop()
        SCANNER_MOTOR.run_to_abs_pos(speed_sp=SCANNER_MOTOR.max_speed / 5, position_sp=0)

    def handle_loop(self):
        target_cycle_time = 0.01
        min_reflect = self.controller.get_min_reflex()
        max_reflect = self.controller.get_max_reflex()
        target_reflect = self.get_config_value('TARGET_REFLECT')
        min_distance = self.get_config_value('OBSTACLE_MIN_DISTANCE')
        target_power = self.get_config_value('TARGET_POWER')
        target_speed = target_power / 100 * LEFT_MOTOR.max_speed
        side = self.get_config_value('OBSTACLE_AVOID_SIDE')
        obstacle_width = None  # TODO: to config
        obstacle_height = None  # TODO: to config

        course = 50 * side
        rel_deg_rotation = 0  # TODO: calculate from wheels diameter, offset and gear ratio
        LEFT_MOTOR.run_to_rel_pos(speed_sp=target_speed, position_sp=rel_deg_rotation / 100 * (50 + course))
        RIGHT_MOTOR.run_to_rel_pos(speed_sp=target_speed, position_sp=rel_deg_rotation / 100 * (50 - course))
        if obstacle_width is None or obstacle_height is None:
            SCANNER_MOTOR.run_to_abs_pos(speed_sp=SCANNER_MOTOR.max_speed / 5,
                                         position_sp=90 * ROBOT_MOTOR_SCANNER_GEAR_RATIO * side)

        while 'running' in LEFT_MOTOR.state or 'running' in RIGHT_MOTOR.state:
            time.sleep(target_cycle_time)

        for i in range(2):
            if obstacle_width is None or obstacle_height is None:
                LEFT_MOTOR.run_direct(duty_cycle_sp=target_power)
                RIGHT_MOTOR.run_direct(duty_cycle_sp=target_power)

                while DISTANCE_SENSOR.value() < min_distance:
                    time.sleep(target_cycle_time)

                LEFT_MOTOR.stop()
                RIGHT_MOTOR.stop()

                rel_deg_additional_run = 0  # TODO: calculate from wheels diameter, offset, gear ratio and robot length
                LEFT_MOTOR.run_to_rel_pos(speed_sp=target_speed, position_sp=rel_deg_additional_run)
                RIGHT_MOTOR.run_to_rel_pos(speed_sp=target_speed, position_sp=rel_deg_additional_run)
            else:
                rel_deg_additional_run = 0
                # TODO: calculate from wheels diameter, offset, gear ratio, robot length and obstacle width/height
                LEFT_MOTOR.run_to_rel_pos(speed_sp=target_speed, position_sp=rel_deg_additional_run)
                RIGHT_MOTOR.run_to_rel_pos(speed_sp=target_speed, position_sp=rel_deg_additional_run)
                pass

            while 'running' in LEFT_MOTOR.state or 'running' in RIGHT_MOTOR.state:
                time.sleep(target_cycle_time)

            LEFT_MOTOR.run_to_rel_pos(speed_sp=target_speed, position_sp=rel_deg_rotation / 100 * (50 - course))
            RIGHT_MOTOR.run_to_rel_pos(speed_sp=target_speed, position_sp=rel_deg_rotation / 100 * (50 + course))

            while 'running' in LEFT_MOTOR.state or 'running' in RIGHT_MOTOR.state:
                time.sleep(target_cycle_time)

        LEFT_MOTOR.run_direct(duty_cycle_sp=target_power)
        RIGHT_MOTOR.run_direct(duty_cycle_sp=target_power)
        SCANNER_MOTOR.run_to_abs_pos(speed_sp=SCANNER_MOTOR.max_speed / 5, position_sp=0)

        while 100 * (COLOR_SENSOR.value() - min_reflect) / (max_reflect - min_reflect) > target_reflect:
            time.sleep(target_cycle_time)

        LEFT_MOTOR.duty_cycle_sp(50 + course)
        RIGHT_MOTOR.duty_cycle_sp(50 - course)

        while 100 * (COLOR_SENSOR.value() - min_reflect) / (max_reflect - min_reflect) <= target_reflect:
            time.sleep(target_cycle_time)

        time.sleep(target_cycle_time)

        while 100 * (COLOR_SENSOR.value() - min_reflect) / (max_reflect - min_reflect) > target_reflect:
            time.sleep(target_cycle_time)

        LEFT_MOTOR.stop()
        RIGHT_MOTOR.stop()


class ObstacleDetectionBehaviour(MultiBehaviour, ControllerConfigWrapper):
    def __init__(self, controller):
        ControllerConfigWrapper.__init__(self, controller)
        MultiBehaviour.__init__(self, [
            CollisionAvoidBehaviour(controller),
            ObstacleAvoidBehaviour(controller)
        ])

    def take_control(self) -> bool:
        return HAS_DISTANCE_SENSOR and HAS_SCANNER_MOTOR \
               and (self.get_config_value('OBSTACLE_AVOID')
                    or self.get_config_value('COLLISION_AVOID')) \
               and DISTANCE_SENSOR.value() < self.get_config_value('OBSTACLE_MIN_DISTANCE')


class LineFollowBehaviour(Behaviour, ControllerConfigWrapper):
    def __init__(self, controller):
        Behaviour.__init__(self)
        ControllerConfigWrapper.__init__(self, controller)

        self._last_time = time.time()
        self._last_power = 0
        self.power_regulator = Regulator(const_p=0.5, const_i=0, const_d=0.5,
                                         getter_target=self._get_target_power)

        self.steer_regulator = Regulator(getter_p=lambda: self.get_config_value('REG_STEER_P'),
                                         getter_i=lambda: self.get_config_value('REG_STEER_I'),
                                         getter_d=lambda: self.get_config_value('REG_STEER_D'),
                                         getter_target=lambda: self.get_config_value('TARGET_REFLECT'))

    def reset_regulation(self):
        self.power_regulator.reset()
        self.steer_regulator.reset()

    def on_take_control(self):
        self._last_power = 0
        self.reset_regulation()
        LEFT_MOTOR.run_direct(duty_cycle_sp=0)
        RIGHT_MOTOR.run_direct(duty_cycle_sp=0)
        self._last_time = time.time()

    def on_loose_control(self):
        LEFT_MOTOR.stop()
        RIGHT_MOTOR.stop()
        pass

    def take_control(self) -> bool:
        return True

    def _get_target_power(self):
        if self.get_config_value('PAUSE_POWER') or self.controller.stop:
            return 0
        return self.get_config_value('TARGET_POWER')

    def _next_power(self):
        if self.get_config_value('REGULATE_TARGET_POWER_CHANGE'):
            self._last_power += self.power_regulator.regulate(self._last_power) / 10
        else:
            self._last_power = self._get_target_power()
        return self._last_power

    def handle_loop(self):
        min_reflect = self.controller.get_min_reflex()
        max_reflect = self.controller.get_max_reflex()
        line_side = self.get_config_value('LINE_SIDE')
        target_power = self._next_power()
        target_cycle_time = self.get_config_value('TARGET_CYCLE_TIME')

        read_val = COLOR_SENSOR.value()
        read_percent = 100 * (read_val - min_reflect) / (max_reflect - min_reflect)
        course = min(100, max(-100, self.steer_regulator.regulate(read_percent) * line_side)) / 2

        if self.get_config_value('SHARP_TURN_DETECT') and self.steer_regulator.last_derivative > 25:
            # TODO: test and add to config
            side = self.get_config_value('SHARP_TURN_ROTATE_SIDE')
            target_reflect = self.get_config_value('TARGET_REFLECT')
            course = 50 * side
            LEFT_MOTOR.duty_cycle_sp = target_power / 100 * (50 + course)
            RIGHT_MOTOR.duty_cycle_sp = target_power / 100 * (50 - course)

            while 100 * (COLOR_SENSOR.value() - min_reflect) / (max_reflect - min_reflect) <= target_reflect:
                time.sleep(target_cycle_time)

            time.sleep(target_cycle_time)

            while 100 * (COLOR_SENSOR.value() - min_reflect) / (max_reflect - min_reflect) > target_reflect:
                time.sleep(target_cycle_time)

            self.reset_regulation()
            self._last_time = time.time()
            return

        if self.get_config_value('STOP_ON_LINE_END') and self.steer_regulator.last_derivative < -25:
            # TODO: test and add to config
            self.controller.force_loose_control()
            self.controller.request_exit()

        power_left = target_power + course
        power_right = target_power - course
        diff = 0
        if power_left > 100:
            diff += power_left - 100
        elif power_left < 0:
            diff -= power_left
        if power_right > 100:
            diff -= power_right - 100
        elif power_right < 0:
            diff += power_right
        power_left -= diff
        power_right += diff

        LEFT_MOTOR.duty_cycle_sp = int(power_left)
        RIGHT_MOTOR.duty_cycle_sp = int(power_right)

        new_time = time.time()
        sleep_time = target_cycle_time - (new_time - self._last_time)
        if sleep_time > 0:
            time.sleep(sleep_time)
        elif sleep_time < -target_cycle_time * 5:
            log.warn('Regulation is getting late. It\'s late %s seconds. Use bigger cycle time.' % sleep_time)
        self._last_time += target_cycle_time


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
    def _scan_reflect(reflect):
        while 'running' in LEFT_MOTOR.state or 'running' in RIGHT_MOTOR.state:
            read = COLOR_SENSOR.value()
            reflect[0] = min(reflect[0], read)
            reflect[1] = max(reflect[1], read)

    def on_start(self):
        reflect = [None, None]
        if self.get_config_value('DETECT_REFLECT'):
            reflect = [100, 0]

            LEFT_MOTOR.run_to_rel_pos(speed_sp=200, position_sp=150)
            RIGHT_MOTOR.run_to_rel_pos(speed_sp=200, position_sp=-150)
            self._scan_reflect(reflect)

            LEFT_MOTOR.run_to_rel_pos(position_sp=-300)
            RIGHT_MOTOR.run_to_rel_pos(position_sp=300)
            self._scan_reflect(reflect)

            LEFT_MOTOR.run_to_rel_pos(position_sp=150)
            RIGHT_MOTOR.run_to_rel_pos(position_sp=-150)
            self._scan_reflect(reflect)

            LEFT_MOTOR.stop()
            RIGHT_MOTOR.stop()

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

    def execute(self, config=None) -> RobotProgramController:
        if not HAS_WHEELS or not HAS_COLOR_SENSOR:
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
