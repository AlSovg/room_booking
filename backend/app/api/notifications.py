from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import DB, CurrentUser
from app.schemas import NotificationOut, UnreadCount
from app.services import notifications

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
def list_notifications(user: CurrentUser, db: DB, unread_only: bool = False,
                       limit: Annotated[int, Query(ge=1, le=100)] = 20) -> list[NotificationOut]:
    return notifications.list_for(db, user, unread_only, limit)


@router.get("/unread-count")
def unread_count(user: CurrentUser, db: DB) -> UnreadCount:
    return UnreadCount(count=notifications.unread_count(db, user))


@router.post("/read-all", status_code=204)
def read_all(user: CurrentUser, db: DB) -> None:
    notifications.read_all(db, user)


@router.post("/{notification_id}/read")
def mark_read(notification_id: int, user: CurrentUser, db: DB) -> NotificationOut:
    return notifications.mark_read(db, user, notification_id)
