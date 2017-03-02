import math

from ev3dev.auto import Motor

from .position import Position2D


class Wheel:
    def __init__(self, motor: Motor, gear_ratio: float, diameter: float,
                 width: float, offset: float):
        self.motor = motor
        self.diameter = diameter
        self.width = width

        self.offset = offset
        self.offset_position = Position2D(offset, 0, 0)

        self.gear_ratio = gear_ratio
        self.motor_tacho_ratio = motor.count_per_rot / 360 if motor.connected else 1
        self.total_ratio = self.gear_ratio * self.motor_tacho_ratio
        self.unit_ratio = 360 / (math.pi * self.diameter)
