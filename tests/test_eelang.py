"""Тесты eelang-слоя: пайплайны, ..assert:, ..match:, MatchError."""
import unittest

try:
    import eelang
    from eelang import MatchError
except ImportError:
    eelang = MatchError = None

from tests._server import TestServer


def run(source, ns=None):
    """Парсим eelang-исходник C-парсером и исполняем."""
    if ns is None:
        ns = {}
    mod = eelang.parse(source, '<httpee-test>')
    exec(compile(mod, '<httpee-test>', 'exec'), ns)
    return ns


@unittest.skipIf(eelang is None, 'eelang не установлен')
class EelangPipelineTests(unittest.TestCase):
    def test_post_with_assert_pattern(self):
        with TestServer() as srv:
            ns = run(f'''
from httpee import POST, data, headers, httpee, Response
user =
    httpee()
    ..data: {{'name': 'kenneth', 'role': 'admin'}}
    ..headers: {{'X-Test': 'yes'}}
    ..POST: '{srv.url}/users'
    ..assert:
        Response(status=200)
''')
            req = srv.requests[0]
            self.assertEqual(req['body'], 'name=kenneth&role=admin')
            self.assertEqual(req['headers']['x-test'], 'yes')
            self.assertEqual(ns['user'].json()['echo']['method'], 'POST')

    def test_get_without_body(self):
        with TestServer() as srv:
            ns = run(f'''
from httpee import GET, query, httpee, Response
page =
    httpee()
    ..query: {{'page': 2}}
    ..GET: '{srv.url}/users'
    ..assert:
        Response(status=200)
''')
            self.assertEqual(srv.requests[0]['path'], '/users?page=2')
            self.assertEqual(ns['page'].status, 200)

    def test_assert_failure_raises_matcherror(self):
        with TestServer(status=404) as srv:
            with self.assertRaises(MatchError):
                run(f'''
from httpee import GET, httpee, Response
r =
    httpee()
    ..GET: '{srv.url}/missing'
    ..assert:
        Response(status=200)
''')

    def test_assert_binds_variables(self):
        with TestServer() as srv:
            ns = run(f'''
from httpee import GET, httpee, Response
r =
    httpee()
    ..GET: '{srv.url}/ok'
    ..assert:
        Response(status=s)
doubled = s * 2
''')
            self.assertEqual(ns['doubled'], 400)

    def test_match_branches_on_status(self):
        with TestServer(status=418) as srv:
            ns = run(f'''
from httpee import GET, httpee, Response
verdict =
    httpee()
    ..GET: '{srv.url}/teapot'
    ..match:
        case Response(status=200):
            'ok'
        case Response(status=418):
            'teapot'
        case Response(status=n):
            f'HTTP {{n}}'
''')
            self.assertEqual(ns['verdict'], 'teapot')

    def test_match_fallback_captures_status(self):
        with TestServer(status=503) as srv:
            ns = run(f'''
from httpee import GET, httpee, Response
verdict =
    httpee()
    ..GET: '{srv.url}/down'
    ..match:
        case Response(status=200):
            'ok'
        case Response(status=n):
            f'HTTP {{n}}'
''')
            self.assertEqual(ns['verdict'], 'HTTP 503')

    def test_send_with_dynamic_method(self):
        with TestServer() as srv:
            ns = run(f'''
from httpee import send, data, method, url, httpee, Response
m = 'PATCH'
r =
    httpee()
    ..data: {{'v': 1}}
    ..method: m
    ..url: '{srv.url}/thing'
    ..send()
    ..assert:
        Response(status=200)
''')
            self.assertEqual(srv.requests[0]['method'], 'PATCH')
            self.assertEqual(srv.requests[0]['body'], 'v=1')

    def test_json_modifier_in_pipeline(self):
        with TestServer() as srv:
            ns = run(f'''
from httpee import POST, json, httpee, Response
r =
    httpee()
    ..json: {{'nested': [1, 2]}}
    ..POST: '{srv.url}/j'
    ..assert:
        Response(status=200)
''')
            self.assertEqual(srv.requests[0]['body'], '{"nested":[1,2]}')

    def test_form_body_via_data(self):
        with TestServer() as srv:
            ns = run(f'''
from httpee import GET, data, headers, httpee, Response
r =
    httpee()
    ..data: {{'some': 'json'}}
    ..headers: {{'X-A': '1'}}
    ..GET: '{srv.url}/form'
    ..assert:
        Response(status=200)
''')
            self.assertEqual(srv.requests[0]['body'], 'some=json')


    def test_bare_pipeline_without_assignment(self):
        with TestServer() as srv:
            run(f'''
from httpee import send, data, method, url, httpee, Response
httpee()
..data: {{'v': 1}}
..method: 'PATCH'
..url: '{srv.url}/thing'
..send()
..assert:
    Response(status=200)
''')
            self.assertEqual(srv.requests[0]['method'], 'PATCH')
            self.assertEqual(srv.requests[0]['body'], 'v=1')


if __name__ == '__main__':
    unittest.main()
