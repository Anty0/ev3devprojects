from ev3dev.auto import TouchSensor, ColorSensor, UltrasonicSensor

from .controller import Controller
from .interface import DeviceInterface, MotorInterface, SensorInterface, TouchSensorInterface, ColorSensorInterface, \
    UltrasonicSensorInterface


class DeviceDriver:
    def __init__(self, controller: Controller, device_interface: DeviceInterface):
        self._controller = controller
        self._driver_name = device_interface.driver_name
        self._position = device_interface.position

    @property
    def driver_name(self):
        return self._driver_name


class MotorDriver(DeviceDriver):
    def __init__(self, controller: Controller, device_interface: MotorInterface):
        DeviceDriver.__init__(self, controller, device_interface)
        self._address = device_interface.address
        self._command = ''
        self._commands = device_interface.commands
        self._count_per_rot = device_interface.count_per_rot  # TODO: better simulation of unknown (None) val
        self._count_per_m = device_interface.count_per_m  # TODO: better simulation of unknown (None) val
        self._duty_cycle = 0
        self._duty_cycle_sp = 0
        self._full_travel_count = device_interface.full_travel_count
        self._polarity = device_interface.polarity
        self._position = device_interface.position
        self._position_sp = 0
        self._max_speed = device_interface.max_speed
        self._speed = 0
        self._speed_sp = 0
        self._ramp_up_sp = device_interface.ramp_up_sp
        self._ramp_down_sp = device_interface.ramp_down_sp
        self._stop_action = device_interface.stop_action
        self._stop_actions = device_interface.stop_actions
        self._time_sp = 0

    @property
    def address(self):
        return str(self._address)

    @property
    def command(self):
        raise Exception("command is a write-only property!")

    @command.setter
    def command(self, value):
        if value not in self._commands:
            raise Exception()
        pass  # TODO: implement

    @property
    def commands(self):
        commands_len = len(self._commands)
        if commands_len == 0:
            return ''
        value = self._commands[0]
        for i in range(1, commands_len):
            value += ' ' + self._commands[i]
        return value

    @property
    def count_per_rot(self):
        return str(self._count_per_rot)

    @property
    def count_per_m(self):
        return str(self._count_per_m)

    @property
    def duty_cycle(self):
        return str(self._duty_cycle)

    @property
    def duty_cycle_sp(self):
        return str(self._duty_cycle_sp)

    @duty_cycle_sp.setter
    def duty_cycle_sp(self, value):
        self._duty_cycle_sp = int(value)

    @property
    def full_travel_count(self):
        return str(self._full_travel_count)

    @property
    def polarity(self):
        return self._polarity

    @polarity.setter
    def polarity(self, value):
        if value not in ('normal', 'inversed'):
            raise Exception()
        self._polarity = value

    @property
    def position(self):
        return str(self._position)

    @position.setter
    def position(self, value):
        self._position = int(value)

    @property
    def position_sp(self):
        return str(self._position_sp)

    @position_sp.setter
    def position_sp(self, value):
        self._position_sp = int(value)

    @property
    def max_speed(self):
        return str(self._max_speed)

    @property
    def speed(self):
        return str(self._speed)

    @property
    def speed_sp(self):
        return str(self._speed_sp)

    @speed_sp.setter
    def speed_sp(self, value):
        self._speed_sp = int(value)

    @property
    def ramp_up_sp(self):
        return str(self._ramp_up_sp)

    @ramp_up_sp.setter
    def ramp_up_sp(self, value):
        self._ramp_up_sp = int(value)

    @property
    def ramp_down_sp(self):
        return str(self._ramp_down_sp)

    @ramp_down_sp.setter
    def ramp_down_sp(self, value):
        self._ramp_down_sp = int(value)

    @property
    def state(self):
        return ''  # TODO: implement

    @property
    def stop_action(self):
        return self._stop_action

    @stop_action.setter
    def stop_action(self, value):
        if value not in self._stop_actions:
            raise Exception()
        self._stop_action = value

    @property
    def stop_actions(self):
        stop_actions_len = len(self._stop_actions)
        if stop_actions_len == 0:
            return ''
        value = self._stop_actions[0]
        for i in range(1, stop_actions_len):
            value += ' ' + self._stop_actions[i]
        return value

    @property
    def time_sp(self):
        return str(int(self._time_sp * 1000))

    @time_sp.setter
    def time_sp(self, value):
        self._time_sp = int(value) / 1000


class SensorDriver(DeviceDriver):
    def __init__(self, controller: Controller, device_interface: SensorInterface):
        DeviceDriver.__init__(self, controller, device_interface)
        self._address = device_interface.address
        self._commands = []
        self._mode = device_interface.mode
        self._modes = []
        self._decimals = {}
        self._num_values = {}
        self._units = {}

    @property
    def address(self):
        return str(self._address)

    @property
    def command(self):
        raise Exception("command is a write-only property!")

    @command.setter
    def command(self, value):
        if self._commands is None or value not in self._commands:
            raise Exception()
        self._do_command(value)

    def _do_command(self, command):
        pass

    @property
    def commands(self):
        if self._commands is None:
            raise Exception()

        commands_len = len(self._commands)
        if commands_len == 0:
            return ''
        value = self._commands[0]
        for i in range(1, commands_len):
            value += ' ' + self._commands[i]
        return value

    @property
    def decimals(self):
        return str(self._decimals[self._mode])

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        if self._mode == value:
            return
        if value not in self._modes:
            raise Exception()
        self._on_mode_change(self._mode, value)
        self._mode = value

    def _on_mode_change(self, old_mode, new_mode):
        pass

    @property
    def modes(self):
        modes_len = len(self._modes)
        if modes_len == 0:
            return ''
        value = self._modes[0]
        for i in range(1, modes_len):
            value += ' ' + self._commands[i]
        return value

    @property
    def num_values(self):
        return str(self._num_values[self._mode])

    @property
    def units(self):
        return str(self._units[self._mode])  # TODO: better simulation of none units

    @property
    def bin_data_format(self):
        raise NotImplementedError()

    @property
    def bin_data(self):
        raise NotImplementedError()


class TouchSensorDriver(SensorDriver):
    def __init__(self, controller: Controller, device_interface: TouchSensorInterface):
        SensorDriver.__init__(self, controller, device_interface)
        self._commands = []  # TODO: extract from robot
        self._modes = [TouchSensor.MODE_TOUCH]
        self._decimals = {TouchSensor.MODE_TOUCH: 0}
        self._num_values = {TouchSensor.MODE_TOUCH: 1}
        self._units = {TouchSensor.MODE_TOUCH: None}

    @property
    def value0(self):
        if self._mode == TouchSensor.MODE_TOUCH:
            return str(int(self._controller.is_pos_in_wall(self._position)))

        raise Exception()


class ColorSensorDriver(SensorDriver):
    def __init__(self, controller: Controller, device_interface: ColorSensorInterface):
        SensorDriver.__init__(self, controller, device_interface)
        self._commands = []  # TODO: extract from robot
        self._modes = [ColorSensor.MODE_COL_REFLECT, ColorSensor.MODE_COL_AMBIENT, ColorSensor.MODE_COL_COLOR,
                       ColorSensor.MODE_REF_RAW, ColorSensor.MODE_RGB_RAW]
        self._decimals = {
            ColorSensor.MODE_COL_REFLECT: 0,
            ColorSensor.MODE_COL_AMBIENT: 0,
            ColorSensor.MODE_COL_COLOR: 0,
            ColorSensor.MODE_REF_RAW: 0,
            ColorSensor.MODE_RGB_RAW: 0
        }
        self._num_values = {
            ColorSensor.MODE_COL_REFLECT: 1,
            ColorSensor.MODE_COL_AMBIENT: 1,
            ColorSensor.MODE_COL_COLOR: 1,
            ColorSensor.MODE_REF_RAW: 2,
            ColorSensor.MODE_RGB_RAW: 3
        }
        self._units = {
            ColorSensor.MODE_COL_REFLECT: 'pct',
            ColorSensor.MODE_COL_AMBIENT: 'pct',
            ColorSensor.MODE_COL_COLOR: 'pct',
            ColorSensor.MODE_REF_RAW: None,
            ColorSensor.MODE_RGB_RAW: None
        }

    @property
    def value0(self):
        if self._mode == ColorSensor.MODE_COL_REFLECT:
            return str(int(self._controller.get_reflect_on_pos(self._position)))
        if self._mode == ColorSensor.MODE_COL_AMBIENT:
            return str(int(self._controller.get_light_on_pos(self._position)))
        if self._mode == ColorSensor.MODE_COL_COLOR:
            return str(int(0))  # TODO: implement
        if self._mode == ColorSensor.MODE_REF_RAW:
            return str(int(0))  # TODO: implement
        if self._mode == ColorSensor.MODE_RGB_RAW:
            return str(int(self._controller.get_color_rgb_on_pos(self._position)[0]))

        raise Exception()

    @property
    def value1(self):
        if self._mode == ColorSensor.MODE_REF_RAW:
            return str(int(0))  # TODO: implement
        if self._mode == ColorSensor.MODE_RGB_RAW:
            return str(int(self._controller.get_color_rgb_on_pos(self._position)[1]))

        raise Exception()

    @property
    def value2(self):
        if self._mode == ColorSensor.MODE_RGB_RAW:
            return str(int(self._controller.get_color_rgb_on_pos(self._position)[2]))

        raise Exception()


class UltrasonicSensorDriver(SensorDriver):
    def __init__(self, controller: Controller, device_interface: UltrasonicSensorInterface):
        SensorDriver.__init__(self, controller, device_interface)
        ev3 = self._driver_name == 'lego-ev3-us'
        self._commands = []  # TODO: extract from robot
        self._modes = [UltrasonicSensor.MODE_US_DIST_CM, UltrasonicSensor.MODE_US_DIST_IN,
                       UltrasonicSensor.MODE_US_LISTEN, UltrasonicSensor.MODE_US_SI_CM, UltrasonicSensor.MODE_US_SI_IN]
        self._decimals = {
            UltrasonicSensor.MODE_US_DIST_CM: 1 if ev3 else 0,
            UltrasonicSensor.MODE_US_DIST_IN: 1,
            UltrasonicSensor.MODE_US_LISTEN: 0,
            UltrasonicSensor.MODE_US_SI_CM: 1 if ev3 else 0,
            UltrasonicSensor.MODE_US_SI_IN: 1
        }
        self._num_values = {
            UltrasonicSensor.MODE_US_DIST_CM: 1,
            UltrasonicSensor.MODE_US_DIST_IN: 1,
            UltrasonicSensor.MODE_US_LISTEN: 1,
            UltrasonicSensor.MODE_US_SI_CM: 1,
            UltrasonicSensor.MODE_US_SI_IN: 1
        }
        self._units = {
            UltrasonicSensor.MODE_US_DIST_CM: 'cm',
            UltrasonicSensor.MODE_US_DIST_IN: 'in',
            UltrasonicSensor.MODE_US_LISTEN: None,
            UltrasonicSensor.MODE_US_SI_CM: 'cm',
            UltrasonicSensor.MODE_US_SI_IN: 'in'
        }
        self._tmp_value = 0

    def _on_mode_change(self, old_mode, new_mode):
        if new_mode == UltrasonicSensor.MODE_US_SI_CM or new_mode == UltrasonicSensor.MODE_US_SI_IN:
            self._tmp_value = self._controller.get_distance_on_pos(self._position)
        else:
            self._tmp_value = 0

    @property
    def value0(self):
        ev3 = self._driver_name == 'lego-ev3-us'
        if self._mode == UltrasonicSensor.MODE_US_DIST_CM:
            return str(
                int(self._controller.get_distance_on_pos(self._position) * (10 if ev3 else 1)))  # map must be in cm
        if self._mode == UltrasonicSensor.MODE_US_DIST_IN:
            return str(int(self._controller.get_distance_on_pos(self._position) * 10))  # map must be in inch
        if self._mode == UltrasonicSensor.MODE_US_LISTEN:
            return str(int(0))  # TODO: add support
        if self._mode == UltrasonicSensor.MODE_US_SI_CM:
            return str(int(self._tmp_value * (10 if ev3 else 1)))  # map must be in cm
        if self._mode == UltrasonicSensor.MODE_US_SI_IN:
            return str(int(self._tmp_value * 10))  # map must be in inch

        raise Exception()


class GyroSensorDriver(SensorDriver):
    pass  # TODO: complete implementations fo drivers


DRIVERS = {
    'unknown': DeviceDriver,

    'lego-ev3-l-motor': MotorDriver,
    'lego-nxt-motor': MotorDriver,
    'lego-ev3-m-motor': MotorDriver,

    'lego-sensor': SensorDriver,
    'lego-ev3-touch': TouchSensorDriver,
    'lego-nxt-touch': TouchSensorDriver,
    'lego-ev3-color': None,  # TODO: implement
    'lego-ev3-us': None,  # TODO: implement
    'lego-nxt-us': None,  # TODO: implement
    'lego-ev3-gyro': None,  # TODO: implement
    'lego-ev3-ir': None,  # TODO: implement
    'lego-nxt-sound': None,  # TODO: implement
    'lego-nxt-light': None,  # TODO: implement
    'lego-ev3-leds': None  # TODO: implement
}
