from sqlalchemy import func, select, text, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AppError
from app.models import Booking, Notification, NotificationType, Room, User

REMINDER_SQL = text("""
INSERT INTO notifications (user_id, type, booking_id, message, dedupe_key)
SELECT b.organizer_id, 'reminder', b.id,
       'Скоро начнётся: ' || b.title || ', ' || r.name || ', ' ||
       to_char(b.start_at AT TIME ZONE :tz, 'HH24:MI'),
       'reminder:' || b.id || ':' || CAST(extract(epoch FROM b.start_at) AS bigint)
FROM bookings b JOIN rooms r ON r.id = b.room_id
WHERE b.status = 'active' AND b.start_at > now() AND b.start_at <= now() + interval '15 minutes'
ON CONFLICT (dedupe_key) DO NOTHING
""")


def notify_organizer(db: Session, actor: User, b: Booking, kind: NotificationType) -> None:
    """changed/cancelled организатору; своё действие не уведомляет (BR-12). Без commit — в транзакции действия."""
    if b.organizer_id == actor.id:
        return
    room = db.get(Room, b.room_id)
    when = f"{b.start_at.astimezone(settings.tz):%d.%m %H:%M}–{b.end_at.astimezone(settings.tz):%H:%M}"
    verb = "изменена" if kind == NotificationType.changed else "отменена"
    db.add(Notification(user_id=b.organizer_id, type=kind, booking_id=b.id,
                        message=f"Бронь «{b.title}» {verb} ({actor.full_name}): {room.name}, {when}"))


def remind_due(db: Session) -> int:
    """Идемпотентно создаёт напоминания за 15 минут (docs/02-design.md, п. 6); возвращает число новых."""
    n = db.execute(REMINDER_SQL, {"tz": settings.org_timezone}).rowcount
    db.commit()
    return n


def list_for(db: Session, user: User, unread_only: bool, limit: int) -> list[Notification]:
    q = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        q = q.where(Notification.is_read.is_(False))
    return list(db.scalars(q.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit)))


def unread_count(db: Session, user: User) -> int:
    return db.scalar(select(func.count()).where(Notification.user_id == user.id,
                                                Notification.is_read.is_(False)))


def mark_read(db: Session, user: User, notification_id: int) -> Notification:
    n = db.get(Notification, notification_id)
    if n is None or n.user_id != user.id:
        raise AppError(404, "NOT_FOUND", "Уведомление не найдено")
    n.is_read = True
    db.commit()
    return n


def read_all(db: Session, user: User) -> None:
    db.execute(update(Notification).where(Notification.user_id == user.id).values(is_read=True))
    db.commit()
