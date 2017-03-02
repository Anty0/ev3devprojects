from utils.position import Position2D
from . import driver, interface


class SimulatedEnvironment:
    def __init__(self, controller):
        self._controller = controller
        self._environment = {}

    def get_environment(self):
        return self._environment

    def _add_device(self, device_interface, device):
        class_name = device_interface.class_name
        if class_name not in self._environment:
            self._environment[class_name] = {}

        name = device_interface.name
        index = 0
        while name + str(index) in self._environment[class_name]:
            index += 1

        self._environment[class_name][name + str(index)] = device

    def create_device(self, device_interface):
        device = driver.DRIVERS[device_interface.driver_name](self._controller, device_interface)
        self._add_device(device_interface, device)


def build_simulator(controller, *devices_interfaces: list) -> SimulatedEnvironment:
    simulated_environment = SimulatedEnvironment(controller)
    for device_interface in devices_interfaces:
        simulated_environment.create_device(device_interface)
    return simulated_environment


def _generate_base_ev3_devices(brick_center_position: Position2D):
    left_led_position = brick_center_position.offset_by(Position2D(-0.8, -1.5, 0))
    right_led_position = brick_center_position.offset_by(Position2D(0.8, -1.5, 0))
    return [
        interface.EV3LedInterface(left_led_position, 'ev3:left:red:ev3dev'),
        interface.EV3LedInterface(right_led_position, 'ev3:right:red:ev3dev'),
        interface.EV3LedInterface(left_led_position, 'ev3:left:green:ev3dev'),
        interface.EV3LedInterface(right_led_position, 'ev3:right:green:ev3dev')
    ]


def build_ev3_simulator(controller, brick_center_position: Position2D,
                        *additional_devices_interfaces: list) -> SimulatedEnvironment:
    devices_interfaces = list(_generate_base_ev3_devices(brick_center_position)) + list(additional_devices_interfaces)
    return build_simulator(controller, *devices_interfaces)
