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


# --- изменение и отмена ---

def patch(client, h, booking_id, **body):
    return client.patch(f"{API}/bookings/{booking_id}", headers=h, json=body)


def insert(db, room, user_email, start_delta_min, end_delta_min, title="Встреча"):
    """Бронь напрямую в БД, минуя правила: старт/конец — смещения от начала текущего 15-минутного слота."""
    from app.domain.rules import floor_step
    base = floor_step(datetime.now(timezone.utc))
    user = db.scalar(select(User).where(User.email == user_email))
    b = Booking(room_id=room.id, organizer_id=user.id, title=title, attendees=2,
                start_at=base + timedelta(minutes=start_delta_min), end_at=base + timedelta(minutes=end_delta_min))
    db.add(b)
    db.flush()
    return b


def test_patch_own_booking_fields_and_time(client, room):
    h = auth(client, EMPLOYEE)
    b = create(client, h, room).json()
    r = patch(client, h, b["id"], title="Ревью", attendees=6, **slot("12:00", "13:30"))
    assert r.status_code == 200 and r.json()["title"] == "Ревью" and r.json()["attendees"] == 6
    assert datetime.fromisoformat(r.json()["start_at"]) == datetime(2030, 1, 15, 9, 0, tzinfo=timezone.utc)


def test_patch_without_time_change_and_self_overlap_ok(client, room):
    h = auth(client, EMPLOYEE)
    b = create(client, h, room, "10:00", "11:00").json()
    assert patch(client, h, b["id"], title="Новое").status_code == 200          # AC-4
    assert patch(client, h, b["id"], **slot("10:15", "11:15")).status_code == 200  # сдвиг внутри себя же
    assert patch(client, h, b["id"]).status_code == 200                          # пустой патч


def test_patch_conflict_and_room_move(client, db, room):
    h = auth(client, EMPLOYEE)
    create(client, h, room, "10:00", "11:00")
    b = create(client, h, room, "12:00", "13:00").json()
    r = patch(client, h, b["id"], **slot("10:30", "11:30"))
    assert r.status_code == 409 and error(r) == "BOOKING_CONFLICT"
    assert patch(client, h, b["id"], **slot("11:00", "12:00")).status_code == 200  # встык
    small = db.scalar(select(Room).where(Room.name == "Урал"))  # вместимость 4
    assert error(patch(client, h, b["id"], room_id=small.id, attendees=5)) == "CAPACITY_EXCEEDED"
    assert patch(client, h, b["id"], room_id=small.id, attendees=4).json()["room_id"] == small.id
    assert patch(client, h, b["id"], room_id=999999).status_code == 404
    assert error(patch(client, h, b["id"], start_at="2030-01-15T10:00:00+03:00", end_at="2030-01-15T10:00:00+03:00")) \
        == "INVALID_DURATION"


def test_patch_permissions(client, room):
    b = create(client, auth(client, EMPLOYEE), room).json()
    other = create(client, auth(client, ADMIN), room, "14:00", "15:00").json()
    h_emp = auth(client, EMPLOYEE)
    assert patch(client, h_emp, other["id"], title="x").status_code == 403       # AC-8
    assert patch(client, auth(client, ADMIN), b["id"], title="От админа").status_code == 200
    assert patch(client, h_emp, 999999, title="x").status_code == 404


def test_started_booking_can_only_be_shortened(client, db, room):
    h = auth(client, EMPLOYEE)
    b = insert(db, room, EMPLOYEE[0], -30, 60)  # идёт: началась 30 минут назад
    assert error(patch(client, h, b.id, title="x")) == "BOOKING_STARTED"
    assert error(patch(client, h, b.id, end_at=(b.end_at + timedelta(hours=1)).isoformat())) == "BOOKING_STARTED"
    r = patch(client, h, b.id, end_at=(b.end_at - timedelta(minutes=30)).isoformat())
    assert r.status_code == 200


def test_finished_booking_cannot_change_or_cancel(client, db, room):
    h = auth(client, EMPLOYEE)
    b = insert(db, room, EMPLOYEE[0], -120, -60)
    assert error(patch(client, h, b.id, title="x")) == "BOOKING_FINISHED"
    assert error(client.post(f"{API}/bookings/{b.id}/cancel", headers=h)) == "BOOKING_FINISHED"


def test_cancel_frees_slot_and_is_idempotent(client, room):
    h = auth(client, EMPLOYEE)
    b = create(client, h, room).json()
    assert create(client, auth(client, ADMIN), room).status_code == 409
    r = client.post(f"{API}/bookings/{b['id']}/cancel", headers=h)
    assert r.status_code == 200 and r.json()["status"] == "cancelled" and r.json()["can_edit"] is False
    assert client.post(f"{API}/bookings/{b['id']}/cancel", headers=h).status_code == 200
    assert create(client, auth(client, ADMIN), room).status_code == 201
    assert error(patch(client, h, b["id"], title="x")) == "BOOKING_CANCELLED"


def test_cancel_permissions_and_started_cancel(client, db, room):
    b = create(client, auth(client, EMPLOYEE), room).json()
    assert client.post(f"{API}/bookings/{b['id']}/cancel", headers=auth(client, ADMIN)).status_code == 200
    mine = insert(db, room, ADMIN[0], -30, 60)  # чужая идущая бронь
    assert client.post(f"{API}/bookings/{mine.id}/cancel", headers=auth(client, EMPLOYEE)).status_code == 403
    assert client.post(f"{API}/bookings/{mine.id}/cancel", headers=auth(client, ADMIN)).status_code == 200
    assert client.post(f"{API}/bookings/999999/cancel", headers=auth(client, ADMIN)).status_code == 404
