import csv
import io
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AppError

MAX_DAYS = 366

ROOMS_SQL = text("""
SELECT r.id AS room_id, r.name, count(b.id) AS bookings,
       coalesce(sum(extract(epoch FROM least(b.end_at, :end) - greatest(b.start_at, :start)) / 60), 0)::int
         AS booked_minutes
FROM rooms r
LEFT JOIN bookings b ON b.room_id = r.id AND b.status = 'active' AND b.start_at < :end AND b.end_at > :start
GROUP BY r.id ORDER BY r.name
""")

# Часовые слоты в локальной зоне; бронь режется по границам периода.
PEAK_SQL = text("""
WITH b AS (
  SELECT greatest(start_at, :start) AT TIME ZONE :tz AS ls, least(end_at, :end) AT TIME ZONE :tz AS le
  FROM bookings WHERE status = 'active' AND start_at < :end AND end_at > :start
)
SELECT extract(isodow FROM hs)::int AS weekday, extract(hour FROM hs)::int AS hour,
       count(*) AS bookings,
       sum(extract(epoch FROM least(le, hs + interval '1 hour') - greatest(ls, hs)) / 60)::int AS booked_minutes
FROM b, generate_series(date_trunc('hour', ls), le - interval '1 second', interval '1 hour') AS hs
GROUP BY 1, 2 ORDER BY 1, 2
""")

USERS_SQL = text("""
SELECT u.id AS user_id, u.full_name, count(*) AS total,
       count(*) FILTER (WHERE b.status = 'active') AS active,
       count(*) FILTER (WHERE b.status = 'cancelled') AS cancelled,
       round((coalesce(sum(extract(epoch FROM b.end_at - b.start_at)) FILTER (WHERE b.status = 'active'), 0)
              / 3600)::numeric, 2)::float AS hours
FROM bookings b JOIN users u ON u.id = b.organizer_id
WHERE b.start_at >= :start AND b.start_at < :end
GROUP BY u.id ORDER BY hours DESC, u.full_name
""")

SUMMARY_SQL = text("""
SELECT count(*) AS total, count(*) FILTER (WHERE status = 'cancelled') AS cancelled,
       coalesce(avg(extract(epoch FROM end_at - start_at) / 60) FILTER (WHERE status = 'active'), 0)::float
         AS avg_duration_minutes
FROM bookings WHERE start_at >= :start AND start_at < :end
""")


def _period(start: date, end: date) -> tuple[datetime, datetime, int]:
    """Локальные даты организации (включительно) → границы в UTC и число дней."""
    days = (end - start).days + 1
    if days < 1 or days > MAX_DAYS:
        raise AppError(422, "VALIDATION_ERROR", f"Период: from ≤ to и не более {MAX_DAYS} дней")
    utc = lambda d: datetime.combine(d, time(), settings.tz).astimezone(timezone.utc)  # noqa: E731
    return utc(start), utc(end + timedelta(days=1)), days


def _rows(db: Session, sql, start: date, end: date) -> tuple[list[dict], int]:
    s, e, days = _period(start, end)
    return [dict(r) for r in db.execute(sql, {"start": s, "end": e, "tz": settings.org_timezone}).mappings()], days


def rooms(db: Session, start: date, end: date) -> list[dict]:
    rows, days = _rows(db, ROOMS_SQL, start, end)
    available = (settings.work_end.hour - settings.work_start.hour) * 60 * days
    for r in rows:
        r["utilization"] = round(r["booked_minutes"] / available, 4)
    return rows


def peak_hours(db: Session, start: date, end: date) -> list[dict]:
    return _rows(db, PEAK_SQL, start, end)[0]


def users(db: Session, start: date, end: date) -> list[dict]:
    rows = _rows(db, USERS_SQL, start, end)[0]
    for r in rows:
        r["cancel_rate"] = round(r["cancelled"] / r["total"], 4)
    return rows


def summary(db: Session, start: date, end: date) -> dict:
    r = _rows(db, SUMMARY_SQL, start, end)[0][0]
    return {**r, "cancel_rate": round(r["cancelled"] / r["total"], 4) if r["total"] else 0.0,
            "avg_duration_minutes": round(r["avg_duration_minutes"], 1)}


def to_csv(rows: list[dict]) -> str:
    """`;` и BOM — чтобы Excel открыл без мастера импорта (docs/02-design.md, п. 5.5)."""
    out = io.StringIO()
    out.write("﻿")
    if rows:
        w = csv.DictWriter(out, fieldnames=list(rows[0]), delimiter=";", lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    return out.getvalue()
