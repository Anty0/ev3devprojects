#!/usr/bin/env python3

import cgi
import json
import logging
import mimetypes
import os
import shutil
import signal
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from time import sleep

import config
import hardware
from robot_program import RobotProgram, RobotProgramInstance, SimpleRobotProgramController

log = logging.getLogger(__name__)
mimetypes.add_type('application/dynamic-content', '.esp')


class FilesWebHandler(BaseHTTPRequestHandler):
    def log_error(self, format, *args):
        log.error(format % args)
        pass

    def log_message(self, format, *args):
        log.debug(format % args)
        pass

    def resolve_post_args(self):
        content_type, options_dictionary = cgi.parse_header(self.headers.get('content-type'))
        if content_type == 'multipart/form-data':
            post_args = cgi.parse_multipart(self.rfile, options_dictionary)
        elif content_type == 'application/x-www-form-urlencoded':
            length = int(self.headers.get('content-length'))
            post_args = urllib.parse.parse_qs(self.rfile.read(length), keep_blank_values=True)
        else:
            post_args = {}

        return post_args

    def resolve_url_info(self):
        url_info = urllib.parse.urlparse(self.path)
        result = type('UrlInfo', (object,), {})()
        result.scheme, result.netloc, result.path, result.params, result.query, result.fragment \
            = url_info.scheme, url_info.netloc, url_info.path, url_info.params, url_info.query, url_info.fragment
        result.args = urllib.parse.parse_qs(url_info.query)
        return result

    def try_handle_request(self, path, post_args, get_args):
        filename = os.curdir + os.sep + 'html' + os.sep + path

        if os.path.isdir(filename):
            if os.path.exists(filename + os.sep + 'index.html'):
                filename += os.sep + 'index.html'
            elif os.path.exists(filename + os.sep + 'index.esp'):
                filename += os.sep + 'index.esp'

        if os.path.isfile(filename):
            mime_type, encoding = mimetypes.guess_type(filename)
            if mime_type is None:
                mime_type = 'text/plain'

            if mime_type == 'application/dynamic-content':
                with open(filename, mode='r') as fh:
                    command_info = json.load(fh)
                method_name = 'command_' + command_info['name']
                if not hasattr(self, method_name):
                    return False
                method = getattr(self, method_name)
                return method(path, post_args, get_args, command_info['data'] if 'data' in command_info else None)

            self.send_response(200)
            self.send_header('Content-type', mime_type)
            self.end_headers()

            if self.command != 'HEAD':
                with open(filename, mode='rb') as fh:
                    shutil.copyfileobj(fh, self.wfile)
        else:
            self.send_error(404, 'File Not Found: %s' % path)
        return True

    def handle_request(self, path, post_args, get_args):
        if not self.try_handle_request(path, post_args, get_args):
            self.send_error(404, 'Can\'t handle: %s' % path)

    def do_HEAD(self):
        url_info = self.resolve_url_info()
        self.handle_request(url_info.path, {}, url_info.args)

    def do_POST(self):
        url_info = self.resolve_url_info()
        self.handle_request(url_info.path, self.resolve_post_args(), url_info.args)

    def do_GET(self):
        url_info = self.resolve_url_info()
        self.handle_request(url_info.path, {}, url_info.args)


class SimpleProgramInstance(RobotProgramInstance):
    def __init__(self):
        self.running = True

    def stop(self):
        self.running = False

    def wait_to_exit(self):
        while self.running:
            sleep(1)


class TestProgram1(RobotProgram):
    def __init__(self, name, config_values):
        super().__init__(name, config_values)

    def execute(self, config=None):
        return SimpleRobotProgramController(self, SimpleProgramInstance(), config)


class TestProgram2(RobotProgram):
    def __init__(self, name, config_values):
        super().__init__(name, config_values)

    def execute(self, config=None):
        return None


robot_programs = {}


def add_program(robot_program):
    robot_programs[robot_program.name] = robot_program


add_program(TestProgram1('SomeProgram1', {
    'SomeText': {
        'display_name': 'Some text',
        'type': 'str',
        'default_value': 'Hello'
    },
    'SomeInt': {
        'display_name': 'Some integer',
        'type': 'int',
        'default_value': 5
    }
}))
add_program(TestProgram2('SomeProgram2', {
    'SomeFloat': {
        'display_name': 'Some float',
        'type': 'float',
        'default_value': 0.2
    },
    'SomeBool': {
        'display_name': 'Some boolean',
        'type': 'bool',
        'default_value': 0.2
    }
}))

running_controllers = {}


class ProgramsPageWebHandler(FilesWebHandler):
    def command_index(self, path, post_args, get_args, data):
        page_text_filename = os.curdir + os.sep + 'data' + os.sep + data[0]
        program_line_filename = os.curdir + os.sep + 'data' + os.sep + data[1]
        program_config_line_filename = os.curdir + os.sep + 'data' + os.sep + data[2]
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
        show_success_info = False

        if not running:
            if program_name in robot_programs:
                program_controller = robot_programs[program_name] \
                    .execute(json.loads(post_args[b'config'][0].decode()))
                if program_controller is not None:
                    running_controllers[program_controller.robot_program.name] = program_controller
                    running = True
                else:
                    show_success_info = True
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
                'showSuccessInfo': 'true' if show_success_info else 'false'
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
            log.info('Changing config of \'' + program_name + '\' to: ' + program_config_text)
            program_controller.update_config(program_config)

        self.send_response(200)
        self.end_headers()
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
            log.info('Changing config value \'' + target + '\' to \'' + value + '\' in \'' + program_name + '\'.')
            program_controller.set_config_value(target, value)

        self.send_response(200)
        self.end_headers()
        return True


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
            hardware.reset()

    threading.Thread(target=start_server).start()
    log.info("Started HTTP server on port %d" % config.SERVER_PORT)

    def handle_exit(signum, frame):
        server.shutdown()

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)


if __name__ == '__main__':
    run()
