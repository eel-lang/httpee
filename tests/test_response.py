"""Тесты Response — fetch.Response с паттерн-совместимыми полями."""
import unittest

from httpee import HTTPError, Response
from httpee._fetch import Headers


class ResponseTests(unittest.TestCase):
    def test_status_field(self):
        r = Response(201, Headers(), b'{}', 'http://x/', 'Created')
        self.assertEqual(r.status, 201)

    def test_json(self):
        r = Response(200, Headers([('content-type', 'application/json')]), b'{"k": "v"}',
                     'http://x/', 'OK')
        self.assertEqual(r.json(), {'k': 'v'})

    def test_text(self):
        r = Response(200, Headers([('content-type', 'text/plain; charset=utf-8')]),
                     'привет'.encode('utf-8'), 'http://x/', 'OK')
        self.assertEqual(r.text, 'привет')

    def test_headers_case_insensitive(self):
        r = Response(200, Headers([('Content-Type', 'application/json')]), b'{}',
                     'http://x/', 'OK')
        self.assertEqual(r.headers['content-type'], 'application/json')

    def test_ok(self):
        self.assertTrue(Response(200, Headers(), b'', 'http://x/', 'OK').ok)
        self.assertFalse(Response(404, Headers(), b'', 'http://x/', 'Not Found').ok)

    def test_raise_for_status(self):
        r = Response(500, Headers(), b'', 'http://x/', 'Error')
        with self.assertRaises(HTTPError):
            r.raise_for_status()


if __name__ == '__main__':
    unittest.main()
