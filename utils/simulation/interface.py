from ev3dev.auto import Motor, Sensor, Led

from utils.position import Position2D


class DeviceInterface:
    def __init__(self, position):
        self.position = position
        self.class_name = 'unknown'
        self.driver_name = 'unknown'
        self.name = 'unknown'


class MotorInterface(DeviceInterface):
    def __init__(self, position: Position2D):
        DeviceInterface.__init__(self, position)
        self.class_name = Motor.SYSTEM_CLASS_NAME
        self.name = 'motor'
        self.address = 'unknown'
        self.commands = []
        self.count_per_rot = None
        self.count_per_m = None
        self.driver_name = 'unknown'
        self.full_travel_count = None
        self.polarity = 'normal'  # 'inversed'
        self.position = 0
        self.max_speed = None
        self.ramp_up_sp = 0  # TODO: extract defaults from robot
        self.ramp_down_sp = 0  # TODO: extract defaults from robot
        self.stop_action = 'coast'
        self.stop_actions = ['coast', 'brake', 'hold']


class EV3LargeMotorInterface(MotorInterface):
    def __init__(self, position: Position2D, address):
        MotorInterface.__init__(self, position)
        self.address = address
        self.commands = ['run-forever', 'run-to-abs-pos', 'run-to-rel-pos', 'run-timed', 'run-direct', 'stop', 'reset']
        self.count_per_rot = 360
        self.driver_name = 'lego-ev3-l-motor'
        self.max_speed = 1050
        self.ramp_up_sp = 0  # TODO: extract defaults from robot
        self.ramp_down_sp = 0  # TODO: extract defaults from robot


class NXTLargeMotor(MotorInterface):
    def __init__(self, position: Position2D, address):
        MotorInterface.__init__(self, position)
        self.address = address
        self.commands = ['run-forever', 'run-to-abs-pos', 'run-to-rel-pos', 'run-timed', 'run-direct', 'stop', 'reset']
        self.count_per_rot = 360
        self.driver_name = 'lego-nxt-motor'
        self.max_speed = 1050
        self.ramp_up_sp = 0  # TODO: extract defaults from robot
        self.ramp_down_sp = 0  # TODO: extract defaults from robot


class EV3MediumMotorInterface(MotorInterface):
    def __init__(self, position: Position2D, address):
        MotorInterface.__init__(self, position)
        self.address = address
        self.commands = ['run-forever', 'run-to-abs-pos', 'run-to-rel-pos', 'run-timed', 'run-direct', 'stop', 'reset']
        self.count_per_rot = 360
        self.driver_name = 'lego-ev3-m-motor'
        self.max_speed = 1050  # TODO: extract defaults from robot
        self.ramp_up_sp = 0  # TODO: extract defaults from robot
        self.ramp_down_sp = 0  # TODO: extract defaults from robot


class ActuonixL1250MotorInterface(MotorInterface):  # placeholder
    pass  # TODO: add support


class ActuonixL12100MotorInterface(MotorInterface):  # placeholder
    pass  # TODO: add support


class DcMotorInterface(DeviceInterface):  # placeholder
    pass  # TODO: add support


class ServoMotorInterface(DeviceInterface):  # placeholder
    pass  # TODO: add support


class SensorInterface(DeviceInterface):
    def __init__(self, position):
        DeviceInterface.__init__(self, position)
        self.class_name = Sensor.SYSTEM_CLASS_NAME
        self.address = 'unknown'
        self.driver_name = 'unknown'
        self.name = 'sensor'
        self.mode = 'unknown'


class TouchSensorInterface(SensorInterface):
    def __init__(self, position: Position2D, address):
        SensorInterface.__init__(self, position)
        self.address = address
        self.mode = 'TOUCH'


class EV3TouchSensorInterface(TouchSensorInterface):
    def __init__(self, position: Position2D, address):
        TouchSensorInterface.__init__(self, position, address)
        self.driver_name = 'lego-ev3-touch'


class NXTTouchSensorInterface(TouchSensorInterface):
    def __init__(self, position: Position2D, address):
        TouchSensorInterface.__init__(self, position, address)
        self.driver_name = 'lego-nxt-touch'


class ColorSensorInterface(SensorInterface):
    def __init__(self, position: Position2D, address):
        SensorInterface.__init__(self, position)
        self.address = address
        self.mode = 'COL-REFLECT'


class EV3ColorSensorInterface(ColorSensorInterface):
    def __init__(self, position: Position2D, address):
        ColorSensorInterface.__init__(self, position, address)
        self.driver_name = 'lego-ev3-color'


class UltrasonicSensorInterface(SensorInterface):
    def __init__(self, position: Position2D, address):
        SensorInterface.__init__(self, position)
        self.address = address
        self.mode = 'US-DIST-CM'


class EV3UltrasonicSensorInterface(UltrasonicSensorInterface):
    def __init__(self, position: Position2D, address):
        UltrasonicSensorInterface.__init__(self, position, address)
        self.driver_name = 'lego-ev3-us'


class NXTUltrasonicSensorInterface(UltrasonicSensorInterface):
    def __init__(self, position: Position2D, address):
        UltrasonicSensorInterface.__init__(self, position, address)
        self.driver_name = 'lego-nxt-us'


class GyroSensorInterface(SensorInterface):
    def __init__(self, position: Position2D, address):
        SensorInterface.__init__(self, position)
        self.address = address
        self.mode = 'GYRO-ANG'


class EV3GyroSensorInterface(GyroSensorInterface):
    def __init__(self, position: Position2D, address):
        GyroSensorInterface.__init__(self, position, address)
        self.driver_name = 'lego-ev3-gyro'


class InfraredSensorInterface(SensorInterface):
    def __init__(self, position: Position2D, address):
        SensorInterface.__init__(self, position)
        self.address = address
        self.mode = 'IR-PROX'


class EV3InfraredSensorInterface(InfraredSensorInterface):
    def __init__(self, position: Position2D, address):
        InfraredSensorInterface.__init__(self, position, address)
        self.driver_name = 'lego-ev3-ir'


class SoundSensorInterface(SensorInterface):
    def __init__(self, position: Position2D, address):
        SensorInterface.__init__(self, position)
        self.address = address
        self.mode = 'DB'


class NXTSoundSensorInterface(SoundSensorInterface):
    def __init__(self, position: Position2D, address):
        SoundSensorInterface.__init__(self, position, address)
        self.driver_name = 'lego-nxt-sound'


class LightSensorInterface(SensorInterface):
    def __init__(self, position: Position2D, address):
        SensorInterface.__init__(self, position)
        self.address = address
        self.mode = 'REFLECT'


class NXTLightSensorInterface(LightSensorInterface):
    def __init__(self, position: Position2D, address):
        LightSensorInterface.__init__(self, position, address)
        self.driver_name = 'lego-nxt-light'


class LedInterface(DeviceInterface):
    def __init__(self, position: Position2D, name):
        DeviceInterface.__init__(self, position)
        self.class_name = Led.SYSTEM_CLASS_NAME
        self.driver_name = 'unknown'
        self.name = name
        self.max_brightness = None
        self.brightness = 0
        self.triggers = []
        self.delay_on = None
        self.delay_off = None


class EV3LedInterface(LedInterface):
    def __init__(self, position: Position2D, name):
        LedInterface.__init__(self, position, name)
        self.driver_name = 'lego-ev3-leds'  # TODO: extract from robot
        self.max_brightness = 100  # TODO: extract from robot
        self.brightness = 0
        self.triggers = []  # TODO: extract from robot
        self.delay_on = 100  # TODO: extract from robot
        self.delay_off = 100  # TODO: extract from robot


class PowerSupplyInterface(DeviceInterface):  # placeholder
    pass  # TODO: add support


class EV3LegoPortInterface(DeviceInterface):  # placeholder
    pass  # TODO: add support
