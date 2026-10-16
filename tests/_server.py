"""Helpers для тестов eel_http."""
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# eel_http из исходника (репозиторий), не из установленного пакета.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class EchoHandler(BaseHTTPRequestHandler):
    """Отвечает JSON-эхом запроса; статус и задержка задаются на сервере."""

    def _handle(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        self.server.requests.append({
            'method': self.command,
            'path': self.path,
            'headers': dict(self.headers.items()),
            'body': body.decode('utf-8', 'replace'),
        })
        if self.server.delay:
            import time
            time.sleep(self.server.delay)
        out = json.dumps({'echo': self.server.requests[-1]}).encode()
        self.send_response(self.server.response_status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', '0' if self.command == 'HEAD' else str(len(out)))
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(out)

    do_GET = _handle
    do_POST = _handle
    do_PUT = _handle
    do_PATCH = _handle
    do_DELETE = _handle
    do_HEAD = _handle
    do_OPTIONS = _handle

    def log_message(self, *args):
        pass


class TestServer:
    """Локальный HTTP-сервер в потоке; requests — список эхо-записей."""

    def __init__(self, status=200, delay=0.0):
        self.response_status = status
        self.delay = delay
        self.requests = []

    def __enter__(self):
        self.httpd = HTTPServer(('127.0.0.1', 0), EchoHandler)
        self.httpd.requests = self.requests
        self.httpd.response_status = self.response_status
        self.httpd.delay = self.delay
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.httpd.server_address[1]
        self.url = f'http://127.0.0.1:{self.port}'
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()
