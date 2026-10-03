# Meeting Room Booking

**English** · [Русский](README.ru.md)

A web app for booking meeting rooms: room list, creating, changing and cancelling bookings, an occupancy calendar, free-room search, notifications and usage reports. Overlapping bookings in the same room are ruled out at the database level (a PostgreSQL exclusion constraint), so concurrent requests can never take the same slot.

How to use the app: [docs/user-guide.md](docs/user-guide.md) ([Русская версия](docs/user-guide.ru.md)).

> The UI is available in Russian and English (the language button in the header; the choice is remembered in the browser). The seed data and most project documents are in Russian.

## Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy 2, Alembic, pytest
- Frontend: Vue 3, Vite, TypeScript, Vitest
- Database: PostgreSQL 16

## Quick start (Docker)

```bash
docker compose up -d --build
```

The app is served at http://localhost:8000 (frontend and API in one container, Swagger at `/docs`). PostgreSQL runs in a separate `db` container. Migrations and seeding run on startup.

| User | Email | Password | Role |
|---|---|---|---|
| Administrator | `admin@example.com` | `admin12345` | admin |
| Ivan Petrov | `ivan@example.com` | `employee123` | employee |
| Maria Sidorova | `maria@example.com` | `employee123` | employee |

Stop: `docker compose down` (data stays in the `pgdata` volume; `docker compose down -v` removes it too).

### Configuration

Set via environment variables (in `docker-compose.yml` for the `app` service, in `backend/.env` for local runs):

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://booking:booking@localhost:5433/booking` | database connection |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | `admin@example.com`, `admin12345` | administrator created by the seed |
| `JWT_SECRET` | development value | **must be replaced outside development** |
| `COOKIE_SECURE` | `false` | set to `true` when served over HTTPS |
| `ORG_TIMEZONE` | `Europe/Moscow` | time zone for working hours 08:00–20:00 |
| `SCHEDULER_ENABLED` | `true` | reminder scheduler |

The seed creates demo employees with the password `employee123`; remove them or change their passwords in a real deployment.

## Development

PostgreSQL in Docker, backend and frontend run locally (hot reload):

```bash
docker compose up -d db                      # PostgreSQL on localhost:5433

cd backend
python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]"
cp .env.example .env
.venv/Scripts/alembic upgrade head           # migrations
.venv/Scripts/python -m app.seed             # seed (idempotent)
.venv/Scripts/uvicorn app.main:app --reload  # API on :8000

cd frontend
npm install
npm run dev                                  # Vite, /api is proxied to :8000
```

On Linux/macOS use `.venv/bin/` instead of `.venv/Scripts/`. Stop the `app` container first (it occupies port 8000): `docker compose stop app`.

After API changes, regenerate the frontend types with `npm run gen:api` (OpenAPI → `src/api/schema.d.ts`).

## Tests

```bash
docker compose up -d db
cd backend && .venv/Scripts/python -m pytest   # needs a running PostgreSQL
cd frontend && npm test                        # Vitest
npm run build                                  # type check and build
```

Backend tests use a separate `<name>_test` database, created and migrated automatically.

## Documentation

- [docs/user-guide.md](docs/user-guide.md) — user guide ([Русский](docs/user-guide.ru.md))
- [AGENTS.md](AGENTS.md) — context and decisions for AI agents
