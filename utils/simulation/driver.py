import math
import time
from threading import Thread, Event

from ev3dev.auto import TouchSensor, ColorSensor, UltrasonicSensor, GyroSensor, InfraredSensor, SoundSensor, LightSensor

from utils.utils import wait_to_cycle_time
from .controller import Controller
from .interface import DeviceInterface, MotorInterface, SensorInterface, TouchSensorInterface, ColorSensorInterface, \
    UltrasonicSensorInterface, GyroSensorInterface, InfraredSensorInterface, SoundSensorInterface, \
    LightSensorInterface, LedInterface


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
        self._command_applied_event = Event()
        self._last_command = ''
        self._command = 'stop'
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
        self._state = []
        self._stop_action = device_interface.stop_action
        self._stop_actions = device_interface.stop_actions
        self._time_sp = 0

        self._commands_handler_thread = None

    def _commands_handler_loop(self):
        cycle_time = 0.05
        self._last_command = ''
        command_args = {}
        last_time = time.time()
        while True:
            actual_command = self._command
            if self._last_command != actual_command:
                if actual_command == 'run-forever':
                    command_args = {'speed': self._speed_sp}
                elif actual_command == 'run-to-abs-pos':
                    command_args = {
                        'speed': self._speed_sp,
                        'position': self._position_sp,
                        'stop_action': self._stop_action
                    }
                elif actual_command == 'run-to-rel-pos':
                    command_args = {
                        'speed': self._speed_sp,
                        'position': self._position + self._position_sp,
                        'stop_action': self._stop_action
                    }
                elif actual_command == 'run-timed':
                    command_args = {
                        'speed': self._speed_sp,
                        'start_time': time.time(),
                        'time': self._time_sp / 1000,
                        'stop_action': self._stop_action
                    }
                elif actual_command == 'run-direct':
                    command_args = {}
                elif actual_command == 'stop':
                    command_args = {'stop_action': self._stop_action}
                elif actual_command == 'reset':
                    command_args = {}
                else:
                    command_args = {}
                self._last_command = actual_command

            self._command_applied_event.set()
            self._command_applied_event.clear()

            if actual_command == 'run-forever':
                speed = command_args['speed']
                self._position += speed * cycle_time
                self._speed = speed
                self._duty_cycle = speed / abs(speed) * 100 if speed != 0 else 0
                self._state = ['running']
            elif actual_command == 'run-to-abs-pos' or actual_command == 'run-to-rel-pos':
                speed = command_args['speed']
                actual_pos = self._position
                target_pos = command_args['position']
                diff = target_pos - actual_pos
                way = diff / abs(diff) if diff != 0 else 0
                change = abs(speed * cycle_time) * way
                if abs(diff) <= abs(change):
                    self._position = target_pos
                    self._command = self._last_command = 'stop'
                else:
                    self._position += change
                self._speed = abs(speed) * way
                self._duty_cycle = way * 100
                self._state = ['running']
            elif actual_command == 'run-timed':
                speed = command_args['speed']
                self._position += speed * cycle_time
                self._speed = speed
                self._duty_cycle = speed / abs(speed) * 100 if speed != 0 else 0
                self._state = ['running']

                if time.time() - command_args['start_time'] >= command_args['time']:
                    self._command = self._last_command = 'stop'
            elif actual_command == 'run-direct':
                duty_cycle = self._duty_cycle_sp
                speed = (duty_cycle - (8 * (duty_cycle / abs(duty_cycle)))) * 10 if abs(duty_cycle) > 8 else 0
                self._position += speed * cycle_time
                self._speed = speed
                self._duty_cycle = duty_cycle
                self._state = ['running']
                pass
            elif actual_command == 'stop':
                self._speed = 0
                self._duty_cycle = 0
                if command_args['stop_action'] == 'hold':
                    self._state = ['holding']
                else:
                    self._state = []
                pass
            elif actual_command == 'reset':
                self._last_command = ''
                self._command = 'stop'
                self._duty_cycle = 0
                self._duty_cycle_sp = 0
                self._polarity = 'normal'
                self._position = 0
                self._position_sp = 0
                self._speed = 0
                self._speed_sp = 0
                self._ramp_up_sp = 0
                self._ramp_down_sp = 0
                self._state = []
                self._stop_action = 'coast'
                self._time_sp = 0

            last_time = wait_to_cycle_time(__name__, last_time, cycle_time)

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

        if self._commands_handler_thread is None:
            self._commands_handler_thread = Thread(target=self._commands_handler_loop, daemon=True)
            self._commands_handler_thread.start()

        while self._last_command != self._command:
            self._command_applied_event.wait()

        if self._command == value:
            self._command = ''

            while self._last_command != self._command:
                self._command_applied_event.wait()

        self._command = value

        while self._last_command != self._command:
            self._command_applied_event.wait()

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
        return str(int(self._duty_cycle))

    @property
    def duty_cycle_sp(self):
        return str(int(self._duty_cycle_sp))

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
        return str(int(self._position))

    @position.setter
    def position(self, value):
        self._position = int(value)

    @property
    def position_sp(self):
        return str(int(self._position_sp))

    @position_sp.setter
    def position_sp(self, value):
        self._position_sp = int(value)

    @property
    def max_speed(self):
        return str(self._max_speed)

    @property
    def speed(self):
        return str(int(self._speed))

    @property
    def speed_sp(self):
        return str(int(self._speed_sp))

    @speed_sp.setter
    def speed_sp(self, value):
        if abs(int(value)) > self._max_speed:
            raise Exception()
        self._speed_sp = int(value)

    @property
    def ramp_up_sp(self):
        return str(int(self._ramp_up_sp))

    @ramp_up_sp.setter
    def ramp_up_sp(self, value):
        self._ramp_up_sp = int(value)

    @property
    def ramp_down_sp(self):
        return str(int(self._ramp_down_sp))

    @ramp_down_sp.setter
    def ramp_down_sp(self, value):
        self._ramp_down_sp = int(value)

    @property
    def state(self):
        state = self._state.copy()
        state_len = len(state)
        if state_len == 0:
            return ''
        value = state[0]
        for i in range(1, state_len):
            value += ' ' + state[i]
        return value

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
        stop_actions = self._stop_actions.copy()
        stop_actions_len = len(stop_actions)
        if stop_actions_len == 0:
            return ''
        value = stop_actions[0]
        for i in range(1, stop_actions_len):
            value += ' ' + stop_actions[i]
        return value

    @property
    def time_sp(self):
        return str(int(self._time_sp))

    @time_sp.setter
    def time_sp(self, value):
        self._time_sp = int(value)


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
        self._commands = []
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
        self._commands = []
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
        self._on_mode_change(None, self._mode)

    def _on_mode_change(self, old_mode, new_mode):
        if new_mode == UltrasonicSensor.MODE_US_SI_CM or new_mode == UltrasonicSensor.MODE_US_SI_IN:
            self._tmp_value = self._controller.get_distance_on_pos(self._position)
        else:
            self._tmp_value = 0

    @property
    def value0(self):  # TODO: crop distance values
        ev3 = self._driver_name == 'lego-ev3-us'
        if self._mode == UltrasonicSensor.MODE_US_DIST_CM:
            distance = self._controller.get_distance_on_pos(self._position)
            return str(int((distance * (10 if ev3 else 1)) if math.isfinite(distance) and
                                                              distance < (2550 if ev3 else 255) else (
                2550 if ev3 else 255)))  # map must be in cm
        if self._mode == UltrasonicSensor.MODE_US_DIST_IN:
            distance = self._controller.get_distance_on_pos(self._position)
            return str(int((distance * 10) if math.isfinite(distance) and
                                              distance < 1003 else 1003))  # map must be in inch
        if self._mode == UltrasonicSensor.MODE_US_LISTEN:
            return str(int(0))  # TODO: add support
        if self._mode == UltrasonicSensor.MODE_US_SI_CM:
            return str(int((self._tmp_value * (10 if ev3 else 1)) if math.isfinite(self._tmp_value) and
                                                                     self._tmp_value < (2550 if ev3 else 255) else (
                2550 if ev3 else 255)))  # map must be in cm
        if self._mode == UltrasonicSensor.MODE_US_SI_IN:
            return str(int((self._tmp_value * 10) if math.isfinite(self._tmp_value) and
                                                     self._tmp_value < 1003 else 1003))  # map must be in inch
        raise Exception()


class GyroSensorDriver(SensorDriver):
    def __init__(self, controller: Controller, device_interface: GyroSensorInterface):
        SensorDriver.__init__(self, controller, device_interface)
        self._commands = []
        self._modes = [GyroSensor.MODE_GYRO_ANG, GyroSensor.MODE_GYRO_RATE, GyroSensor.MODE_GYRO_FAS,
                       GyroSensor.MODE_GYRO_G_A, GyroSensor.MODE_GYRO_CAL]
        self._decimals = {
            GyroSensor.MODE_GYRO_ANG: 0,
            GyroSensor.MODE_GYRO_RATE: 0,
            GyroSensor.MODE_GYRO_FAS: 0,
            GyroSensor.MODE_GYRO_G_A: 0,
            GyroSensor.MODE_GYRO_CAL: 0
        }
        self._num_values = {
            GyroSensor.MODE_GYRO_ANG: 1,
            GyroSensor.MODE_GYRO_RATE: 1,
            GyroSensor.MODE_GYRO_FAS: 1,
            GyroSensor.MODE_GYRO_G_A: 2,
            GyroSensor.MODE_GYRO_CAL: 4
        }
        self._units = {
            GyroSensor.MODE_GYRO_ANG: 'deg',
            GyroSensor.MODE_GYRO_RATE: 'd/s',
            GyroSensor.MODE_GYRO_FAS: None,
            GyroSensor.MODE_GYRO_G_A: None,
            GyroSensor.MODE_GYRO_CAL: None
        }
        self._start_angle = 0
        self._on_mode_change(None, self._mode)

    def _on_mode_change(self, old_mode, new_mode):
        self._start_angle = self._controller.get_actual_pos().get_angle_deg()

    @property
    def value0(self):
        if self._mode == GyroSensor.MODE_GYRO_ANG or self._mode == GyroSensor.MODE_GYRO_G_A:
            return str(self._controller.get_actual_pos().get_angle_deg() - self._start_angle)
        if self._mode == GyroSensor.MODE_GYRO_RATE:
            return str(0)  # TODO: add support
        if self._mode == GyroSensor.MODE_GYRO_FAS:
            return str(0)  # TODO: add support
        if self._mode == GyroSensor.MODE_GYRO_CAL:
            return str(0)  # TODO: add support
        raise Exception()

    @property
    def value1(self):
        if self._mode == GyroSensor.MODE_GYRO_G_A:
            return str(0)  # TODO: add support
        if self._mode == GyroSensor.MODE_GYRO_CAL:
            return str(0)  # TODO: add support
        raise Exception()

    @property
    def value2(self):
        if self._mode == GyroSensor.MODE_GYRO_CAL:
            return str(0)  # TODO: add support
        raise Exception()

    @property
    def value3(self):
        if self._mode == GyroSensor.MODE_GYRO_CAL:
            return str(0)  # TODO: add support
        raise Exception()


class InfraredSensorDriver(SensorDriver):
    def __init__(self, controller: Controller, device_interface: InfraredSensorInterface):
        SensorDriver.__init__(self, controller, device_interface)
        self._commands = []
        self._modes = [InfraredSensor.MODE_IR_PROX, InfraredSensor.MODE_IR_SEEK, InfraredSensor.MODE_IR_REMOTE,
                       InfraredSensor.MODE_IR_REM_A, InfraredSensor.MODE_IR_CAL]
        self._decimals = {
            InfraredSensor.MODE_IR_PROX: 0,
            InfraredSensor.MODE_IR_SEEK: 0,
            InfraredSensor.MODE_IR_REMOTE: 0,
            InfraredSensor.MODE_IR_REM_A: 0,
            InfraredSensor.MODE_IR_CAL: 0
        }
        self._num_values = {
            InfraredSensor.MODE_IR_PROX: 1,
            InfraredSensor.MODE_IR_SEEK: 8,
            InfraredSensor.MODE_IR_REMOTE: 4,
            InfraredSensor.MODE_IR_REM_A: 1,
            InfraredSensor.MODE_IR_CAL: 2
        }
        self._units = {
            InfraredSensor.MODE_IR_PROX: 'pct',
            InfraredSensor.MODE_IR_SEEK: 'pct',
            InfraredSensor.MODE_IR_REMOTE: 'btn',
            InfraredSensor.MODE_IR_REM_A: None,
            InfraredSensor.MODE_IR_CAL: None
        }

    @property
    def value0(self):  # TODO: crop distance values
        if self._mode == InfraredSensor.MODE_IR_PROX:
            distance = self._controller.get_distance_on_pos(self._position)
            return str(int((distance / 70 * 100) if math.isfinite(distance) and distance < 70 else 100))
        if self._mode == InfraredSensor.MODE_IR_SEEK:
            return str(0)  # TODO: add support
        if self._mode == InfraredSensor.MODE_IR_REMOTE:
            return str(0)  # TODO: add support
        if self._mode == InfraredSensor.MODE_IR_REM_A:
            return str(0)  # TODO: add support
        if self._mode == InfraredSensor.MODE_IR_CAL:
            return str(0)  # TODO: add support
        raise Exception()

    @property
    def value1(self):
        if self._mode == InfraredSensor.MODE_IR_SEEK:
            return str(-128)  # TODO: add support
        if self._mode == InfraredSensor.MODE_IR_REMOTE:
            return str(0)  # TODO: add support
        if self._mode == InfraredSensor.MODE_IR_CAL:
            return str(0)  # TODO: add support
        raise Exception()

    @property
    def value2(self):
        if self._mode == InfraredSensor.MODE_IR_SEEK:
            return str(0)  # TODO: add support
        if self._mode == InfraredSensor.MODE_IR_REMOTE:
            return str(0)  # TODO: add support
        raise Exception()

    @property
    def value3(self):
        if self._mode == InfraredSensor.MODE_IR_SEEK:
            return str(-128)  # TODO: add support
        if self._mode == InfraredSensor.MODE_IR_REMOTE:
            return str(0)  # TODO: add support
        raise Exception()

    @property
    def value4(self):
        if self._mode == InfraredSensor.MODE_IR_SEEK:
            return str(0)  # TODO: add support
        raise Exception()

    @property
    def value5(self):
        if self._mode == InfraredSensor.MODE_IR_SEEK:
            return str(-128)  # TODO: add support
        raise Exception()

    @property
    def value6(self):
        if self._mode == InfraredSensor.MODE_IR_SEEK:
            return str(0)  # TODO: add support
        raise Exception()

    @property
    def value7(self):
        if self._mode == InfraredSensor.MODE_IR_SEEK:
            return str(-128)  # TODO: add support
        raise Exception()


class SoundSensorDriver(SensorDriver):
    def __init__(self, controller: Controller, device_interface: SoundSensorInterface):
        SensorDriver.__init__(self, controller, device_interface)
        self._commands = []
        self._modes = [SoundSensor.MODE_DB, SoundSensor.MODE_DBA]
        self._decimals = {
            SoundSensor.MODE_DB: 1,
            SoundSensor.MODE_DBA: 1
        }
        self._num_values = {
            SoundSensor.MODE_DB: 1,
            SoundSensor.MODE_DBA: 1
        }
        self._units = {
            SoundSensor.MODE_DB: 'pct',
            SoundSensor.MODE_DBA: 'pct'
        }

    @property
    def value0(self):
        if self._mode == SoundSensor.MODE_DB:
            return str(0)  # TODO: add support
        if self._mode == SoundSensor.MODE_DBA:
            return str(0)  # TODO: add support
        raise Exception()


class LightSensorDriver(SensorDriver):
    def __init__(self, controller: Controller, device_interface: LightSensorInterface):
        SensorDriver.__init__(self, controller, device_interface)
        self._commands = []
        self._modes = [LightSensor.MODE_REFLECT, LightSensor.MODE_AMBIENT]
        self._decimals = {
            LightSensor.MODE_REFLECT: 1,
            LightSensor.MODE_AMBIENT: 1
        }
        self._num_values = {
            LightSensor.MODE_REFLECT: 1,
            LightSensor.MODE_AMBIENT: 1
        }
        self._units = {
            LightSensor.MODE_REFLECT: 'pct',
            LightSensor.MODE_AMBIENT: 'pct'
        }

    @property
    def value0(self):
        if self._mode == LightSensor.MODE_REFLECT:
            return str(int(self._controller.get_reflect_on_pos(self._position) * 10))
        if self._mode == LightSensor.MODE_AMBIENT:
            return str(int(self._controller.get_light_on_pos(self._position) * 10))
        raise Exception()


class LedDriver(DeviceDriver):
    def __init__(self, controller: Controller, device_interface: LedInterface):
        DeviceDriver.__init__(self, controller, device_interface)
        self._max_brightness = device_interface.max_brightness
        self._brightness = device_interface.brightness
        self._triggers = device_interface.triggers
        self._trigger = 'none'
        self._delay_on = device_interface.delay_on
        self._delay_off = device_interface.delay_off

    @property
    def max_brightness(self):
        return str(self._max_brightness)

    @property
    def brightness(self):
        return str(self._brightness)

    @brightness.setter
    def brightness(self, value):
        self._brightness = int(value)

    @property
    def trigger(self):
        triggers_len = len(self._triggers)
        if triggers_len == 0:
            return ''
        value = self._triggers[0]
        for i in range(1, triggers_len):
            value += ' ' + self._triggers[i]
        return value

    @trigger.setter
    def trigger(self, value):
        if value not in self._triggers:
            raise Exception()
        self._trigger = value
        # TODO: apply trigger

    @property
    def delay_on(self):
        return str(self._delay_on)

    @delay_on.setter
    def delay_on(self, value):
        self._delay_on = int(value)

    @property
    def delay_off(self):
        return str(self._delay_off)

    @delay_off.setter
    def delay_off(self, value):
        self._delay_off = int(value)


DRIVERS = {
    'unknown': DeviceDriver,

    'lego-ev3-l-motor': MotorDriver,
    'lego-nxt-motor': MotorDriver,
    'lego-ev3-m-motor': MotorDriver,

    'lego-sensor': SensorDriver,
    'lego-ev3-touch': TouchSensorDriver,
    'lego-nxt-touch': TouchSensorDriver,
    'lego-ev3-color': ColorSensorDriver,
    'lego-ev3-us': UltrasonicSensorDriver,
    'lego-nxt-us': UltrasonicSensorDriver,
    'lego-ev3-gyro': GyroSensorDriver,
    'lego-ev3-ir': InfraredSensorDriver,
    'lego-nxt-sound': SoundSensorDriver,
    'lego-nxt-light': LightSensorDriver,
    'leds-pwm': LedDriver
}
