#!/usr/bin/env python3

import cgi
import json
import logging
import mimetypes
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

import config
from robot_program import RobotProgram

log = logging.getLogger(__name__)
mimetypes.add_type('application/dynamic-content', '.esp')


class FilesWebHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        log.debug(format % args)
        pass

    def resolve_post_args(self):
        content_type, options_dictionary = cgi.parse_header(self.headers.getheader('content-type'))
        if content_type == 'multipart/form-data':
            post_args = cgi.parse_multipart(self.rfile, options_dictionary)
        elif content_type == 'application/x-www-form-urlencoded':
            length = int(self.headers.getheader('content-length'))
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

    def handle_request(self, type, path, post_args, get_args):
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
                return method(type, path, post_args, get_args,
                              command_info['data'] if 'data' in command_info else None)

            self.send_response(200)
            self.send_header('Content-type', mime_type)
            self.end_headers()

            if mime_type.startswith('text'):
                # Open as plain text and encode
                with open(filename, mode='r') as fh:
                    self.wfile.write(fh.read().encode())
            else:
                # Open in binary mode, do not encode
                with open(filename, mode='rb') as fh:
                    self.wfile.write(fh.read())
        else:
            log.error("404: %s not found" % path)
            self.send_error(404, 'File Not Found: %s' % path)
        return True

    def try_handle_request(self, type, path, post_args, get_args):
        if not self.handle_request(type, path, post_args, get_args):
            log.error("404: %s can\'t handle" % path)
            self.send_error(404, 'Can\'t handle: %s' % path)

    def do_POST(self):
        url_info = self.resolve_url_info()
        self.try_handle_request('POST', url_info.path, self.resolve_post_args(), url_info.args)

    def do_GET(self):
        url_info = self.resolve_url_info()
        self.try_handle_request('GET', url_info.path, {}, url_info.args)


robot_programs = [
    RobotProgram('test1'),
    RobotProgram('test2')
]


class ProgramsPageWebHandler(FilesWebHandler):
    def command_main_page(self, type, path, post_args, get_args, data):
        self.send_response(200)  # self.send_response(204)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        program_text = '\n'.join(data[1])
        programs_text = '\n'
        for robot_program in robot_programs:
            programs_text += program_text.replace('<robot_program_name>', robot_program.name) + '\n'
            pass
        page_text = '\n'.join(data[0]).replace('<robot_programs>', programs_text)
        self.wfile.write(page_text.encode())
        return True

        # TODO: create robot program starter and other methods


def run():
    server = None
    try:
        server = HTTPServer(('', config.SERVER_PORT), ProgramsPageWebHandler)
        log.info("Starting HTTP server on port %d" % config.SERVER_PORT)
        server.serve_forever()

    except (KeyboardInterrupt, Exception) as e:
        log.exception(e)

        if server:
            server.socket.close()

            # TODO: stop all motors


if __name__ == '__main__':
    run()
