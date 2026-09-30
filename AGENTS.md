# AGENTS.md — Бронирование переговорных комнат

Веб-приложение: просмотр комнат, бронирование (создание, изменение, отмена), календарь, поиск свободных комнат, отчёты. Главный инвариант: **в одной комнате не бывает пересекающихся броней**.

Общение — на русском. Кратко, по делу.

## Стек

| Часть | Технологии |
|---|---|
| `backend/` | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic, pytest |
| `frontend/` | Vue 3, Vite, TypeScript, Vitest |
| БД | PostgreSQL 16 (Docker) |
| Контракт | OpenAPI бэкенда → типы фронта через `openapi-typescript` |

## Структура

```
backend/            # API, модели, миграции, тесты
frontend/           # SPA
docker-compose.yml  # postgres
docs/               # 01-requirements, 02-design, questions-for-author, 04-testing, 05-report
PLAN.md             # план и прогресс — источник правды по статусу
README.md           # запуск и пользовательская инструкция
```

## Решения (не пересматривать без причины)

1. **Два проекта** (backend + frontend) — выбор пользователя.
2. **PostgreSQL**, а не SQLite: пересечения запрещены exclusion-констрейнтом `EXCLUDE USING gist (room_id WITH =, tstzrange(start_at, end_at) WITH &&) WHERE (status = 'active')`. Сервисный слой даёт понятную ошибку, констрейнт закрывает гонки.
3. **Интервалы полуоткрытые** `[start, end)`: встык (10–11 и 11–12) не конфликтует.
4. **Время в UTC** (`timestamptz`), в API — ISO 8601 с offset, отображение в локальной зоне на фронте.
5. **Отмена** = смена статуса на `cancelled`, запись не удаляется (нужна для отчётов).
6. **Авторизация:** email+пароль, аккаунты создаёт администратор, JWT (access + refresh), роли `employee`/`admin`. Права проверяются на бэкенде.
7. Конфликт → HTTP **409**. Ловим `23P01` (exclusion_violation).
8. **Уведомления** только внутри приложения (опрос раз в 30 с): напоминание за 15 мин и изменение/отмена чужим пользователем.
9. **Статистика** — только администратору: загрузка комнат, пиковые часы, пользователи и отмены, CSV.
10. Правила времени: 08:00–20:00, шаг 15 минут, 15 мин – 8 ч. Повторяющихся встреч нет.
11. Структура помещений (здания/этажи) не уточнена у автора кейса — пока плоский список.

Полные требования: `docs/01-requirements.md`.

## Правила работы

- Начинай с `PLAN.md`: бери первый незакрытый пункт, по завершении отмечай `[x]` и обновляй таблицу прогресса.
- Скоуп: только то, что в плане. Соседние проблемы — упомяни, не чини.
- Логика пересечений — чистые функции, тестируются без БД. Гонки — тест с реальным Postgres.
- Перед новым кодом ищи, как это уже сделано в проекте.
- Типы фронта не пиши руками — генерируй из OpenAPI.
- Не добавляй зависимости ради того, что решается несколькими строками.

## Команды

```
docker compose up -d db                      # Postgres на localhost:5433
cd backend
python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]"
cp .env.example .env
.venv/Scripts/alembic upgrade head           # миграции
.venv/Scripts/python -m app.seed             # сид (идемпотентный)
.venv/Scripts/python -m pytest               # тесты (нужен запущенный db)
.venv/Scripts/uvicorn app.main:app --reload  # API, /docs — Swagger
```
Миграции: после `alembic revision --autogenerate` заменить `%%` на `%` в CHECK и вручную держать `CREATE EXTENSION btree_gist`.

## LLM Wiki

Вики проекта: `C:/Users/Al/Obsidian/LLM Wiki/room-booking/` (`index.md`, `pages/`). Читай по теме, не перед каждым ответом.
Запись — только через ObsidianDataWeave (`C:/Users/Al/Desktop/education/Vibe/ObsidianDataWeave`): `wiki_ingest` → `wiki_compile` → `wiki_lint`, запуск через `python`.
