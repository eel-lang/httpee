"""Тесты Response — подкласс httpx.Response со свойством status."""
import unittest

import httpx

from httpee import Response


class ResponseTests(unittest.TestCase):
    def test_subclass_of_httpx(self):
        self.assertTrue(issubclass(Response, httpx.Response))

    def test_status_property(self):
        r = Response(201, content=b'{}', headers={'content-type': 'application/json'})
        self.assertEqual(r.status, 201)
        self.assertEqual(r.status_code, 201)

    def test_httpx_api_intact(self):
        r = Response(200, content=b'{"k": "v"}',
                     headers={'content-type': 'application/json'})
        self.assertEqual(r.json(), {'k': 'v'})
        self.assertIn('application/json', r.headers['content-type'])
        self.assertEqual(r.status, 200)

    def test_raise_for_status_still_available(self):
        r = Response(500, content=b'', request=httpx.Request('GET', 'http://x/'))
        with self.assertRaises(httpx.HTTPStatusError):
            r.raise_for_status()


if __name__ == '__main__':
    unittest.main()
