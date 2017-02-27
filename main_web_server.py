#!/usr/bin/env python3

import json
import logging
import os

from odict.pyodict import odict

import config
from utils.web_server import FilesWebHandler

log = logging.getLogger(__name__)

robot_programs = odict()
running_controllers = {}


def add_program(robot_program):
    robot_programs[robot_program.name] = robot_program


class MainWebHandler(FilesWebHandler):
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
        program_category_line_filename = data_dir + os.sep + data[2]
        program_input_config_line_filename = data_dir + os.sep + data[3]
        program_enum_config_line_filename = data_dir + os.sep + data[4]
        program_enum_option_config_line_filename = data_dir + os.sep + data[5]
        if not os.path.isfile(page_text_filename) \
                or not os.path.isfile(program_line_filename) \
                or not os.path.isfile(program_category_line_filename) \
                or not os.path.isfile(program_input_config_line_filename):
            return False

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        if self.command != 'HEAD':
            with open(page_text_filename, mode='r') as fh:
                page_text = fh.read()
            with open(program_line_filename, mode='r') as fh:
                program_line = fh.read()
            with open(program_category_line_filename, mode='r') as fh:
                program_category_line = fh.read()
            with open(program_input_config_line_filename, mode='r') as fh:
                program_input_config_line = fh.read()
            with open(program_enum_config_line_filename, mode='r') as fh:
                program_enum_config_line = fh.read()
            with open(program_enum_option_config_line_filename, mode='r') as fh:
                program_enum_option_config_line = fh.read()

            programs_lines = ''
            for robot_program in robot_programs.values():
                categories = odict()
                for value_name, value_info in robot_program.config_values.items():
                    category = value_info['category'] if 'category' in value_info else 'Main'
                    if category not in categories:
                        categories[category] = odict()
                    categories[category][value_name] = value_info

                actual_program_config = ''
                for category_name, category_content in categories.items():
                    actual_program_category_config = ''
                    for value_name, value_info in category_content.items():
                        value_display_name = value_info['display_name']
                        value_type = value_info['type']
                        default_value = value_info['default_value']

                        if value_type == 'enum':  # hack to support enum
                            options = value_info['enum_options']
                            default_value = list(options.keys())[list(options.values()).index(default_value)]
                            value_type = 'str'

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
                        elif value_type == 'enum':
                            # TODO: add support
                            continue
                        else:
                            continue

                        actual_program_category_config += '\n' + program_input_config_line \
                            .replace('<!--robot_program_config_value_name-->', value_name) \
                            .replace('<!--robot_program_config_value_display_name-->', value_display_name) \
                            .replace('<!--robot_program_config_value_input_type-->', value_input_type) \
                            .replace('<!--robot_program_config_value_style_type-->', value_style_type) \
                            .replace('<!--robot_program_config_value_additional_arguments-->',
                                     value_additional_arguments) \
                            .replace('<!--robot_program_config_value_default_value-->', str(default_value))

                    actual_program_config += program_category_line \
                        .replace('<!--robot_program_category_config-->', actual_program_category_config) \
                        .replace('<!--robot_program_config_category_name-->', category_name)

                running = robot_program.name in running_controllers
                programs_lines += '\n' + program_line \
                    .replace('<!--robot_program_config-->', actual_program_config) \
                    .replace('<!--robot_program_name-->', robot_program.name) \
                    .replace('<!--robot_program_state-->', 'running' if running else 'not running') \
                    .replace('<!--robot_program_state_switch-->', 'Stop' if running else 'Start')

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
                    log.exception('Can\'t execute command')
                    additional_controls = ''
                    status = 'fail'
        else:
            program_controller = running_controllers[program_name]
            program_controller.request_exit()
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
