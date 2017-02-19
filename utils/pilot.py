from ev3dev.auto import *


class Wheel:  # TODO: implement
    def __init__(self, motor: Motor, gear_ratio: float, diameter: float,
                 width: float, offset_x: float):
        self.motor = motor
        self.gear_ratio = gear_ratio
        self.motor_tacho_ratio = motor.count_per_rot / 360
        self.wheel_ratio = self.gear_ratio * self.motor_tacho_ratio
        self.diameter = diameter
        self.width = width
        self.offset_x = offset_x


class Pilot:
    def __init__(self, wheels: array):
        self.wheels = wheels

    def reset(self):
        for wheel in self.wheels:
            wheel.motor.reset()

    def stop(self):
        for wheel in self.wheels:
            wheel.motor.stop()

    def run_forever(self, speeds=None, max_duty_cycle=100, ramp_up=0, ramp_down=0):
        pass

    def run_to_abs_pos(self, positions, max_speed=None, max_duty_cycle=100, ramp_up=0, ramp_down=0):
        pass

    def run_to_rel_pos(self, positions, max_speed=None, max_duty_cycle=100, ramp_up=0, ramp_down=0):
        pass

    def run_timed(self, time_len, speeds=None, max_duty_cycle=100, ramp_up=0, ramp_down=0):
        pass

    def run_drive_forever(self, course, max_speed=None, max_duty_cycle=100, ramp_up=0, ramp_down=0):
        pass

    def run_drive_to_angle(self, angle, course, max_speed=None, max_duty_cycle=100, ramp_up=0, ramp_down=0):
        pass

    def run_drive_to_distance(self, distance, course, max_speed=None, max_duty_cycle=100, ramp_up=0, ramp_down=0):
        pass

    def run_drive_timed(self, time_len, course, max_speed=None, max_duty_cycle=100, ramp_up=0, ramp_down=0):
        pass

    def run_direct(self):
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
        pass
