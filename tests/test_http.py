"""Тесты глаголов, модификаторов и send на чистом Python (без eelang)."""
import unittest

import httpx

from httpee import (GET, POST, PATCH, HEAD, send, httpee, headers, query,
                      timeout, cookies, auth, json, method, url, Response)
from tests._server import TestServer


class VerbTests(unittest.TestCase):
    def test_get_executes_and_returns_response(self):
        with TestServer() as srv:
            r = GET(srv.url + '/x', None)
            self.assertIsInstance(r, Response)
            self.assertIsInstance(r, httpx.Response)
            self.assertEqual(r.status, 200)
            self.assertEqual(srv.requests[0]['method'], 'GET')
            self.assertEqual(srv.requests[0]['path'], '/x')

    def test_all_verbs(self):
        with TestServer() as srv:
            for verb, path in [(GET, '/a'), (POST, '/b'), (PATCH, '/c')]:
                r = verb(srv.url + path, None)
                self.assertEqual(r.status, 200)
                self.assertEqual(srv.requests[-1]['method'], verb.__name__)

    def test_head(self):
        with TestServer() as srv:
            r = HEAD(srv.url + '/h', None)
            self.assertEqual(r.status, 200)
            self.assertEqual(srv.requests[0]['method'], 'HEAD')

    def test_httpee_empty_request(self):
        with TestServer() as srv:
            r = GET(srv.url + '/e', httpee())
            self.assertIsInstance(r, Response)
            self.assertEqual(r.status, 200)
            self.assertEqual(srv.requests[0]['method'], 'GET')

    def test_non_2xx_does_not_raise(self):
        with TestServer(status=404) as srv:
            r = GET(srv.url + '/missing', None)
            self.assertEqual(r.status, 404)

    def test_connect_error_propagates(self):
        # Порт занят локальным сервером, но сервер закрыт — соединение разорвётся.
        with TestServer() as srv:
            port = srv.port
        with self.assertRaises(httpx.ConnectError):
            GET(f'http://127.0.0.1:{port}/x', None)

    def test_timeout_propagates(self):
        with TestServer(delay=1.0) as srv:
            with self.assertRaises(httpx.TimeoutException):
                GET(srv.url + '/slow', timeout(0.05, None))

    def test_verb_after_verb_type_error(self):
        with TestServer() as srv:
            r = GET(srv.url + '/x', None)
            with self.assertRaises(TypeError):
                GET(srv.url + '/y', r)


class BodyTests(unittest.TestCase):
    def test_dict_body_is_form_encoded(self):
        with TestServer() as srv:
            POST(srv.url + '/f', {'a': 1, 'b': 'два'})
            body = srv.requests[0]['body']
            self.assertIn('a=1', body)
            self.assertIn('%D0%B4%D0%B2%D0%B0', body)  # urlencoded utf-8
            self.assertIn('application/x-www-form-urlencoded',
                          srv.requests[0]['headers']['Content-Type'])

    def test_str_body_is_raw_text(self):
        with TestServer() as srv:
            POST(srv.url + '/t', 'привет')
            self.assertEqual(srv.requests[0]['body'], 'привет')

    def test_bytes_body_is_raw(self):
        with TestServer() as srv:
            POST(srv.url + '/b', b'\x00\x01raw')
            self.assertEqual(srv.requests[0]['body'], '\x00\x01raw')

    def test_json_modifier_wins_over_body(self):
        with TestServer() as srv:
            POST(srv.url + '/j', json({'x': [1, 2]}, {'ignored': 'body'}))
            self.assertEqual(srv.requests[0]['body'], '{"x":[1,2]}')
            self.assertIn('application/json',
                          srv.requests[0]['headers']['Content-Type'])

    def test_unsupported_body_type_error(self):
        with self.assertRaises(TypeError):
            GET('http://127.0.0.1:1/x', 123)


class ModifierTests(unittest.TestCase):
    def test_headers_and_query_merge_and_repeat(self):
        with TestServer() as srv:
            v = headers({'X-A': '1'}, None)
            v = headers({'X-B': '2'}, v)
            v = query({'page': 2}, v)
            v = query({'size': 10}, v)
            r = GET(srv.url + '/users', v)
            self.assertEqual(r.status, 200)
            req = srv.requests[0]
            self.assertEqual(req['path'], '/users?page=2&size=10')
            self.assertEqual(req['headers']['X-A'], '1')
            self.assertEqual(req['headers']['X-B'], '2')

    def test_cookies(self):
        with TestServer() as srv:
            r = GET(srv.url + '/c', cookies({'sid': 'abc'}, None))
            self.assertEqual(srv.requests[0]['headers']['Cookie'], 'sid=abc')
            self.assertEqual(r.status, 200)

    def test_auth_basic(self):
        with TestServer() as srv:
            GET(srv.url + '/auth', auth(('user', 'pass'), None))
            auth_header = srv.requests[0]['headers'].get('Authorization')
            self.assertIsNotNone(auth_header)
            self.assertTrue(auth_header.startswith('Basic '))

    def test_modifier_after_verb_type_error(self):
        with TestServer() as srv:
            r = GET(srv.url + '/x', None)
            with self.assertRaises(TypeError):
                headers({'X': '1'}, r)


class SendTests(unittest.TestCase):
    def test_send_with_dynamic_method(self):
        with TestServer() as srv:
            m = 'PATCH'
            v = method(m, {'v': 1})
            v = url(srv.url + '/thing', v)
            r = send(v)
            self.assertEqual(r.status, 200)
            self.assertEqual(srv.requests[0]['method'], 'PATCH')
            self.assertEqual(srv.requests[0]['body'], 'v=1')

    def test_send_defaults_to_get(self):
        with TestServer() as srv:
            r = send(url(srv.url + '/g', None))
            self.assertEqual(r.status, 200)
            self.assertEqual(srv.requests[0]['method'], 'GET')

    def test_send_without_url_type_error(self):
        with self.assertRaises(TypeError):
            send(method('POST', None))

    def test_method_is_uppercased(self):
        with TestServer() as srv:
            send(url(srv.url + '/u', method('post', None)))
            self.assertEqual(srv.requests[0]['method'], 'POST')


if __name__ == '__main__':
    unittest.main()
