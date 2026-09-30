from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AppError
from app.domain import rules
from app.models import Booking, BookingStatus, Room, User, UserRole
from app.schemas import BookingCreate, BookingOut


def _now() -> datetime:
    return datetime.now(timezone.utc)


def to_out(b: Booking, user: User) -> BookingOut:
    """can_edit: активная, ещё не закончившаяся бронь, и пользователь — владелец или admin."""
    out = BookingOut.model_validate(b)
    out.can_edit = (b.status == BookingStatus.active and b.end_at > _now()
                    and (b.organizer_id == user.id or user.role == UserRole.admin))
    return out


def _check_new(room: Room | None, start: datetime, end: datetime, attendees: int, now: datetime) -> Room:
    """Правила создания (docs/02-design.md, п. 5.2): BR-1, 4, 5, 2, затем комната и вместимость."""
    rules.check_interval(start, end, settings.tz, settings.work_start, settings.work_end)
    rules.check_not_past(start, now)
    if room is None:
        raise AppError(404, "NOT_FOUND", "Комната не найдена")
    rules.check_room_active(room.is_active)
    rules.check_capacity(attendees, room.capacity)
    return room


def _conflict(db: Session, room_id: int, start: datetime, end: datetime, exclude_id: int | None = None) -> AppError:
    q = select(Booking).where(Booking.room_id == room_id, Booking.status == BookingStatus.active,
                              Booking.start_at < end, Booking.end_at > start)  # то же, что overlaps()
    if exclude_id:
        q = q.where(Booking.id != exclude_id)
    other = db.scalars(q.order_by(Booking.start_at)).first()
    details = None
    if other:
        details = {"conflicting_booking": {
            "id": other.id, "title": other.title, "start_at": other.start_at.isoformat(),
            "end_at": other.end_at.isoformat(), "organizer": other.organizer.full_name}}
    return AppError(409, "BOOKING_CONFLICT", "Комната занята в это время", details)


def commit_or_conflict(db: Session, room_id: int, start: datetime, end: datetime,
                       exclude_id: int | None = None) -> None:
    """Вставка/обновление и есть проверка пересечений: констрейнт БД закрывает гонки (ADR-6)."""
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if e.orig.sqlstate != "23P01":  # exclusion_violation
            raise
        raise _conflict(db, room_id, start, end, exclude_id) from e


def create(db: Session, user: User, data: BookingCreate) -> BookingOut:
    start, end = data.start_at.astimezone(timezone.utc), data.end_at.astimezone(timezone.utc)
    _check_new(db.get(Room, data.room_id), start, end, data.attendees, _now())
    booking = Booking(room_id=data.room_id, organizer_id=user.id, title=data.title,
                      attendees=data.attendees, start_at=start, end_at=end)
    db.add(booking)
    commit_or_conflict(db, data.room_id, start, end)
    return to_out(booking, user)
