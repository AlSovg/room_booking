"""Проверка констрейнтов БД."""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Booking, Room, User

T0 = datetime(2030, 1, 1, 10, 0, tzinfo=timezone.utc)


def book(db, room, user, start_min, end_min, **kw):
    b = Booking(room_id=room.id, organizer_id=user.id, title="t", attendees=2,
                start_at=T0 + timedelta(minutes=start_min), end_at=T0 + timedelta(minutes=end_min), **kw)
    db.add(b)
    db.flush()


def test_overlap_rejected_adjacent_and_cancelled_allowed(db):
    room, user = db.query(Room).first(), db.query(User).first()
    book(db, room, user, 0, 60)
    book(db, room, user, 60, 120)  # встык — можно
    with pytest.raises(IntegrityError) as e, db.begin_nested():
        book(db, room, user, 30, 90)
    assert e.value.orig.sqlstate == "23P01"
    with pytest.raises(IntegrityError) as e, db.begin_nested():
        book(db, room, user, 10, 20)  # 10 минут и не кратно 15
    assert e.value.orig.sqlstate == "23514"
    book(db, room, user, 30, 90, status="cancelled")  # отменённая не блокирует
