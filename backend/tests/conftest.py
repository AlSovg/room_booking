"""Тесты идут в реальный Postgres (docker compose up -d db; alembic upgrade head).
Каждый тест — во внешней транзакции, которая откатывается в конце."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import engine, get_db
from app.main import app
from app.seed import EMPLOYEE_PASSWORD, seed


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
