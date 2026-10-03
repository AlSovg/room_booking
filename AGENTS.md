# AGENTS.md — Meeting Room Booking

Web app: browse rooms, book (create, edit, cancel), calendar, free-room search, reports. Core invariant: **a room never has overlapping bookings**.

## Stack

| Part | Technologies |
|---|---|
| `backend/` | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic, pytest |
| `frontend/` | Vue 3, Vite, TypeScript, Vitest, vue-i18n (ru/en) |
| DB | PostgreSQL 16 (Docker) |
| Contract | Backend OpenAPI → frontend types via `openapi-typescript` |

## Layout

```
backend/            # API, models, migrations, tests
frontend/           # SPA
Dockerfile          # single image: built frontend served by the backend
docker-compose.yml  # app + postgres
docs/               # user guide (user-guide.md, user-guide.ru.md)
README.md, README.ru.md  # setup (en/ru)
```

## Decisions (do not revisit without a reason)

1. **Two projects** (backend + frontend).
2. **PostgreSQL**, not SQLite: overlaps are forbidden by the exclusion constraint `EXCLUDE USING gist (room_id WITH =, tstzrange(start_at, end_at) WITH &&) WHERE (status = 'active')`. The service layer gives a readable error, the constraint closes race conditions.
3. **Half-open intervals** `[start, end)`: back-to-back bookings (10–11 and 11–12) do not conflict.
4. **Time in UTC** (`timestamptz`); the API uses ISO 8601 with offset; the frontend displays the organization time zone.
5. **Cancel** = status change to `cancelled`; the row is kept (needed for reports).
6. **Auth:** email + password, accounts created by an administrator, JWT (access + refresh), roles `employee`/`admin`. Permissions are enforced on the backend.
7. Conflict → HTTP **409**, caught from `23P01` (exclusion_violation).
8. **Notifications** are in-app only (polled every 30 s): a reminder 15 min before the start, and a change/cancellation by another user.
9. **Statistics** are admin-only: room utilisation, peak hours, users and cancellations, CSV export.
10. Time rules: 08:00–20:00, 15-minute step, 15 min – 8 h. No recurring meetings.
11. Room structure (buildings/floors) is a flat list.

## Working rules

- Scope: only what was asked. Mention neighbouring problems, do not fix them.
- Overlap logic is pure functions, tested without a DB. Races are tested against a real Postgres.
- Before writing new code, look for how it is already done in the project.
- Do not hand-write frontend API types — generate them from OpenAPI.
- Do not add a dependency for something a few lines can do.
- UI strings live in `frontend/src/locales/{ru,en}.ts`; do not hardcode text in components.
- API errors are translated on the frontend by `error.code` (`errors.<CODE>`, params from `error.details`); notifications store `params` and are rendered from `notif.msg.*`. The Russian `message` fields are only a fallback.

## Commands

```
docker compose up -d db                      # Postgres on localhost:5433
cd backend
python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]"
cp .env.example .env
.venv/Scripts/alembic upgrade head           # migrations
.venv/Scripts/python -m app.seed             # seed (idempotent)
.venv/Scripts/python -m pytest               # tests (needs the db running)
.venv/Scripts/uvicorn app.main:app --reload  # API, /docs — Swagger
```
```
cd frontend
npm install
npm run gen:api   # backend OpenAPI → src/api/schema.d.ts (after API changes)
npm run dev       # Vite, proxies /api to :8000
npm run build     # vue-tsc + build; npm test — Vitest
```
Migrations: after `alembic revision --autogenerate` replace `%%` with `%` in CHECK constraints and keep `CREATE EXTENSION btree_gist` by hand.
