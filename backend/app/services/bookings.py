from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AppError
from app.domain import rules
from app.models import Booking, BookingStatus, Room, User, UserRole
from app.schemas import BookingCreate, BookingOut, BookingUpdate


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


def _get_editable(db: Session, user: User, booking_id: int) -> Booking:
    """Бронь под блокировкой строки; права — владелец или admin (FR-13)."""
    b = db.scalars(select(Booking).where(Booking.id == booking_id).with_for_update(of=Booking)).first()
    if b is None:
        raise AppError(404, "NOT_FOUND", "Бронь не найдена")
    if b.organizer_id != user.id and user.role != UserRole.admin:
        raise AppError(403, "FORBIDDEN", "Нельзя менять чужую бронь")
    return b


def update(db: Session, user: User, booking_id: int, data: BookingUpdate) -> BookingOut:
    b = _get_editable(db, user, booking_id)
    if b.status == BookingStatus.cancelled:
        raise AppError(422, "BOOKING_CANCELLED", "Бронь отменена")
    changes = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    for k in ("start_at", "end_at"):
        if k in changes:
            changes[k] = changes[k].astimezone(timezone.utc)
    changes = {k: v for k, v in changes.items() if v != getattr(b, k)}
    if not changes:
        return to_out(b, user)

    now = _now()
    start, end = changes.get("start_at", b.start_at), changes.get("end_at", b.end_at)
    only_shortened = changes.keys() == {"end_at"} and end < b.end_at
    rules.check_editable(b.start_at, b.end_at, now, shortened_to=end if only_shortened else None)
    if "start_at" in changes:
        rules.check_not_past(start, now)
    if "start_at" in changes or "end_at" in changes:
        rules.check_interval(start, end, settings.tz, settings.work_start, settings.work_end)
    if "room_id" in changes or "attendees" in changes:
        room = db.get(Room, changes.get("room_id", b.room_id))
        if room is None:
            raise AppError(404, "NOT_FOUND", "Комната не найдена")
        if "room_id" in changes:
            rules.check_room_active(room.is_active)
        rules.check_capacity(changes.get("attendees", b.attendees), room.capacity)

    for k, v in changes.items():
        setattr(b, k, v)
    commit_or_conflict(db, b.room_id, start, end, exclude_id=b.id)
    return to_out(b, user)


def cancel(db: Session, user: User, booking_id: int) -> BookingOut:
    b = _get_editable(db, user, booking_id)
    if b.status == BookingStatus.active:  # повторная отмена — no-op
        rules.check_cancellable(b.end_at, _now())
        b.status, b.cancelled_by, b.cancelled_at = BookingStatus.cancelled, user.id, _now()
        db.commit()
    return to_out(b, user)
