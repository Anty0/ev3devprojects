class Position2D:
    def __init__(self, x: float, y: float, angle_deg: float):
        self._x = x
        self._y = y
        self._angle_deg = angle_deg

    def get_x(self):
        return self._x

    def get_y(self):
        return self._y

    def get_angle_deg(self):
        return self._angle_deg

    def get_angle_rad(self):
        raise NotImplementedError

    def offset_by(self, offset_position):
        return Position2D(self.get_x() + offset_position.get_x(),
                          self.get_y() + offset_position.get_y(),
                          self.get_angle_deg() + offset_position.get_angle_deg())

        # TODO: add some basic calculations support methods


class Position3D:
    def __init__(self, x: float, y: float, z: float, angle_x_deg: float, angle_y_deg: float):
        self._x = x
        self._y = y
        self._z = z
        self._angle_x_deg = angle_x_deg
        self._angle_y_deg = angle_y_deg

    def get_x(self):
        return self._x

    def get_y(self):
        return self._y

    def get_z(self):
        return self._z

    def get_angle_x_deg(self):
        return self._angle_x_deg

    def get_angle_y_deg(self):
        return self._angle_y_deg

    def get_angle_rad(self):
        raise NotImplementedError

    def offset_by(self, offset_position):
        return Position3D(self.get_x() + offset_position.get_x(),
                          self.get_y() + offset_position.get_y(),
                          self.get_z() + offset_position.get_z(),
                          self.get_angle_x_deg() + offset_position.get_angle_x_deg(),
                          self.get_angle_y_deg() + offset_position.get_angle_y_deg())
