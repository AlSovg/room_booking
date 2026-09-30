from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import DB, require_admin
from app.schemas import PeakCell, RoomStat, StatsSummary, UserStat
from app.services import stats

router = APIRouter(prefix="/stats", tags=["stats"], dependencies=[Depends(require_admin)])

Start = Annotated[date, Query(alias="from")]
End = Annotated[date, Query(alias="to")]
Format = Literal["json", "csv"]


def _csv(name: str, rows: list[dict]) -> Response:
    return Response(stats.to_csv(rows), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{name}.csv"'})


@router.get("/rooms", response_model=list[RoomStat])
def rooms(db: DB, start: Start, end: End, format: Format = "json"):
    rows = stats.rooms(db, start, end)
    return _csv("rooms", rows) if format == "csv" else rows


@router.get("/peak-hours", response_model=list[PeakCell])
def peak_hours(db: DB, start: Start, end: End, format: Format = "json"):
    rows = stats.peak_hours(db, start, end)
    return _csv("peak-hours", rows) if format == "csv" else rows


@router.get("/users", response_model=list[UserStat])
def users(db: DB, start: Start, end: End, format: Format = "json"):
    rows = stats.users(db, start, end)
    return _csv("users", rows) if format == "csv" else rows


@router.get("/summary", response_model=StatsSummary)
def summary(db: DB, start: Start, end: End, format: Format = "json"):
    row = stats.summary(db, start, end)
    return _csv("summary", [row]) if format == "csv" else row
