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

    def stop(self):
        pass

    def wait_to_exit(self):
        pass


class RobotProgram:
    def __init__(self, name, config_values):
        self.name = name
        self.config_values = config_values

    def execute(self, config=None) -> RobotProgramController:
        pass


class RobotProgramInstance:
    def stop(self):
        pass

    def wait_to_exit(self):
        pass


class SimpleRobotProgramController(RobotProgramController):
    def __init__(self, robot_program, robot_program_instance, config=None):
        super().__init__(robot_program)
        self.robot_program_instance = robot_program_instance
        self.config = {}
        self._update_config(config)

    def _update_config(self, config=None):
        if config is None:
            config = {}
        for name, info in self.robot_program.config_values.items():
            if name not in config:
                config[name] = self.config[name] if name in self.config else info['default_value']

        self.config = config

    def update_config(self, config=None):
        self._update_config(config)
        self.on_config_change()

    def set_config_value(self, name, value):
        if name not in self.config:
            log.error('Can\'t set config value \'' + name + '\' in \'' + self.robot_program.name
                      + '\'. No config value with given name exists.')
            return False

        value_type = self.robot_program.config_values[name]['type']
        if value_type == 'str' or value_type == 'string':
            value = str(value)
        elif value_type == 'int' or value_type == 'integer':
            value = int(value)
        elif value_type == 'float':
            value = float(value)
        elif value_type == 'bool' or value_type == 'boolean':
            value = bool(value)

        self.config[name] = value
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

    def stop(self):
        self.robot_program_instance.stop()

    def wait_to_exit(self):
        self.robot_program_instance.wait_to_exit()
