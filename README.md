# httpee

`httpee` is a thin wrapper around [fetch.py](https://github.com/kennethreitz/fetch.py)
(by Kenneth Reitz) for [eelang](https://github.com/eel-lang/eelang-py): requests are
written as pipelines, responses are checked with patterns.

```python
from httpee import GET, httpee, Response

resp =
    httpee()
    ..GET:
        'https://api.example.com/users'
    ..assert:
        Response(status=200)
```

## Cheatsheet

### A request is a pipeline

```python
httpee()
..data: {'name': 'kenneth', 'role': 'admin'}  # mapping → form-encoded
..headers: {'X-Key': v}                  # headers (repeats add keys)
..query: {'page': 2}                     # query parameters (repeats add keys)
..POST: 'https://api.example.com/users'  # verb performs the request
..assert:
    Response(status=201)                 # failure → MatchError
```

### Bodies

Every request starts with `httpee()`; the body goes through `..json:` or `..data:`.
They are mutually exclusive — using both raises `ValueError`.

| Modifier | Value | Sent as |
|---|---|---|
| — | `httpee()` | empty request — no body |
| `..json:` | any JSON value | `application/json` |
| `..data:` | mapping | form-encoded (`data=`, like requests) |
| `..data:` | str | text (`text/plain; charset=utf-8`) |
| `..data:` | bytes | raw bytes (`application/octet-stream`) |

### Dynamic method — `..send()`

```python
httpee()
..data: {'role': 'moderator'}
..method: m                          # any method, even from a variable
..url: 'https://…'
..send()                             # without ..method: defaults to GET
..assert:
    Response(status=200)
```

### Pattern checks

```python
# ..assert: — shape check, binds variables, failure → MatchError
httpee()
..GET: url
..assert:
    Response(status=s)               # s is available afterwards

# ..match: — branch on status; no match → the value is unchanged
httpee()
..GET: url
..match:
    case Response(status=200): 'ok'
    case Response(status=n): f'HTTP {n}'
```

### Errors

- 4xx/5xx do **not** raise: check the status with a pattern.
- `..json:` together with `..data:` raises `ValueError`.
- Network errors and timeouts are fetch.py exceptions (`RequestError`, `Timeout`).
- `Response` is fetch.py's `Response` (it has a `status` field): `.json()`, `.text`,
  `.headers` work as usual.

### Modifiers at a glance

`..headers:` · `..query:` · `..timeout: 5.0` · `..json:` · `..data:` · `..method:` · `..url:`

## How it works

- Every request starts with `httpee()`. The body goes through `..json:` (JSON) or
  `..data:` (mapping → form-encoded, str → text, bytes → raw bytes); the two are
  mutually exclusive.
- Modifiers accumulate parameters (repeatable, in any order); the verb at the end
  performs the request and returns a `Response`.
- 4xx/5xx do not raise — the status is checked with a pattern; a failed `..assert:`
  raises `MatchError`. Network errors and timeouts are fetch.py exceptions.
- Redirects are followed (up to 10), as in fetch.py.

## Verbs

| Verb | Example | What it does |
|---|---|---|
| `GET` … `OPTIONS` | `..GET: url` | performs the request with this method |
| `send` | `..send()` | performs the request with a previously set `..method:`/`..url:` |

The method can be set up front — and can be anything:

```python
httpee()
..data: {'role': 'moderator'}
..method: 'PATCH'                          # or from a variable
..url:
    'https://api.example.com/users/1'
..send()
..assert:
    Response(status=200)
```

## Modifiers

| Modifier | Example | What it does |
|---|---|---|
| `headers` | `..headers: {'X-Key': v}` | headers (repeats add keys) |
| `query` | `..query: {'page': 2}` | URL query parameters (repeats add keys) |
| `timeout` | `..timeout: 5.0` | request timeout, seconds (default 30) |
| `json` | `..json: {…}` | JSON body (exclusive with `..data:`) |
| `data` | `..data: {…}` / `'text'` / `b'…'` | body: mapping → form, str → text, bytes → raw |
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

Requires Python 3.11+ (CPython 3.15 + [eelang](https://github.com/eel-lang/eelang-py)
0.1.6+ to run the bare-pipeline `.eel` examples). No external dependencies —
[fetch.py](https://github.com/kennethreitz/fetch.py) (MIT © Kenneth Reitz) is vendored
inside as `httpee/_fetch.py`. Works under gevent (`gevent.monkey.patch_all()`).

## Tests

```sh
python -m unittest discover -s tests
```

## License

MIT (`LICENSE`).
