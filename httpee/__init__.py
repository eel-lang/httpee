"""httpee — тонкая обёртка над httpx для eelang-пайплайнов.

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

import httpx
from collections.abc import Mapping

__version__ = "0.1.0"

_UNSET = object()


class Response(httpx.Response):
    """httpx.Response + свойство ``status`` для паттерна ``Response(status=200)``.

    Остальное — родное: ``.json()``, ``.text``, ``.content``, ``.headers``,
    ``.raise_for_status()``.
    """

    @property
    def status(self):
        return self.status_code


class _Request:
    """Накопленное состояние запроса. Пользователю не виден."""

    __slots__ = ('method', 'url', 'json_body', 'data_body', 'headers', 'params',
                 'timeout', 'cookies', 'auth')

    def __init__(self):
        self.method = None
        self.url = None
        self.json_body = _UNSET
        self.data_body = _UNSET
        self.headers = {}
        self.params = {}
        self.timeout = None
        self.cookies = None
        self.auth = None


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


def _wrap(resp):
    """httpx.Response → httpee.Response (для class-паттернов)."""
    return Response(
        resp.status_code,
        headers=resp.headers,
        content=resp.content,
        request=resp.request,
        extensions=resp.extensions,
        history=resp.history,
        default_encoding=resp.default_encoding,
    )


def _execute(req):
    """Отправить _Request новым httpx.Client и вернуть Response."""
    if req.url is None:
        raise TypeError(
            'запрос без адреса: задайте ..url: или вызовите ..GET:/..POST: с адресом')
    method = (req.method or 'GET').upper()
    kwargs = {}
    if req.json_body is not _UNSET:
        kwargs['json'] = req.json_body
    elif req.data_body is not _UNSET:
        body = req.data_body
        if isinstance(body, Mapping):
            kwargs['data'] = dict(body)
        elif isinstance(body, str):
            kwargs['content'] = body.encode()
            req.headers.setdefault('content-type', 'text/plain; charset=utf-8')
        else:
            kwargs['content'] = bytes(body)
            req.headers.setdefault('content-type', 'application/octet-stream')
    with httpx.Client(timeout=req.timeout) as client:
        resp = client.request(method, req.url, headers=req.headers or None,
                              params=req.params or None, cookies=req.cookies,
                              auth=req.auth, **kwargs)
    return _wrap(resp)


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
        'Значение пайплайна — тело или накопленный запрос.')
    return run


GET = _verb('GET')
POST = _verb('POST')
PUT = _verb('PUT')
PATCH = _verb('PATCH')
DELETE = _verb('DELETE')
HEAD = _verb('HEAD')
OPTIONS = _verb('OPTIONS')


def send(value):
    """Выполнить запрос с заранее заданными ..method:/..url: (..send())."""
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


def cookies(cookies_value, value):
    """..cookies: {...} — куки запроса."""
    req = _ensure(value)
    req.cookies = cookies_value
    return req


def auth(auth_value, value):
    """..auth: ('user', 'pass') — basic-auth; можно httpx.Auth."""
    req = _ensure(value)
    req.auth = auth_value
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
    """..method: 'PATCH' — метод заранее; выполняется ..send()."""
    req = _ensure(value)
    req.method = str(method_value).upper()
    return req


def url(url_value, value):
    """..url: 'https://...' — адрес заранее; выполняется ..send()."""
    req = _ensure(value)
    req.url = url_value
    return req


__all__ = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS',
           'send', 'headers', 'query', 'timeout', 'cookies', 'auth', 'json',
           'data', 'method', 'url', 'Response', 'httpee']
