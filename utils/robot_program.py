import logging

log = logging.getLogger(__name__)


class RobotProgramController:
    def __init__(self, robot_program):
        self.robot_program = robot_program

    def update_config(self, config):
        pass

    def set_config_value(self, name, value) -> bool:
        pass

    def get_config_value(self, name):
        pass

    def get_additional_controls(self):
        pass

    def request_exit(self):
        pass

    def wait_to_exit(self):
        pass


class RobotProgram:
    def __init__(self, name, config_values):
        self.name = name
        self.config_values = config_values

    def execute(self, config=None) -> RobotProgramController:
        pass


class SimpleRobotProgramController(RobotProgramController):
    def __init__(self, robot_program, config=None, private_config=None):
        RobotProgramController.__init__(self, robot_program)

        if private_config is None:
            private_config = {}
        self.private_config = private_config

        self.config = {}
        self._update_config(config)

    def _update_config(self, config=None):
        if config is None:
            config = {}
        for name, info in self.robot_program.config_values.items():
            if name not in config:
                config[name] = self.config[name] if name in self.config else info['default_value']
            else:
                config[name] = self._convert_config_value(name, config[name])

        self.config = config

    def _convert_config_value(self, name, value):
        value_type = self.robot_program.config_values[name]['type']
        converted_value = value
        if value_type == 'str' or value_type == 'string':
            converted_value = str(value)
        elif value_type == 'int' or value_type == 'integer':
            converted_value = int(value)
        elif value_type == 'float':
            converted_value = float(value)
        elif value_type == 'bool' or value_type == 'boolean':
            converted_value = bool(value)
        elif value_type == 'enum':
            converted_value = self.robot_program.config_values[name]['enum_options'][str(value)]
        log.debug('Setting value of ' + str(value_type) + ' ' + str(name)
                  + ' to ' + str(value) + ' as ' + str(type(converted_value)) + ' ' + str(converted_value))
        return converted_value

    def update_config(self, config=None):
        self._update_config(config)
        self.on_config_change()

    def set_private_config_value(self, name, value):
        self.private_config[name] = value
        return True

    def get_private_config_value(self, name):
        if name not in self.private_config:
            return None
        return self.private_config[name]

    def set_config_value(self, name, value):
        if name not in self.config:
            log.error('Can\'t set config value \'' + name + '\' in \'' + self.robot_program.name
                      + '\'. No config value with given name exists.')
            return False

        self.config[name] = self._convert_config_value(name, value)
        self.on_config_value_change(name, value)
        return True

    def get_config_value(self, name):
        if name not in self.config:
            log.error('Can\'t get config value \'' + name + '\' in \'' + self.robot_program.name
                      + '\'. No config value with given name exists.')
            return None

        return self.config[name]

    def on_config_change(self):
        pass

    def on_config_value_change(self, name, new_value):
        pass

    def get_additional_controls(self):
        return ''


class ControllerConfigWrapper:
    def __init__(self, controller):
        self.controller = controller

    def set_config_value(self, name, value) -> bool:
        return self.controller.set_config_value(name, value)

    def get_config_value(self, name):
        return self.controller.get_config_value(name)

    def set_private_config_value(self, name, value):
        return self.controller.set_private_config_value(name, value)

    def get_private_config_value(self, name):
        return self.controller.get_private_config_value(name)
