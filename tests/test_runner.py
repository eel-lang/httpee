"""Smoke-тесты: настоящий .eel-скрипт через python -m eelang."""
import os
import subprocess
import sys
import tempfile
import unittest

try:
    import eelang  # noqa: F401 — наличие eelang обязательно для runner'а
except ImportError:
    eelang = None

from tests._server import TestServer

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_script(source, env=None):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'smoke.eel')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(source)
        full_env = dict(os.environ)
        full_env['PYTHONPATH'] = REPO_ROOT + os.pathsep + full_env.get('PYTHONPATH', '')
        if env:
            full_env.update(env)
        return subprocess.run(
            [sys.executable, '-m', 'eelang', path],
            capture_output=True, text=True, env=full_env)


@unittest.skipIf(eelang is None, 'eelang не установлен')
class RunnerTests(unittest.TestCase):
    def test_eel_script_ok(self):
        with TestServer() as srv:
            proc = run_script(f'''
from httpee import GET, httpee, Response
r =
    httpee()
    ..GET: '{srv.url}/runner'
    ..assert:
        Response(status=200)
print('status', r.status)
''')
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn('status 200', proc.stdout)
            self.assertEqual(srv.requests[0]['path'], '/runner')

    def test_eel_script_match_error(self):
        with TestServer(status=500) as srv:
            proc = run_script(f'''
from httpee import GET, httpee, Response
r =
    httpee()
    ..GET: '{srv.url}/broken'
    ..assert:
        Response(status=200)
''')
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn('MatchError', proc.stderr)


if __name__ == '__main__':
    unittest.main()
