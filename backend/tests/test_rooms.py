from tests.conftest import ADMIN, EMPLOYEE, auth

API = "/api/v1"


def names(client, h, **params):
    return [x["name"] for x in client.get(f"{API}/rooms", headers=h, params=params).json()]


def test_list_filters(client):
    h = auth(client, EMPLOYEE)
    all_names = names(client, h)
    assert all_names == sorted(all_names) and len(all_names) >= 5
    big = client.get(f"{API}/rooms", headers=h, params={"min_capacity": 10}).json()
    assert big and all(r["capacity"] >= 10 for r in big)
    eq = {e["name"]: e["id"] for e in client.get(f"{API}/equipment", headers=h).json()}
    both = names(client, h, equipment_ids=[eq["Проектор"], eq["Видеоконференция"]])
    assert set(both) == {"Алтай", "Онега"}  # нужны обе позиции


def test_employee_cannot_manage(client):
    h = auth(client, EMPLOYEE)
    assert client.post(f"{API}/rooms", headers=h, json={"name": "X", "capacity": 2}).status_code == 403
    assert client.post(f"{API}/equipment", headers=h, json={"name": "X"}).status_code == 403
    assert client.get(f"{API}/rooms").status_code == 401


def test_admin_room_crud_and_inactive_hidden(client):
    h = auth(client, ADMIN)
    eq = client.get(f"{API}/equipment", headers=h).json()[0]
    r = client.post(f"{API}/rooms", headers=h, json={"name": "Новая", "capacity": 3, "equipment_ids": [eq["id"]]})
    assert r.status_code == 201 and r.json()["equipment"] == [eq]
    room_id = r.json()["id"]
    dup = client.post(f"{API}/rooms", headers=h, json={"name": "Новая", "capacity": 3})
    assert dup.status_code == 409 and dup.json()["error"]["code"] == "ROOM_NAME_TAKEN"
    assert client.post(f"{API}/rooms", headers=h, json={"name": "Z", "capacity": 0}).status_code == 422
    bad_eq = client.post(f"{API}/rooms", headers=h, json={"name": "Z", "capacity": 2, "equipment_ids": [99999]})
    assert bad_eq.status_code == 404

    p = client.patch(f"{API}/rooms/{room_id}", headers=h, json={"capacity": 5, "equipment_ids": [], "is_active": False})
    assert p.json()["capacity"] == 5 and p.json()["equipment"] == [] and p.json()["is_active"] is False
    assert "Новая" not in names(client, h) and "Новая" in names(client, h, include_inactive=True)
    assert client.patch(f"{API}/rooms/99999", headers=h, json={}).status_code == 404


def test_equipment_crud_and_in_use(client):
    h = auth(client, ADMIN)
    e = client.post(f"{API}/equipment", headers=h, json={"name": "Флипчарт"})
    assert e.status_code == 201
    dup = client.post(f"{API}/equipment", headers=h, json={"name": "Флипчарт"})
    assert dup.json()["error"]["code"] == "EQUIPMENT_NAME_TAKEN"
    eid = e.json()["id"]
    assert client.patch(f"{API}/equipment/{eid}", headers=h, json={"name": "Флипчарт A1"}).json()["name"] == "Флипчарт A1"
    room = client.post(f"{API}/rooms", headers=h, json={"name": "С флипчартом", "capacity": 4, "equipment_ids": [eid]}).json()
    r = client.delete(f"{API}/equipment/{eid}", headers=h)
    assert r.status_code == 409 and r.json()["error"]["code"] == "EQUIPMENT_IN_USE"
    client.patch(f"{API}/rooms/{room['id']}", headers=h, json={"equipment_ids": []})
    assert client.delete(f"{API}/equipment/{eid}", headers=h).status_code == 204
    assert client.delete(f"{API}/equipment/{eid}", headers=h).status_code == 404
