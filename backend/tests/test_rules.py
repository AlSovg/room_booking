"""Unit-тесты чистых правил, без БД."""
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.domain.rules import (
    RuleViolation, check_capacity, check_editable, check_interval, check_not_past, floor_step, overlaps,
)

MSK = ZoneInfo("Europe/Moscow")
W = (time(8), time(20))


def t(h, m=0, day=1):
    return datetime(2030, 1, day, h, m, tzinfo=MSK)


@pytest.mark.parametrize("a, b, expected", [
    ((10, 11), (11, 12), False),  # встык
    ((11, 12), (10, 11), False),
    ((10, 11), (10, 11), True),   # совпадают
    ((10, 12), (10.5, 11), True),  # вложенный
    ((10, 11), (10.5, 12), True),  # частичное
    ((10, 11), (12, 13), False),  # далеко
])
def test_overlaps(a, b, expected):
    def d(h):
        return datetime(2030, 1, 1, tzinfo=timezone.utc) + timedelta(hours=h)
    assert overlaps(d(a[0]), d(a[1]), d(b[0]), d(b[1])) is expected
    assert overlaps(d(b[0]), d(b[1]), d(a[0]), d(a[1])) is expected  # симметрично


def code(fn, *args, **kw):
    with pytest.raises(RuleViolation) as e:
        fn(*args, **kw)
    return e.value.code


def test_interval_valid_edges():
    check_interval(t(8), t(8, 15), MSK, *W)   # минимум, начало дня
    check_interval(t(12), t(20), MSK, *W)     # ровно 8 часов, конец дня
    check_interval(t(10), t(11), ZoneInfo("UTC"), time(0), time(23, 59))


@pytest.mark.parametrize("start, end, expected", [
    (t(10), t(10), "INVALID_DURATION"),
    (t(11), t(10), "INVALID_DURATION"),
    (t(10), t(10, 10), "INVALID_DURATION"),   # < 15 минут
    (t(8), t(16, 15), "INVALID_DURATION"),    # > 8 часов
    (t(10, 5), t(11), "NOT_ALIGNED"),
    (t(10), t(11, 20), "NOT_ALIGNED"),
    (t(7, 45), t(8, 45), "OUTSIDE_WORKING_HOURS"),
    (t(19), t(20, 15), "OUTSIDE_WORKING_HOURS"),
    (t(19), t(0, day=2), "OUTSIDE_WORKING_HOURS"),
])
def test_interval_invalid(start, end, expected):
    assert code(check_interval, start, end, MSK, *W) == expected


def test_working_hours_use_org_timezone_not_utc():
    # 05:00 UTC = 08:00 MSK — можно; 04:45 UTC = 07:45 MSK — нельзя
    check_interval(t(8).astimezone(timezone.utc), t(9).astimezone(timezone.utc), MSK, *W)
    assert code(check_interval, t(7, 45).astimezone(timezone.utc), t(8, 45).astimezone(timezone.utc), MSK, *W) \
        == "OUTSIDE_WORKING_HOURS"


def test_past_uses_floor_of_now():
    now = t(10, 7)
    assert floor_step(now) == t(10)
    check_not_past(t(10), now)          # начало текущего слота — можно
    assert code(check_not_past, t(9, 45), now) == "BOOKING_IN_PAST"


def test_capacity():
    check_capacity(1, 6), check_capacity(6, 6)
    assert code(check_capacity, 7, 6) == "CAPACITY_EXCEEDED"
    assert code(check_capacity, 0, 6) == "CAPACITY_EXCEEDED"


def test_editable():
    now = t(10, 30)
    check_editable(t(11), t(12), now)                                   # будущая — любые правки
    assert code(check_editable, t(9), t(10), now) == "BOOKING_FINISHED"
    assert code(check_editable, t(10), t(12), now) == "BOOKING_STARTED"  # идёт, правка не только конца
    check_editable(t(10), t(12), now, shortened_to=t(11))               # идёт, сократили
    assert code(check_editable, t(10), t(12), now, shortened_to=t(10, 15)) == "BOOKING_STARTED"  # конец в прошлом
    assert code(check_editable, t(10), t(12), now, shortened_to=t(13)) == "BOOKING_STARTED"      # удлинили
