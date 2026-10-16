"""Тесты глаголов, модификаторов и send на чистом Python (без eelang)."""
import unittest

from httpee import (GET, POST, PATCH, HEAD, send, httpee, headers, query,
                    timeout, json, data, method, url, Response, RequestError,
                    Timeout)
from tests._server import TestServer


class VerbTests(unittest.TestCase):
    def test_get_executes_and_returns_response(self):
        with TestServer() as srv:
            r = GET(srv.url + '/x', httpee())
            self.assertIsInstance(r, Response)
            self.assertEqual(r.status, 200)
            self.assertEqual(srv.requests[0]['method'], 'GET')
            self.assertEqual(srv.requests[0]['path'], '/x')

    def test_all_verbs(self):
        with TestServer() as srv:
            for verb, path in [(GET, '/a'), (POST, '/b'), (PATCH, '/c')]:
                r = verb(srv.url + path, httpee())
                self.assertEqual(r.status, 200)
                self.assertEqual(srv.requests[-1]['method'], verb.__name__)

    def test_head(self):
        with TestServer() as srv:
            r = HEAD(srv.url + '/h', httpee())
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
            r = GET(srv.url + '/missing', httpee())
            self.assertEqual(r.status, 404)

    def test_connect_error_propagates(self):
        # Порт занят локальным сервером, но сервер закрыт — соединение разорвётся.
        with TestServer() as srv:
            port = srv.port
        with self.assertRaises(RequestError):
            GET(f'http://127.0.0.1:{port}/x', httpee())

    def test_timeout_propagates(self):
        with TestServer(delay=1.0) as srv:
            with self.assertRaises(Timeout):
                GET(srv.url + '/slow', timeout(0.05, httpee()))

    def test_verb_after_verb_type_error(self):
        with TestServer() as srv:
            r = GET(srv.url + '/x', httpee())
            with self.assertRaises(TypeError):
                GET(srv.url + '/y', r)


class BodyTests(unittest.TestCase):
    def test_data_mapping_is_form_encoded(self):
        with TestServer() as srv:
            POST(srv.url + '/f', data({'a': 1, 'b': 'два'}, httpee()))
            body = srv.requests[0]['body']
            self.assertIn('a=1', body)
            self.assertIn('%D0%B4%D0%B2%D0%B0', body)  # urlencoded utf-8
            self.assertIn('application/x-www-form-urlencoded',
                          srv.requests[0]['headers']['content-type'])

    def test_data_str_is_text(self):
        with TestServer() as srv:
            POST(srv.url + '/t', data('привет', httpee()))
            self.assertEqual(srv.requests[0]['body'], 'привет')
            self.assertIn('text/plain',
                          srv.requests[0]['headers']['content-type'])

    def test_data_bytes_is_raw(self):
        with TestServer() as srv:
            POST(srv.url + '/b', data(b'\x00\x01raw', httpee()))
            self.assertEqual(srv.requests[0]['body'], '\x00\x01raw')
            self.assertIn('application/octet-stream',
                          srv.requests[0]['headers']['content-type'])

    def test_json_body(self):
        with TestServer() as srv:
            POST(srv.url + '/j', json({'x': [1, 2]}, httpee()))
            self.assertEqual(srv.requests[0]['body'], '{"x":[1,2]}')
            self.assertIn('application/json',
                          srv.requests[0]['headers']['content-type'])

    def test_json_and_data_are_exclusive(self):
        with self.assertRaises(ValueError):
            json({}, data({'a': 1}, httpee()))
        with self.assertRaises(ValueError):
            data({'a': 1}, json({}, httpee()))

    def test_data_invalid_type_error(self):
        with self.assertRaises(TypeError):
            data(123, httpee())

    def test_pipeline_must_start_with_httpee(self):
        with self.assertRaises(TypeError):
            GET('http://127.0.0.1:1/x', {'a': 1})
        with self.assertRaises(TypeError):
            GET('http://127.0.0.1:1/x', None)
        with self.assertRaises(TypeError):
            data({'a': 1}, 'не-запрос')

    def test_explicit_content_type_is_not_overridden(self):
        with TestServer() as srv:
            v = data('body', httpee())
            v = headers({'Content-Type': 'application/custom'}, v)
            POST(srv.url + '/ct', v)
            self.assertIn('application/custom',
                          srv.requests[0]['headers']['content-type'])


class ModifierTests(unittest.TestCase):
    def test_headers_and_query_merge_and_repeat(self):
        with TestServer() as srv:
            v = headers({'X-A': '1'}, httpee())
            v = headers({'X-B': '2'}, v)
            v = query({'page': 2}, v)
            v = query({'size': 10}, v)
            r = GET(srv.url + '/users', v)
            self.assertEqual(r.status, 200)
            req = srv.requests[0]
            self.assertEqual(req['path'], '/users?page=2&size=10')
            self.assertEqual(req['headers']['x-a'], '1')
            self.assertEqual(req['headers']['x-b'], '2')

    def test_modifier_after_verb_type_error(self):
        with TestServer() as srv:
            r = GET(srv.url + '/x', httpee())
            with self.assertRaises(TypeError):
                headers({'X': '1'}, r)


class SendTests(unittest.TestCase):
    def test_send_with_dynamic_method(self):
        with TestServer() as srv:
            m = 'PATCH'
            v = method(m, data({'v': 1}, httpee()))
            v = url(srv.url + '/thing', v)
            r = send(v)
            self.assertEqual(r.status, 200)
            self.assertEqual(srv.requests[0]['method'], 'PATCH')
            self.assertEqual(srv.requests[0]['body'], 'v=1')

    def test_send_defaults_to_get(self):
        with TestServer() as srv:
            r = send(url(srv.url + '/g', httpee()))
            self.assertEqual(r.status, 200)
            self.assertEqual(srv.requests[0]['method'], 'GET')

    def test_send_without_url_type_error(self):
        with self.assertRaises(TypeError):
            send(method('POST', httpee()))

    def test_method_is_uppercased(self):
        with TestServer() as srv:
            send(url(srv.url + '/u', method('post', httpee())))
            self.assertEqual(srv.requests[0]['method'], 'POST')


if __name__ == '__main__':
    unittest.main()
