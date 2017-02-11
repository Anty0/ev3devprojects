class RobotProgramController:
    def __init__(self, config):
        self.config = config

    def stop(self):
        pass

    def wait_to_exit(self):
        pass


class RobotProgram:
    def __init__(self, name, config_values=None):
        if config_values is None:
            config_values = {}

        self.name = name
        self.config_values = config_values

    def execute(self, config=None) -> RobotProgramController:
        pass
