from ev3dev.auto import *


class Position:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


class Wheel:
    def __init__(self, motor: Motor, gear_ratio: float, diameter: float,
                 width: float, position: Position):
        self.motor = motor
        self.gear_ratio = gear_ratio
        self.diameter = diameter
        self.width = width
        self.position = position


class Pilot:
    def __init__(self, wheels: array):
        self.wheels = wheels
