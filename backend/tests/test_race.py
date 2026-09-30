"""Гонка: две параллельные брони на один слот — одна создаётся, вторая получает 409.
Нужны настоящие коммиты в двух соединениях, поэтому без откатываемой транзакции из conftest."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier

from sqlalchemy import delete, select

from app.core.db import SessionLocal
from app.core.errors import AppError
from app.models import Booking, Room, User
from app.schemas import BookingCreate
from app.seed import seed
from app.services import bookings

SLOTS = [datetime(2031, 3, d, 7, 0, tzinfo=timezone.utc) for d in range(1, 6)]  # 10:00 МСК, разные дни


def test_parallel_bookings_one_wins():
    with SessionLocal() as db:
        seed(db)
        db.commit()
        room_id = db.scalar(select(Room.id).where(Room.name == "Урал"))
        user_ids = list(db.scalars(select(User.id).order_by(User.id).limit(2)))

    def attempt(start: datetime, user_id: int, gate: Barrier) -> str:
        with SessionLocal() as db:
            user = db.get(User, user_id)
            data = BookingCreate(room_id=room_id, title="race", attendees=2,
                                 start_at=start, end_at=start.replace(hour=8))
            gate.wait()
            try:
                bookings.create(db, user, data)
                return "ok"
            except AppError as e:
                return e.code

    try:
        for start in SLOTS:
            gate = Barrier(2)
            with ThreadPoolExecutor(2) as pool:
                results = sorted(f.result() for f in [pool.submit(attempt, start, u, gate) for u in user_ids])
            assert results == ["BOOKING_CONFLICT", "ok"], (start, results)
    finally:
        with SessionLocal() as db:
            db.execute(delete(Booking).where(Booking.room_id == room_id, Booking.title == "race"))
            db.commit()
