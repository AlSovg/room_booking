"""Тесты идут в реальный Postgres (docker compose up -d db), но в отдельную базу `<имя>_test`:
она создаётся и мигрируется сама. Каждый тест — во внешней транзакции, которая откатывается в конце."""
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, make_url, text
from sqlalchemy.orm import Session

from app.core.config import settings

# До импорта app.core.db: движок создаётся при импорте из settings.database_url.
_dev = make_url(settings.database_url)
settings.database_url = _dev.set(database=f"{_dev.database}_test").render_as_string(hide_password=False)
settings.scheduler_enabled = False  # напоминания в тестах вызываются напрямую

from app.core.db import engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import EMPLOYEE_PASSWORD, seed  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    name = make_url(settings.database_url).database
    admin = create_engine(_dev, isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        if not c.scalar(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": name}):
            c.execute(text(f'CREATE DATABASE "{name}"'))
    admin.dispose()
    command.upgrade(Config(Path(__file__).parents[1] / "alembic.ini"), "head")  # alembic/env.py берёт тот же settings.database_url


@pytest.fixture
def db():
    conn = engine.connect()
    tx = conn.begin()
    session = Session(conn, join_transaction_mode="create_savepoint", expire_on_commit=False)
    seed(session)
    yield session
    session.close()
    tx.rollback()
    conn.close()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


ADMIN = (settings.admin_email, settings.admin_password)
EMPLOYEE = ("ivan@example.com", EMPLOYEE_PASSWORD)


def login(client, creds):
    r = client.post("/api/v1/auth/login", json={"email": creds[0], "password": creds[1]})
    return r


def auth(client, creds) -> dict:
    return {"Authorization": f"Bearer {login(client, creds).json()['access_token']}"}
