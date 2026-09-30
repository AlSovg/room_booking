from fastapi import APIRouter

from app.api.deps import DB, CurrentUser
from app.schemas import BookingCreate, BookingOut
from app.services import bookings

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", status_code=201)
def create_booking(body: BookingCreate, user: CurrentUser, db: DB) -> BookingOut:
    return bookings.create(db, user, body)
