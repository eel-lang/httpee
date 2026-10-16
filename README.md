# httpee

`httpee` is a thin wrapper around [httpx](https://www.python-httpx.org/) for
[eelang](https://github.com/eel-lang/eelang-py): requests are written as pipelines,
responses are checked with patterns.

```python
from httpee import POST, headers, httpee, Response

user =
    {'name': 'kenneth', 'role': 'admin'}      # dict → form-encoded, like requests data=
    ..headers: {'Authorization': f'Bearer {token}'}
    ..POST: 'https://api.example.com/users'
    ..assert:
        Response(status=201)

page =
    httpee()                                  # empty request — no body
    ..query: {'page': 2}
    ..GET: 'https://api.example.com/users'
    ..assert:
        Response(status=200)
```

## Cheatsheet

```python
from httpee import (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS, send,
                    httpee, headers, query, timeout, cookies, auth, json,
                    method, url, Response)
from eelang import MatchError
```

### A request is a pipeline

```python
r =
    {'name': 'kenneth', 'role': 'admin'}     # dict → form-encoded
    ..headers: {'X-Key': v}                  # headers (repeats add keys)
    ..query: {'page': 2}                     # query parameters (repeats add keys)
    ..POST: 'https://api.example.com/users'  # verb performs the request
    ..assert:
        Response(status=201)                 # failure → MatchError
```

### Bodies

| Value | Sent as |
|---|---|
| dict | form-encoded (`data=`, like requests) |
| str | text |
| bytes | raw bytes |
| `httpee()` | empty request — no body |
| `..json: {…}` | JSON — takes precedence over the pipeline body |

### Dynamic method — `..send()`

```python
r =
    {'role': 'moderator'}
    ..method: m                          # any method, even from a variable
    ..url: 'https://…'
    ..send()                             # without ..method: defaults to GET
    ..assert:
        Response(status=200)
```

### Pattern checks

```python
# ..assert: — shape check, binds variables, failure → MatchError
p =
    httpee()
    ..GET: url
    ..assert:
        Response(status=s)               # s is available afterwards

# ..match: — branch on status; no match → the value is unchanged
verdict =
    httpee()
    ..GET: url
    ..match:
        case Response(status=200): 'ok'
        case Response(status=n): f'HTTP {n}'
```

### Errors

- 4xx/5xx do **not** raise: check the status with a pattern.
- Network errors and timeouts are httpx exceptions (`ConnectError`, `TimeoutException`).
- `Response` is `httpx.Response` plus `.status`: `.json()`, `.text`, `.headers` work as usual.

### Modifiers at a glance

`..headers:` · `..query:` · `..timeout: 5.0` · `..cookies:` · `..auth: (u, p)` · `..json:` · `..method:` · `..url:`

## How it works

- The pipeline's initial value is the request body: dict → form-encoded, str → text,
  bytes → raw bytes. JSON goes through an explicit `..json: {…}`. A request without
  a body starts with `httpee()`.
- Modifiers accumulate parameters (repeatable, in any order); the verb at the end
  performs the request and returns a `Response`.
- 4xx/5xx do not raise — the status is checked with a pattern; a failed `..assert:`
  raises `MatchError`. Network errors and timeouts are httpx exceptions.

## Verbs

| Verb | Example | What it does |
|---|---|---|
| `GET` … `OPTIONS` | `..GET: url` | performs the request with this method |
| `send` | `..send()` | performs the request with a previously set `..method:`/`..url:` |

The method can be set up front — and can be anything:

```python
patch =
    {'role': 'moderator'}
    ..method: 'PATCH'                          # or from a variable
    ..url: 'https://api.example.com/users/1'
    ..send()
    ..assert:
        Response(status=200)
```

## Modifiers

| Modifier | Example | What it does |
|---|---|---|
| `headers` | `..headers: {'X-Key': v}` | headers (repeats add keys) |
| `query` | `..query: {'page': 2}` | URL query parameters (repeats add keys) |
| `timeout` | `..timeout: 5.0` | request timeout, seconds |
| `cookies` | `..cookies: {'sid': v}` | cookies |
| `auth` | `..auth: ('user', 'pass')` | basic auth (any `httpx.Auth` works) |
| `json` | `..json: {…}` | JSON body (takes precedence over the pipeline body) |
| `method` | `..method: 'PATCH'` | method up front — for `..send()` |
| `url` | `..url: 'https://…'` | URL up front — for `..send()` |

## Installation

```sh
pip install httpee
```

From source:

```sh
git clone https://github.com/eel-lang/httpee
pip install ./httpee
```

Requires CPython 3.15 + [eelang](https://github.com/eel-lang/eelang-py) to run `.eel`
files — the package itself is plain Python, and httpx is its only dependency.
Works under gevent (`gevent.monkey.patch_all()`).

## Tests

```sh
python -m unittest discover -s tests
```

## License

MIT (`LICENSE`).
