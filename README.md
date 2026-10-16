# eel-http

**HTTP для людей. Теперь пайплайнами.**

`eel-http` — маленькая обёртка над [httpx](https://www.python-httpx.org/) для
[eelang](https://github.com/eel-lang/eelang-py): запрос собирается пайплайном, результат проверяется
паттернами. Никаких развесистых вызовов и отдельных проверок статуса.

```python
from eel_http import POST, headers, Response

user =
    {'name': 'kenneth', 'role': 'admin'}      # dict → form-encoded, как requests data=
    ..headers: {'Authorization': f'Bearer {token}'}
    ..POST: 'https://api.example.com/users'
    ..assert:
        Response(status=201)

page =
    None                                     # запрос без тела
    ..query: {'page': 2}
    ..GET: 'https://api.example.com/users'
    ..assert:
        Response(status=200)
```

## Шпаргалка

```python
from eel_http import (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS, send,
                      headers, query, timeout, cookies, auth, json, method,
                      url, Response)
from eelang import MatchError
```

### Запрос — это пайплайн

```python
r =
    {'name': 'kenneth', 'role': 'admin'}     # dict → form-encoded
    ..headers: {'X-Key': v}                  # заголовки (повторы дополняют)
    ..query: {'page': 2}                     # query-параметры (дополняют)
    ..POST: 'https://api.example.com/users'  # глагол выполняет запрос
    ..assert:
        Response(status=201)                 # провал → MatchError
```

### Тела

| Значение | Уходит как |
|---|---|
| dict | form-encoded (`data=`, как requests) |
| str | текст |
| bytes | сырые байты |
| `None` | без тела |
| `..json: {…}` | JSON — побеждает над телом пайплайна |

### Динамический метод — `..send()`

```python
r =
    {'role': 'moderator'}
    ..method: m                          # любой метод, хоть из переменной
    ..url: 'https://…'
    ..send()                             # без ..method: — GET
    ..assert:
        Response(status=200)
```

### Проверки паттернами

```python
# ..assert: — проверка формы, биндит переменные, провал → MatchError
p =
    None
    ..GET: url
    ..assert:
        Response(status=s)               # s видна дальше

# ..match: — ветвление по статусу; нет совпадения → значение не меняется
verdict =
    None
    ..GET: url
    ..match:
        case Response(status=200): 'ok'
        case Response(status=n): f'HTTP {n}'
```

### Ошибки

- 4xx/5xx — **не** исключение: статус проверяйте паттерном.
- Сеть и таймауты — исключения httpx как есть (`ConnectError`, `TimeoutException`).
- `Response` — это `httpx.Response` + `.status`: `.json()`, `.text`, `.headers` работают.

### Модификаторы одним взглядом

`..headers:` · `..query:` · `..timeout: 5.0` · `..cookies:` · `..auth: (u, p)` · `..json:` · `..method:` · `..url:`

## Как это работает

- **Начальное значение пайплайна — тело запроса**: dict → form-encoded,
  str → текст, bytes → сырые байты. JSON — явным `..json: {…}`.
- **Модификаторы** накапливают параметры (повторяемы, в любом порядке);
  **глагол** в конце выполняет запрос и возвращает `Response`.
- **4xx/5xx исключений не вызывают** — статус проверяется паттерном;
  провал `..assert:` — `MatchError`. Сетевые ошибки и таймауты — исключения httpx.

## Глаголы

| Глагол | Пример | Что делает |
|---|---|---|
| `GET` … `OPTIONS` | `..GET: url` | выполняет запрос этим методом |
| `send` | `..send()` | выполняет запрос с заранее заданными `..method:`/`..url:` |

Метод можно передать заранее — он может быть любым:

```python
patch =
    {'role': 'moderator'}
    ..method: 'PATCH'                          # хоть из переменной
    ..url: 'https://api.example.com/users/1'
    ..send()
    ..assert:
        Response(status=200)
```

## Модификаторы

| Модификатор | Пример | Что делает |
|---|---|---|
| `headers` | `..headers: {'X-Key': v}` | заголовки (повторные вызовы дополняют) |
| `query` | `..query: {'page': 2}` | query-параметры URL (дополняют) |
| `timeout` | `..timeout: 5.0` | таймаут запроса, секунды |
| `cookies` | `..cookies: {'sid': v}` | куки |
| `auth` | `..auth: ('user', 'pass')` | basic-auth (можно `httpx.Auth`) |
| `json` | `..json: {…}` | тело JSON-ом (побеждает над телом пайплайна) |
| `method` | `..method: 'PATCH'` | метод заранее — для `..send()` |
| `url` | `..url: 'https://…'` | адрес заранее — для `..send()` |

## Установка

```sh
git clone https://github.com/eel-lang/eel_http
pip install ./eel_http
```

Нужен CPython 3.15 + [eelang](https://github.com/eel-lang/eelang-py) (пакет сам по себе — обычный Python,
но пайплайны даёт язык). Зависимость одна — httpx. Работает под gevent
(`gevent.monkey.patch_all()`).

## Тесты

```sh
python -m unittest discover -s tests
```

## Лицензия

MIT (`LICENSE`).
