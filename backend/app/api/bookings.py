from typing import Annotated, Literal

from fastapi import APIRouter, Query
from pydantic import AwareDatetime

from app.api.deps import DB, CurrentUser
from app.schemas import BookingCreate, BookingOut, BookingUpdate
from app.services import bookings

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("")
def list_bookings(user: CurrentUser, db: DB, start: Annotated[AwareDatetime, Query(alias="from")],
                  end: Annotated[AwareDatetime, Query(alias="to")], room_id: int | None = None) -> list[BookingOut]:
    return bookings.list_range(db, user, start, end, room_id)


@router.get("/my")
def my_bookings(user: CurrentUser, db: DB,
                scope: Literal["upcoming", "past", "cancelled"] = "upcoming") -> list[BookingOut]:
    return bookings.list_my(db, user, scope)


@router.get("/{booking_id}")
def get_booking(booking_id: int, user: CurrentUser, db: DB) -> BookingOut:
    return bookings.get(db, user, booking_id)


@router.post("", status_code=201)
def create_booking(body: BookingCreate, user: CurrentUser, db: DB) -> BookingOut:
    return bookings.create(db, user, body)


@router.patch("/{booking_id}")
def update_booking(booking_id: int, body: BookingUpdate, user: CurrentUser, db: DB) -> BookingOut:
    return bookings.update(db, user, booking_id, body)


@router.post("/{booking_id}/cancel")
def cancel_booking(booking_id: int, user: CurrentUser, db: DB) -> BookingOut:
    return bookings.cancel(db, user, booking_id)
