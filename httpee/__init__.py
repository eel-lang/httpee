"""httpee — тонкая обёртка над fetch.py для eelang-пайплайнов.

Запрос начинается с httpee(), тело — через ..json: или ..data:, результат
проверяется паттернами::

    from httpee import POST, headers, json, httpee, Response

    user =
        httpee()
        ..json: {'name': 'kenneth'}
        ..headers: {'Authorization': 'Bearer ...'}
        ..POST: 'https://api.example.com/users'
        ..assert:
            Response(status=201)

    page =
        httpee()
        ..GET: 'https://api.example.com/users'
        ..assert:
            Response(status=200)

4xx/5xx исключений не вызывают — статус проверяется ``..assert:``/``..match:``.
"""

from collections.abc import Mapping

from . import _fetch

__version__ = "0.2.2"

# fetch.py — HTTP-движок (завендорен, MIT © Kenneth Reitz).
Response = _fetch.Response
Error = _fetch.Error
RequestError = _fetch.RequestError
Timeout = _fetch.Timeout
HTTPError = _fetch.HTTPError

_UNSET = object()


class _Request:
    """Накопленное состояние запроса. Пользователю не виден."""

    __slots__ = ('method', 'url', 'json_body', 'data_body', 'headers', 'params',
                 'timeout')

    def __init__(self):
        self.method = None
        self.url = None
        self.json_body = _UNSET
        self.data_body = _UNSET
        self.headers = {}
        self.params = {}
        self.timeout = None


def httpee():
    """Пустой запрос: httpee() ..GET: url — тела нет, пока не задано."""
    return _Request()


def _ensure(value):
    """Значение пайплайна обязано быть _Request (из httpee()); иначе TypeError."""
    if isinstance(value, Response):
        raise TypeError(
            'это уже Response — модификаторы и глаголы идут до выполнения запроса')
    if not isinstance(value, _Request):
        raise TypeError(
            'запрос начинается с httpee(); тело задавайте ..json:/..data:')
    return value


def _execute(req):
    """Отправить _Request через fetch.py и вернуть Response."""
    if req.url is None:
        raise TypeError(
            'запрос без адреса: задайте ..url: или вызовите ..GET:/..POST: с адресом')
    method = (req.method or 'GET').upper()
    kwargs = {}
    if req.json_body is not _UNSET:
        kwargs['json'] = req.json_body
    elif req.data_body is not _UNSET:
        kwargs['data'] = req.data_body
    if req.timeout is not None:
        kwargs['timeout'] = req.timeout
    return _fetch.request(method, req.url, params=req.params or None,
                          headers=req.headers or None, check_status=False, **kwargs)


def _verb(method):
    """Глагол: ..GET: url → GET(url, значение) — выполняет запрос сразу."""

    def run(url, value):
        req = _ensure(value)
        req.method = method
        req.url = url
        return _execute(req)

    run.__name__ = method
    run.__qualname__ = method
    run.__doc__ = (
        f'Выполнить {method}-запрос: ..{method}: url. '
        'Значение пайплайна — httpee().')
    return run


GET = _verb('GET')
POST = _verb('POST')
PUT = _verb('PUT')
PATCH = _verb('PATCH')
DELETE = _verb('DELETE')
HEAD = _verb('HEAD')
OPTIONS = _verb('OPTIONS')


def fetch(value):
    """Выполнить запрос с заранее заданными ..method:/..url: (..fetch())."""
    return _execute(_ensure(value))


def headers(headers_value, value):
    """..headers: {...} — заголовки запроса (повторные вызовы дополняют)."""
    req = _ensure(value)
    req.headers.update({k.lower(): v for k, v in dict(headers_value).items()})
    return req


def query(params_value, value):
    """..query: {...} — query-параметры URL (повторные вызовы дополняют)."""
    req = _ensure(value)
    req.params.update(dict(params_value))
    return req


def timeout(timeout_value, value):
    """..timeout: 5.0 — таймаут запроса в секундах."""
    req = _ensure(value)
    req.timeout = timeout_value
    return req


def json(json_value, value):
    """..json: {…} — тело JSON-ом. Несовместим с ..data:."""
    req = _ensure(value)
    if req.data_body is not _UNSET:
        raise ValueError('..json: и ..data: вместе нельзя — выберите одно')
    req.json_body = json_value
    return req


def data(data_value, value):
    """..data: — тело: mapping → form, str → текст, bytes → сырые. Несовместим с ..json:."""
    req = _ensure(value)
    if not isinstance(data_value, (Mapping, str, bytes, bytearray, memoryview)):
        raise TypeError('..data: принимает mapping, str или bytes')
    if req.json_body is not _UNSET:
        raise ValueError('..json: и ..data: вместе нельзя — выберите одно')
    req.data_body = data_value
    return req


def method(method_value, value):
    """..method: 'PATCH' — метод заранее; выполняется ..fetch()."""
    req = _ensure(value)
    req.method = str(method_value).upper()
    return req


def url(url_value, value):
    """..url: 'https://...' — адрес заранее; выполняется ..fetch()."""
    req = _ensure(value)
    req.url = url_value
    return req


__all__ = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS',
           'fetch', 'headers', 'query', 'timeout', 'json', 'data', 'method',
           'url', 'Response', 'Error', 'RequestError', 'Timeout', 'HTTPError',
           'httpee']
