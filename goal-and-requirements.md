---
id: httpee-client
type: goal-and-requirements
title: httpee — HTTP-клиент для eelang: запросы пайплайнами
status: active
---

# httpee — HTTP-клиент для eelang

Tagline: «HTTP для людей. Теперь пайплайнами.»

## Цель

httpee — маленький Python-пакет, обёртка над fetch.py (завендорен, MIT © Kenneth
Reitz) для eelang: HTTP-запрос пишется одним пайплайном, а результат проверяется
паттернами (`..assert:` / `..match:`).
Публикуется на PyPI как `httpee`; исходники — github.com/eel-lang/httpee.

## Аудитория и проблема

Python-разработчик на eelang, который ходит в HTTP-API скриптами. На чистом fetch.py
запрос — это вызов `fetch.request(method=…, url=…, headers=…, params=…, json=…)`
плюс отдельные проверки статуса. httpee сжимает это в одно выражение, где тело,
параметры и проверка читаются сверху вниз.

## Возможности

- **Запрос пайплайном.** Начинается с `httpee()`; модификаторы накапливают параметры;
  глагол выполняет запрос и возвращает `Response`:

  ```python
  from httpee import GET, POST, httpee, headers, query, timeout, json, data, Response

  user =
      httpee()
      ..data: {'name': 'kenneth', 'role': 'admin'}   # mapping → form-encoded
      ..headers: {'Authorization': f'Bearer {token}'}
      ..POST: 'https://api.example.com/users'
      ..assert:
          Response(status=201)

  page =
      httpee()                                # пустой запрос — тела нет
      ..query: {'page': 2}
      ..GET: 'https://api.example.com/users'
      ..assert:
          Response(status=200)

  patch =
      httpee()
      ..data: {'role': 'moderator'}           # метод задан заранее — может быть любым
      ..method: 'PATCH'
      ..url: 'https://api.example.com/users/1'
      ..send()
      ..assert:
          Response(status=200)
  ```

- **Глаголы** — `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`; `..send()`
  выполняет запрос с заранее заданными `..method:`/`..url:` (метод может быть динамическим;
  по умолчанию — GET).
  **Модификаторы** — `headers`, `query`, `timeout`, `json`, `data`, `method`, `url`.
- **Тела:** `..json: {…}` — JSON; `..data:` — mapping → form-encoded (как `data=` в
  requests), str → текст, bytes → сырые байты; content-type'ы ставит fetch.py.
  `..json:` и `..data:` вместе — `ValueError`. Запрос без тела — просто без
  модификаторов тела. Модификаторы можно повторять и ставить в любом порядке
  перед глаголом.
- **Проверка паттернами:** `..assert: Response(status=200)` — провал → `MatchError`;
  ветвление по статусу — `..match: case Response(status=404): …`.
- **`Response` — это `fetch.Response`** (у него уже есть поле `status`, поэтому
  паттерн `Response(status=200)` работает как есть); `.json()`, `.text`, `.headers`,
  `.raise_for_status()` — родные.
- **4xx/5xx не кидаются** — возвращаются как `Response` (`check_status=False`), статус
  проверяется паттерном. Редиректы следуются (до 10, как в fetch.py). Сетевые ошибки
  и таймауты — исключения fetch.py как есть (`RequestError`, `Timeout`).

## Не-цели

- Только sync (fetch.py, HTTP/1.1); async-клиент не делаем.
- Без явных сессий и пулов: каждый запрос — временная сессия fetch.py, как модульный
  API requests. Переиспользуемый клиент — отдельной идеей позже.
- Без ретраев, стриминга и загрузки файлов.
- Модификаторов `cookies`/`auth` нет — fetch.py их не имеет; заголовки — через `..headers:`.
- Не форк и не замена fetch.py/requests: тонкая обёртка поверх fetch.py.

## Принципы (по Рейцу)

- API читается как предложение: глаголы ЗАГЛАВНЫМИ (это сами HTTP-методы),
  модификаторы — обычными английскими словами.
- Счастливый путь в одну строку; никакой магии и неявного состояния между запросами.
- Одно очевидное решение; простое лучше сложного.
- Работает под gevent (monkey-patched): только блокирующие сокеты, свои потоки и
  event loop'ы не создаём.
