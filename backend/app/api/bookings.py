from fastapi import APIRouter

from app.api.deps import DB, CurrentUser
from app.schemas import BookingCreate, BookingOut, BookingUpdate
from app.services import bookings

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", status_code=201)
def create_booking(body: BookingCreate, user: CurrentUser, db: DB) -> BookingOut:
    return bookings.create(db, user, body)


@router.patch("/{booking_id}")
def update_booking(booking_id: int, body: BookingUpdate, user: CurrentUser, db: DB) -> BookingOut:
    return bookings.update(db, user, booking_id, body)


@router.post("/{booking_id}/cancel")
def cancel_booking(booking_id: int, user: CurrentUser, db: DB) -> BookingOut:
    return bookings.cancel(db, user, booking_id)
