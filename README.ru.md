# Бронирование переговорных комнат

[English](README.md) · **Русский**

Веб-приложение для бронирования переговорных: список комнат, создание, изменение и отмена броней, календарь занятости, поиск свободных комнат, уведомления и отчёты по использованию. Пересечение встреч в одной комнате исключено на уровне БД (exclusion-констрейнт PostgreSQL), поэтому параллельные запросы не могут занять один слот.

Как пользоваться приложением — в [docs/user-guide.ru.md](docs/user-guide.ru.md) ([English version](docs/user-guide.md)).

## Стек

- Backend: Python 3.12, FastAPI, SQLAlchemy 2, Alembic, pytest
- Frontend: Vue 3, Vite, TypeScript, Vitest
- БД: PostgreSQL 16

## Быстрый старт (Docker)

```bash
docker compose up -d --build
```

Приложение откроется на http://localhost:8000 (фронт и API в одном контейнере, Swagger — `/docs`). Postgres — отдельный контейнер `db`. Миграции и сид выполняются при старте.

| Пользователь | Email | Пароль | Роль |
|---|---|---|---|
| Администратор | `admin@example.com` | `admin12345` | admin |
| Иван Петров | `ivan@example.com` | `employee123` | employee |
| Мария Сидорова | `maria@example.com` | `employee123` | employee |

Остановить: `docker compose down` (данные сохраняются в томе `pgdata`; `docker compose down -v` удалит и их).

### Настройки

Задаются переменными окружения (в `docker-compose.yml` — для сервиса `app`, локально — в `backend/.env`):

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://booking:booking@localhost:5433/booking` | подключение к БД |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | `admin@example.com`, `admin12345` | администратор, создаваемый сидом |
| `JWT_SECRET` | dev-значение | **обязательно заменить вне разработки** |
| `COOKIE_SECURE` | `false` | `true` при работе через HTTPS |
| `ORG_TIMEZONE` | `Europe/Moscow` | зона для рабочих часов 08:00–20:00 |
| `SCHEDULER_ENABLED` | `true` | планировщик напоминаний |

Сид создаёт демонстрационных сотрудников с паролем `employee123` — в боевой среде их нужно удалить или сменить пароли.

## Разработка

Postgres в Docker, бэкенд и фронтенд — локально (hot reload):

```bash
docker compose up -d db                      # Postgres на localhost:5433

cd backend
python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]"
cp .env.example .env
.venv/Scripts/alembic upgrade head           # миграции
.venv/Scripts/python -m app.seed             # сид (идемпотентный)
.venv/Scripts/uvicorn app.main:app --reload  # API на :8000

cd frontend
npm install
npm run dev                                  # Vite, /api проксируется на :8000
```

На Linux/macOS вместо `.venv/Scripts/` используйте `.venv/bin/`. Контейнер `app` при этом нужно остановить (он занимает порт 8000): `docker compose stop app`.

После изменений API типы фронта обновляются командой `npm run gen:api` (OpenAPI → `src/api/schema.d.ts`).

## Тесты

```bash
docker compose up -d db
cd backend && .venv/Scripts/python -m pytest   # нужен запущенный Postgres
cd frontend && npm test                        # Vitest
npm run build                                  # проверка типов и сборка
```

Тесты бэкенда используют отдельную базу `<имя>_test`, она создаётся и мигрируется автоматически.

## Документация

- [docs/user-guide.ru.md](docs/user-guide.ru.md) — инструкция пользователя ([English](docs/user-guide.md))
- [PLAN.md](PLAN.md) — план и прогресс
- [AGENTS.md](AGENTS.md) — контекст и решения для AI-агентов
