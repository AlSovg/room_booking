from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models import User
from tests.conftest import ADMIN, EMPLOYEE, auth, login

API = "/api/v1"


def test_login_me_and_bad_token(client):
    r = login(client, EMPLOYEE)
    assert r.status_code == 200 and "httponly" in r.headers["set-cookie"].lower()
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert client.get(f"{API}/me", headers=h).json()["email"] == EMPLOYEE[0]
    for headers in ({}, {"Authorization": "Bearer junk"}):
        r = client.get(f"{API}/me", headers=headers)
        assert r.status_code == 401 and r.json()["error"]["code"] == "UNAUTHENTICATED"


def test_wrong_password_and_unknown_email_look_same(client):
    a = login(client, (EMPLOYEE[0], "wrong-password"))
    b = login(client, ("nobody@example.com", "whatever12"))
    assert a.status_code == b.status_code == 401 and a.json() == b.json()


def test_lockout_after_5_failures(client, db):
    for _ in range(5):
        assert login(client, (EMPLOYEE[0], "wrong-password")).status_code == 401
    r = login(client, EMPLOYEE)  # даже верный пароль не пускает
    assert r.status_code == 429 and int(r.headers["retry-after"]) > 0
    # по истечении блокировки вход возможен
    db.scalar(select(User).where(User.email == EMPLOYEE[0])).locked_until = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert login(client, EMPLOYEE).status_code == 200


def test_refresh_rotates_and_logout_revokes(client):
    login(client, EMPLOYEE)
    old = client.cookies.get("refresh_token")
    r = client.post(f"{API}/auth/refresh")
    assert r.status_code == 200 and client.cookies.get("refresh_token") != old
    client.cookies.set("refresh_token", old, path="/api/v1/auth")  # старый токен уже отозван
    assert client.post(f"{API}/auth/refresh").status_code == 401
    login(client, EMPLOYEE)
    assert client.post(f"{API}/auth/logout").status_code == 204
    assert client.post(f"{API}/auth/refresh").status_code == 401


def test_refresh_token_is_not_an_access_token(client):
    login(client, EMPLOYEE)
    h = {"Authorization": f"Bearer {client.cookies.get('refresh_token')}"}
    assert client.get(f"{API}/me", headers=h).status_code == 401


def test_rbac(client):
    h = auth(client, EMPLOYEE)
    assert client.get(f"{API}/users", headers=h).status_code == 403
    assert client.get(f"{API}/users", headers=auth(client, ADMIN)).status_code == 200


def test_admin_creates_user_who_can_login(client):
    h = auth(client, ADMIN)
    r = client.post(f"{API}/users", headers=h, json={"full_name": "Новый", "email": "New@Example.com"})
    assert r.status_code == 201
    pw = r.json()["temporary_password"]
    assert login(client, ("new@example.com", pw)).status_code == 200  # регистр email не важен
    dup = client.post(f"{API}/users", headers=h, json={"full_name": "Дубль", "email": "new@example.com"})
    assert dup.status_code == 409 and dup.json()["error"]["code"] == "EMAIL_TAKEN"
    bad = client.post(f"{API}/users", headers=h, json={"full_name": "", "email": "nope"})
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "VALIDATION_ERROR"


def test_block_takes_effect_immediately_and_unblock(client, db):
    h_emp = auth(client, EMPLOYEE)
    emp_id = client.get(f"{API}/me", headers=h_emp).json()["id"]
    h_adm = auth(client, ADMIN)
    assert client.patch(f"{API}/users/{emp_id}", headers=h_adm, json={"is_active": False}).status_code == 200
    r = client.get(f"{API}/me", headers=h_emp)  # тот же access-токен
    assert r.status_code == 403 and r.json()["error"]["code"] == "ACCOUNT_DISABLED"
    assert login(client, EMPLOYEE).status_code == 403
    client.patch(f"{API}/users/{emp_id}", headers=h_adm, json={"is_active": True})
    assert login(client, EMPLOYEE).status_code == 200


def test_admin_cannot_lock_out_self(client):
    h = auth(client, ADMIN)
    me = client.get(f"{API}/me", headers=h).json()
    for body in ({"is_active": False}, {"role": "employee"}):
        r = client.patch(f"{API}/users/{me['id']}", headers=h, json=body)
        assert r.status_code == 409 and r.json()["error"]["code"] == "SELF_LOCKOUT"
    assert client.patch(f"{API}/users/{me['id']}", headers=h, json={"full_name": "Босс"}).status_code == 200
    assert client.patch(f"{API}/users/999999", headers=h, json={}).status_code == 404


def test_change_password(client):
    h = auth(client, EMPLOYEE)
    body = {"old_password": "wrong-password", "new_password": "brand-new-pass"}
    assert client.post(f"{API}/me/password", headers=h, json=body).json()["error"]["code"] == "WRONG_PASSWORD"
    body["old_password"] = EMPLOYEE[1]
    assert client.post(f"{API}/me/password", headers=h, json=body).status_code == 204
    assert client.post(f"{API}/auth/refresh").status_code == 401  # старые refresh отозваны
    assert login(client, EMPLOYEE).status_code == 401
    assert login(client, (EMPLOYEE[0], "brand-new-pass")).status_code == 200
    short = {"old_password": "brand-new-pass", "new_password": "short"}
    assert client.post(f"{API}/me/password", headers=h, json=short).status_code == 422


def test_reset_password_unlocks_and_replaces(client, db):
    h = auth(client, ADMIN)
    emp = db.scalar(select(User).where(User.email == EMPLOYEE[0]))
    for _ in range(5):
        login(client, (EMPLOYEE[0], "wrong-password"))
    assert login(client, EMPLOYEE).status_code == 429
    r = client.post(f"{API}/users/{emp.id}/reset-password", headers=h)
    assert r.status_code == 200
    assert login(client, (EMPLOYEE[0], r.json()["temporary_password"])).status_code == 200
    assert login(client, EMPLOYEE).status_code == 401
