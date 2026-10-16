---
id: httpee-client
type: goal-and-requirements
title: httpee — HTTP-клиент для eelang: запросы пайплайнами
status: active
---

# httpee — HTTP-клиент для eelang

Tagline: «HTTP для людей. Теперь пайплайнами.»

## Цель

httpee — маленький Python-пакет, обёртка над httpx для eelang: HTTP-запрос пишется
одним пайплайном, а результат проверяется паттернами (`..assert:` / `..match:`).
Публикуется на PyPI как `httpee`; исходники — github.com/eel-lang/httpee.

## Аудитория и проблема

Python-разработчик на eelang, который ходит в HTTP-API скриптами. На чистом httpx запрос —
это развесистый вызов `client.request(method=…, url=…, headers=…, params=…, json=…)`
плюс отдельные проверки статуса. httpee сжимает это в одно выражение, где тело,
параметры и проверка читаются сверху вниз.

## Возможности

- **Запрос пайплайном.** Начальное значение — тело запроса; модификаторы накапливают
  параметры; глагол выполняет запрос и возвращает `Response`:

  ```python
  from httpee import GET, POST, httpee, headers, query, timeout, cookies, auth, json, Response

  user =
      {'name': 'kenneth', 'role': 'admin'}      # dict → form-encoded (как requests data=)
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
      {'role': 'moderator'}                   # метод задан заранее — может быть любым
      ..method: 'PATCH'
      ..url: 'https://api.example.com/users/1'
      ..send()
      ..assert:
          Response(status=200)
  ```

- **Глаголы** — `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`; `..send()`
  выполняет запрос с заранее заданными `..method:`/`..url:` (метод может быть динамическим;
  по умолчанию — GET).
  **Модификаторы** — `headers`, `query`, `timeout`, `cookies`, `auth`, `json`, `method`, `url`.
- **Тела:** dict → form-encoded (как `data=` в requests), str → текст, bytes → сырые
  байты; JSON — явным `..json: {…}`. Запрос без тела начинается с `httpee()`.
  Модификаторы можно повторять и ставить в любом порядке перед глаголом.
- **Проверка паттернами:** `..assert: Response(status=200)` — провал → `MatchError`;
  ветвление по статусу — `..match: case Response(status=404): …`.
- **`Response` — подкласс `httpx.Response`** с добавленным свойством `.status`
  (в httpx есть только `.status_code`); `.json()`, `.text`, `.headers`,
  `.raise_for_status()` — родные.
- **4xx/5xx не кидаются** — возвращаются как `Response`, статус проверяется паттерном.
  Сетевые ошибки и таймауты — исключения httpx как есть (`ConnectError`,
  `TimeoutException`).

## Не-цели

- Только sync (`httpx.Client`); async-клиент не делаем.
- Без явных сессий и пулов: каждый запрос — новый `httpx.Client`, как модульный API
  requests. Переиспользуемый клиент — отдельной идеей позже.
- Без ретраев, стриминга и загрузки файлов.
- Не форк и не замена httpx/requests: тонкая обёртка поверх httpx.

## Принципы (по Рейцу)

- API читается как предложение: глаголы ЗАГЛАВНЫМИ (это сами HTTP-методы),
  модификаторы — обычными английскими словами.
- Счастливый путь в одну строку; никакой магии и неявного состояния между запросами.
- Одно очевидное решение; простое лучше сложного.
- Работает под gevent (monkey-patched): только блокирующие сокеты, свои потоки и
  event loop'ы не создаём.
