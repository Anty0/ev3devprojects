import math
from threading import Thread

from utils.position import Position2D


class RobotInfo:
    pass


class Map:
    pass


class Controller:
    def __init__(self, robot_info: RobotInfo, surrounding_map: Map, start_position: Position2D = None):
        self.robot_info = robot_info
        self._map = surrounding_map
        self._position = start_position if start_position is not None else Position2D(0, 0, 0)
        self._wheels = []
        self._odometry = None

    def _register_wheel(self, wheel):
        self._wheels.append(wheel)

    def register_wheel(self, wheel):
        self._register_wheel(wheel)
        self._start_odometry()

    def register_wheels(self, wheels: list):
        for wheel in wheels:
            self._register_wheel(wheel)
        self._start_odometry()

    def _start_odometry(self):
        if self._odometry is None:
            self._odometry = Thread(target=self._run_odometry, daemon=True)
            self._odometry.start()

    def _run_odometry(self):
        while True:
            pass
        pass

    def get_map(self):
        return self._map

    def set_actual_pos(self, position):
        self._position = position

    def get_actual_pos(self):
        return self._position

    def get_color_rgb_on_pos(self, offset_position=None):
        return [0, 0, 0]  # TODO: implement

    def get_reflect_on_pos(self, offset_position=None):
        return 50  # TODO: implement

    def get_light_on_pos(self, offset_position=None):
        return 50  # TODO: implement

    def get_distance_on_pos(self, offset_position=None):
        return math.inf  # TODO: implement

    def get_beacon_pos_offset(self, offset_position=None):
        return None  # TODO: implement

    def is_pos_in_wall(self, offset_position=None):
        return False  # TODO: implement

    def get_noise_on_pos(self, offset_position=None, use_a_weighting=False):
        return 0  # TODO: implement
