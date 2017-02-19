import cgi
import json
import logging
import mimetypes
import os
import shutil
import urllib.parse
from http.server import BaseHTTPRequestHandler

log = logging.getLogger(__name__)
mimetypes.add_type('application/dynamic-content', '.esp')


class FilesWebHandler(BaseHTTPRequestHandler):
    def log_error(self, format, *args):
        log.error(format % args)
        pass

    # def log_message(self, format, *args):
    #     log.debug(format % args)
    #     pass

    def _get_html_dir(self):
        return os.curdir

    def resolve_post_args(self):
        content_type_header = self.headers.get('content-type')
        if content_type_header is None:
            return {}

        content_type, options_dictionary = cgi.parse_header(content_type_header)
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
        filename = self._get_html_dir() + os.sep + path

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
