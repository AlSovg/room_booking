from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models import Booking, Room, User
from tests.conftest import ADMIN, EMPLOYEE, auth

API = "/api/v1"
MSK = "+03:00"


def slot(start: str, end: str, day: int = 15) -> dict:
    """Интервал 2030-01-{day} в поясе организации, например slot('10:00', '11:00')."""
    return {"start_at": f"2030-01-{day:02d}T{start}:00{MSK}", "end_at": f"2030-01-{day:02d}T{end}:00{MSK}"}


@pytest.fixture
def room(db):
    return db.scalar(select(Room).where(Room.name == "Волга"))  # вместимость 10


def create(client, h, room, start="10:00", end="11:00", **kw):
    body = {"room_id": room.id, "title": "Планёрка", "attendees": 4, **slot(start, end), **kw}
    return client.post(f"{API}/bookings", headers=h, json=body)


def error(r):
    return r.json()["error"]["code"]


def test_create_ok(client, room):
    h = auth(client, EMPLOYEE)
    r = create(client, h, room)
    assert r.status_code == 201
    b = r.json()
    assert b["status"] == "active" and b["can_edit"] is True and b["organizer"]["full_name"] == "Иван Петров"
    assert datetime.fromisoformat(b["start_at"]) == datetime(2030, 1, 15, 7, 0, tzinfo=timezone.utc)


def test_conflict_returns_409_with_conflicting_booking(client, room):
    h = auth(client, EMPLOYEE)
    first = create(client, h, room, "10:00", "11:00").json()
    r = create(client, auth(client, ADMIN), room, "10:30", "11:30")
    assert r.status_code == 409 and error(r) == "BOOKING_CONFLICT"
    c = r.json()["error"]["details"]["conflicting_booking"]
    assert c["id"] == first["id"] and c["title"] == "Планёрка" and c["organizer"] == "Иван Петров"


def test_adjacent_and_other_room_are_fine(client, db, room):
    h = auth(client, EMPLOYEE)
    assert create(client, h, room, "10:00", "11:00").status_code == 201
    assert create(client, h, room, "11:00", "12:00").status_code == 201   # встык
    assert create(client, h, room, "09:00", "10:00").status_code == 201   # встык с другой стороны
    other = db.scalar(select(Room).where(Room.name == "Алтай"))
    assert create(client, h, other, "10:00", "11:00").status_code == 201  # другая комната


@pytest.mark.parametrize("kw, code", [
    ({"start": "10:00", "end": "10:00"}, "INVALID_DURATION"),
    ({"start": "10:00", "end": "10:10"}, "INVALID_DURATION"),
    ({"start": "10:05", "end": "11:00"}, "NOT_ALIGNED"),
    ({"start": "07:45", "end": "08:45"}, "OUTSIDE_WORKING_HOURS"),
    ({"start": "19:00", "end": "20:15"}, "OUTSIDE_WORKING_HOURS"),
    ({"attendees": 11}, "CAPACITY_EXCEEDED"),
])
def test_rule_violations_422(client, room, kw, code):
    r = create(client, auth(client, EMPLOYEE), room, kw.pop("start", "10:00"), kw.pop("end", "11:00"), **kw)
    assert r.status_code == 422 and error(r) == code


def test_past_inactive_missing_room_and_bad_input(client, db, room):
    h = auth(client, EMPLOYEE)
    body = {"room_id": room.id, "title": "t", "attendees": 2,
            "start_at": "2020-01-01T10:00:00+03:00", "end_at": "2020-01-01T11:00:00+03:00"}
    assert error(client.post(f"{API}/bookings", headers=h, json=body)) == "BOOKING_IN_PAST"

    room.is_active = False
    db.flush()
    assert error(create(client, h, room)) == "ROOM_INACTIVE"
    missing = client.post(f"{API}/bookings", headers=h, json={"room_id": 999999, "title": "t", "attendees": 2, **slot("10:00", "11:00")})
    assert missing.status_code == 404

    naive = {"room_id": 1, "title": "t", "attendees": 2, "start_at": "2030-01-15T10:00:00", "end_at": "2030-01-15T11:00:00"}
    assert error(client.post(f"{API}/bookings", headers=h, json=naive)) == "VALIDATION_ERROR"  # без offset
    assert client.post(f"{API}/bookings", json=naive).status_code == 401


def test_cancelled_booking_does_not_block(client, db, room):
    h = auth(client, EMPLOYEE)
    b = create(client, h, room).json()
    db.get(Booking, b["id"]).status = "cancelled"
    db.flush()
    assert create(client, h, room).status_code == 201
