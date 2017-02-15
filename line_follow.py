#!/usr/bin/env python3

import config as _config
from behaviour import *
from hardware import *
from regulator import *
from robot_program import *


class CollisionAvoidBehaviour(Behaviour, ControllerConfigWrapper):
    def __init__(self, controller):
        Behaviour.__init__(self)
        ControllerConfigWrapper.__init__(self, controller)

    def take_control(self):
        return self.get_config_value('LINE_FOLLOWER_COLLISION_AVOID')  # and TODO: implement

    def handle_loop(self):
        pass  # TODO: implement


class ObstacleAvoidBehaviour(Behaviour, ControllerConfigWrapper):
    def __init__(self, controller):
        Behaviour.__init__(self)
        ControllerConfigWrapper.__init__(self, controller)

    def take_control(self):
        return self.get_config_value('LINE_FOLLOWER_OBSTACLE_AVOID')  # and TODO: implement

    def handle_loop(self):
        pass  # TODO: implement


class ObstacleDetectionBehaviour(MultiBehaviour, ControllerConfigWrapper):
    def __init__(self, controller):
        ControllerConfigWrapper.__init__(self, controller)
        MultiBehaviour.__init__(self, [
            CollisionAvoidBehaviour(controller),
            ObstacleAvoidBehaviour(controller)
        ])

    def take_control(self) -> bool:
        return (self.get_config_value('LINE_FOLLOWER_OBSTACLE_AVOID')
                or self.get_config_value('LINE_FOLLOWER_COLLISION_AVOID')) \
               and DISTANCE_SENSOR.value() < self.get_config_value('OBSTACLE_MIN_DISTANCE')


class LineFollowBehaviour(Behaviour, ControllerConfigWrapper):
    def __init__(self, controller):
        Behaviour.__init__(self)
        ControllerConfigWrapper.__init__(self, controller)

        self.last_time = time.time()
        self.last_power = 0
        self.power_regulator = Regulator(const_p=0.05, const_d=0.05, const_i=0,
                                         getter_target=lambda: self.get_config_value('TARGET_POWER')
                                         if not self.get_config_value('PAUSE_POWER') and not controller.stop else 0)

        self.steer_regulator = Regulator(getter_p=lambda: self.get_config_value('REG_STEER_P'),
                                         getter_d=lambda: self.get_config_value('REG_STEER_D'),
                                         getter_i=lambda: self.get_config_value('REG_STEER_I'),
                                         getter_target=lambda: self.get_config_value('TARGET_REFLECT'))

    def reset_regulation(self):
        self.power_regulator.reset()
        self.steer_regulator.reset()

    def on_take_control(self):
        self.last_power = 0
        self.power_regulator.reset()
        self.steer_regulator.reset()
        LEFT_MOTOR.run_direct(duty_cycle_sp=0)
        RIGHT_MOTOR.run_direct(duty_cycle_sp=0)
        self.last_time = time.time()

    def on_loose_control(self):
        LEFT_MOTOR.stop()
        RIGHT_MOTOR.stop()
        pass

    def _next_power(self):
        if self.get_config_value('REGULATE_TARGET_POWER_CHANGE'):
            self.last_power += self.power_regulator.regulate(self.last_power)
        else:
            self.last_power = self.power_regulator.get_target()
        return self.last_power

    def _get_min_reflex(self):
        result = self.get_private_config_value('MIN_REFLECT')
        return result if result is not None else self.get_config_value('MIN_REFLECT')

    def _get_max_reflex(self):
        result = self.get_private_config_value('MAX_REFLECT')
        return result if result is not None else self.get_config_value('MAX_REFLECT')

    def take_control(self) -> bool:
        return True

    def handle_loop(self):
        min_reflect = self._get_min_reflex()
        max_reflect = self._get_max_reflex()
        line_side = self.get_config_value('LINE_SIDE')
        target_power = self._next_power()
        target_cycle_time = self.get_config_value('TARGET_CYCLE_TIME')

        read_val = COLOR_SENSOR.value()
        read_percent = 100 * (read_val - min_reflect) / (max_reflect - min_reflect)
        course = min(100, max(-100, self.steer_regulator.regulate(read_percent) * line_side)) / 2

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
        sleep_time = target_cycle_time - (new_time - self.last_time)
        if sleep_time > 0:
            time.sleep(sleep_time)
        elif sleep_time < -target_cycle_time * 5:
            log.warn('Regulation is getting late. It\'s late %s seconds. Use bigger cycle time.' % sleep_time)
        self.last_time += target_cycle_time
        pass


class LineFollowController(SimpleRobotProgramController, BehaviourController):
    def __init__(self, robot_program, config=None):
        SimpleRobotProgramController.__init__(self, robot_program, config)
        BehaviourController.__init__(self, robot_program, [
            ObstacleDetectionBehaviour(self),
            LineFollowBehaviour(self)
        ])

    @staticmethod
    def _scan_reflect(reflect):
        while 'running' in LEFT_MOTOR.state or 'running' in RIGHT_MOTOR.state:
            read = COLOR_SENSOR.value()
            reflect[0] = min(reflect[0], read)
            reflect[1] = max(reflect[1], read)

    def on_start(self):
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
        else:
            self.set_private_config_value('MIN_REFLECT', None)
            self.set_private_config_value('MAX_REFLECT', None)
        pass

    def on_exit(self):
        reset_hardware()

    def stop_loop(self):
        return super().stop_loop() and (not isinstance(self.last_behaviour, LineFollowBehaviour)
                                        or self.last_behaviour.last_power < 5)

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
        return LineFollowController(config)


def run():
    controller = LineFollowRobotProgram().execute()
    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass

    controller.stop()
    controller.wait_to_exit()


if __name__ == '__main__':
    run()
