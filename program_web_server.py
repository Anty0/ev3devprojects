#!/usr/bin/env python3

import json
import logging
import os
import signal
import threading
from http.server import HTTPServer

from odict.pyodict import odict

import config
import hardware
from auto_drive import AutoDriveRobotProgram
from line_follow import LineFollowRobotProgram
from web_server import FilesWebHandler

log = logging.getLogger(__name__)

robot_programs = odict()
running_controllers = {}


class ProgramsPageWebHandler(FilesWebHandler):
    def _get_html_dir(self):
        return config.SERVER_HTML_DIR

    def _get_data_dir(self):
        return config.SERVER_DATA_DIR

    def command_get_log(self, path, post_args, get_args, data):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        if self.command != 'HEAD':
            self.wfile.write(json.dumps({
                'logText': config.LOG_TMP
            }).encode())

        return True

    def command_index(self, path, post_args, get_args, data):
        data_dir = self._get_data_dir()
        page_text_filename = data_dir + os.sep + data[0]
        program_line_filename = data_dir + os.sep + data[1]
        program_config_line_filename = data_dir + os.sep + data[2]
        if not os.path.isfile(page_text_filename) or not os.path.isfile(program_line_filename) \
                or not os.path.isfile(program_config_line_filename):
            return False

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        if self.command != 'HEAD':
            with open(page_text_filename, mode='r') as fh:
                page_text = fh.read()
            with open(program_line_filename, mode='r') as fh:
                program_line = fh.read()
            with open(program_config_line_filename, mode='r') as fh:
                program_config_line = fh.read()

            programs_lines = ''
            for robot_program in robot_programs.values():
                actual_program_config = ''
                for value_name, value_info in robot_program.config_values.items():
                    value_display_name = value_info['display_name']
                    value_type = value_info['type']
                    default_value = value_info['default_value']

                    if value_type == 'str' or value_type == 'string':
                        value_input_type = 'text'
                        value_style_type = 'string'
                        value_additional_arguments = ''
                    elif value_type == 'int' or value_type == 'integer':
                        value_input_type = 'number'
                        value_style_type = 'integer'
                        value_additional_arguments = 'step=1'
                    elif value_type == 'float':
                        value_input_type = 'number'
                        value_style_type = 'float'
                        value_additional_arguments = 'step=any'
                    elif value_type == 'bool' or value_type == 'boolean':
                        value_input_type = 'checkbox'
                        value_style_type = 'boolean'
                        value_additional_arguments = 'checked' if default_value else ''
                    else:
                        continue

                    actual_program_config += '\n' + program_config_line \
                        .replace('<!--robot_program_config_value_name-->', value_name) \
                        .replace('<!--robot_program_config_value_display_name-->', value_display_name) \
                        .replace('<!--robot_program_config_value_input_type-->', value_input_type) \
                        .replace('<!--robot_program_config_value_style_type-->', value_style_type) \
                        .replace('<!--robot_program_config_value_additional_arguments-->', value_additional_arguments) \
                        .replace('<!--robot_program_config_value_default_value-->', str(default_value))

                running = robot_program.name in running_controllers
                programs_lines += '\n' + program_line \
                    .replace('<!--robot_program_config-->', actual_program_config) \
                    .replace('<!--robot_program_name-->', robot_program.name) \
                    .replace('<!--robot_program_state-->', 'running' if running else 'not running') \
                    .replace('<!--robot_program_state_switch-->', 'Stop' if running else 'Start')
                pass
            page_text = page_text.replace('<!--robot_programs-->', programs_lines)
            self.wfile.write(page_text.encode())
        return True

    def command_execute(self, path, post_args, get_args, data):
        if b'name' not in post_args or b'config' not in post_args:
            return False

        program_name = post_args[b'name'][0].decode()
        running = program_name in running_controllers
        additional_controls = ''
        status = 'none'

        if not running:
            if program_name in robot_programs:
                try:
                    program_controller = robot_programs[program_name] \
                        .execute(json.loads(post_args[b'config'][0].decode()))
                    if program_controller is not None:
                        running_controllers[program_controller.robot_program.name] = program_controller
                        additional_controls = program_controller.get_additional_controls()
                        running = True
                    else:
                        status = 'success'
                except Exception:
                    additional_controls = ''
                    status = 'fail'
        else:
            program_controller = running_controllers[program_name]
            program_controller.stop()
            program_controller.wait_to_exit()
            del running_controllers[program_name]
            running = False

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        if self.command != 'HEAD':
            self.wfile.write(json.dumps({
                'stateText': 'running' if running else 'not running',
                'stateSwitchText': 'Stop' if running else 'Start',
                'additionalControls': additional_controls,
                'showStatus': status
            }).encode())

        return True

    def command_update_config(self, path, post_args, get_args, data):
        if b'name' not in post_args or b'config' not in post_args:
            return False

        program_name = post_args[b'name'][0].decode()
        running = program_name in running_controllers

        if running:
            program_controller = running_controllers[program_name]
            program_config_text = post_args[b'config'][0].decode()
            program_config = json.loads(program_config_text)
            log.info('Changing config of \'%s\' to: %s' % (program_name, program_config_text))
            program_controller.update_config(program_config)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        if self.command != 'HEAD':
            self.wfile.write(json.dumps({
                'success': 'true'
            }).encode())

        return True

    def command_update_config_value(self, path, post_args, get_args, data):
        if b'name' not in post_args or b'target' not in post_args or b'value' not in post_args:
            return False

        program_name = post_args[b'name'][0].decode()
        running = program_name in running_controllers

        if running:
            program_controller = running_controllers[program_name]
            target = post_args[b'target'][0].decode()
            value = post_args[b'value'][0].decode()
            log.info('Changing config value \'%s\' to \'%s\' in \'%s\'.' % (target, value, program_name))
            program_controller.set_config_value(target, value)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        if self.command != 'HEAD':
            self.wfile.write(json.dumps({
                'success': 'true'
            }).encode())

        return True


def add_program(robot_program):
    robot_programs[robot_program.name] = robot_program


add_program(LineFollowRobotProgram())
add_program(AutoDriveRobotProgram())


def run():
    server = HTTPServer(('', config.SERVER_PORT), ProgramsPageWebHandler)

    def start_server():
        try:
            server.serve_forever()
        except (KeyboardInterrupt, Exception) as e:
            log.exception(e)
            if server:
                server.shutdown()
                server.server_close()
        finally:
            hardware.reset_hardware()

    threading.Thread(target=start_server).start()
    log.info("Started HTTP server on port %d" % config.SERVER_PORT)

    def handle_exit(signum, frame):
        server.shutdown()

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)


if __name__ == '__main__':
    run()
