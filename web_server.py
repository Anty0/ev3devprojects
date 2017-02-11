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
from robot_program import RobotProgram

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


robot_programs = [
    RobotProgram('SomeProgram1', {
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
    }),
    RobotProgram('SomeProgram2', {
        'SomeFloat': {
            'display_name': 'Some float',
            'type': 'float',
            'default_value': 0.2
        }
    })
]
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
            for robot_program in robot_programs:
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

        running = post_args[b'name'][0].decode() in running_controllers

        # TODO: execute/stop program

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        if self.command != 'HEAD':
            self.wfile.write(json.dumps({
                'stateText': 'running' if running else 'not running',
                'stateSwitchText': 'Stop' if running else 'Start'
            }).encode())
            pass

        return True


def run():
    def stop_motors():
        # TODO: stop all motors
        pass

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
            stop_motors()

    threading.Thread(target=start_server).start()
    log.info("Started HTTP server on port %d" % config.SERVER_PORT)

    def handle_exit(signum, frame):
        server.shutdown()

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)


if __name__ == '__main__':
    run()
