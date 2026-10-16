"""Проверка под gevent: monkey-patch в изолированном подпроцессе.

patch_all() глобально меняет потоки/сокеты процесса, поэтому проверка идёт
в отдельном подпроцессе и не влияет на остальные тесты.
"""
import os
import subprocess
import sys
import tempfile
import unittest

try:
    import gevent  # noqa: F401
except ImportError:
    gevent = None

from tests._server import TestServer

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@unittest.skipUnless(gevent is not None, 'gevent не установлен')
class GeventTests(unittest.TestCase):
    def test_get_under_gevent_monkeypatch(self):
        with TestServer() as srv:
            script = '''\
import gevent.monkey
gevent.monkey.patch_all()
import sys
from eel_http import GET, Response
r = GET(sys.argv[1], None)
assert isinstance(r, Response)
print('status', r.status)
'''
            with tempfile.TemporaryDirectory() as tmp:
                path = os.path.join(tmp, 'gevent_smoke.py')
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(script)
                env = dict(os.environ)
                env['PYTHONPATH'] = REPO_ROOT + os.pathsep + env.get('PYTHONPATH', '')
                proc = subprocess.run(
                    [sys.executable, path, srv.url + '/g'],
                    capture_output=True, text=True, env=env)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn('status 200', proc.stdout)
                self.assertEqual(srv.requests[0]['path'], '/g')


if __name__ == '__main__':
    unittest.main()
