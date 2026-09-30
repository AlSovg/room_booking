"""Чистые правила бронирования (BR-1…BR-7) без БД. Ничего не импортирует из проекта."""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

STEP = timedelta(minutes=15)
MIN_DURATION = STEP
MAX_DURATION = timedelta(hours=8)


class RuleViolation(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    """Полуоткрытые интервалы [start, end): встык не пересекаются (BR-9)."""
    return a_start < b_end and b_start < a_end


def floor_step(dt: datetime) -> datetime:
    return dt.replace(minute=dt.minute - dt.minute % 15, second=0, microsecond=0)


def check_interval(start: datetime, end: datetime, tz: ZoneInfo, work_start: time, work_end: time) -> None:
    """BR-1, BR-4, BR-5."""
    if not start < end:
        raise RuleViolation("INVALID_DURATION", "Начало должно быть раньше конца")
    if not MIN_DURATION <= end - start <= MAX_DURATION:
        raise RuleViolation("INVALID_DURATION", "Длительность — от 15 минут до 8 часов")
    if any(t.microsecond or int(t.timestamp()) % STEP.seconds for t in (start, end)):
        raise RuleViolation("NOT_ALIGNED", "Начало и конец должны быть кратны 15 минутам")
    s, e = start.astimezone(tz), end.astimezone(tz)
    if s.date() != e.date():
        raise RuleViolation("OUTSIDE_WORKING_HOURS", "Бронь должна укладываться в одни сутки")
    if s.time() < work_start or e.time() > work_end:
        raise RuleViolation("OUTSIDE_WORKING_HOURS",
                            f"Бронирование возможно с {work_start:%H:%M} до {work_end:%H:%M}")


def check_not_past(start: datetime, now: datetime) -> None:
    """BR-2."""
    if start < floor_step(now):
        raise RuleViolation("BOOKING_IN_PAST", "Нельзя бронировать в прошлом")


def check_capacity(attendees: int, capacity: int) -> None:
    """BR-6."""
    if not 1 <= attendees <= capacity:
        raise RuleViolation("CAPACITY_EXCEEDED", f"Участников должно быть от 1 до {capacity}")


def check_room_active(is_active: bool) -> None:
    """BR-7."""
    if not is_active:
        raise RuleViolation("ROOM_INACTIVE", "Комната отключена")


def check_editable(start: datetime, end: datetime, now: datetime, *, shortened_to: datetime | None = None) -> None:
    """BR-3: закончившуюся бронь менять нельзя; начавшуюся — только сократить.

    `shortened_to` — новый конец, если правка сводится к его уменьшению; при любых других правках None.
    """
    if end <= now:
        raise RuleViolation("BOOKING_FINISHED", "Бронь уже закончилась")
    if start <= now and not (shortened_to and now < shortened_to < end):
        raise RuleViolation("BOOKING_STARTED", "Начавшуюся бронь можно только сократить или отменить")


def check_cancellable(end: datetime, now: datetime) -> None:
    if end <= now:
        raise RuleViolation("BOOKING_FINISHED", "Бронь уже закончилась")
