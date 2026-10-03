from datetime import datetime, timezone

from sqlalchemy import select

from app.models import BookingStatus, Notification
from app.services.notifications import remind_due
from tests.conftest import ADMIN, EMPLOYEE, auth
from tests.test_bookings import API, create, insert, patch, room  # noqa: F401


def mine(client, h, **params):
    return client.get(f"{API}/notifications", headers=h, params=params).json()


def test_changed_and_cancelled_by_admin_notify_owner_but_own_actions_do_not(client, room):
    emp, adm = auth(client, EMPLOYEE), auth(client, ADMIN)
    b = create(client, emp, room).json()
    patch(client, emp, b["id"], title="Сам")  # BR-12: свои действия молчат
    assert mine(client, emp) == []
    patch(client, adm, b["id"], title="Админ")
    client.post(f"{API}/bookings/{b['id']}/cancel", headers=adm)
    got = mine(client, emp)
    assert [n["type"] for n in got] == ["cancelled", "changed"] and "Волга" in got[0]["message"]
    assert got[0]["params"]["room"] and got[0]["params"]["actor"] and got[0]["params"]["start"]
    assert mine(client, adm) == []

    assert client.get(f"{API}/notifications/unread-count", headers=emp).json() == {"count": 2}
    assert client.post(f"{API}/notifications/{got[0]['id']}/read", headers=emp).json()["is_read"] is True
    assert client.post(f"{API}/notifications/{got[1]['id']}/read", headers=adm).status_code == 404  # чужое
    assert len(mine(client, emp, unread_only=True)) == 1
    assert client.post(f"{API}/notifications/read-all", headers=emp).status_code == 204
    assert client.get(f"{API}/notifications/unread-count", headers=emp).json() == {"count": 0}


def test_reminder_once_only_for_active_upcoming(client, db, room):
    soon = insert(db, room, EMPLOYEE[0], 15, 30)  # начало в пределах ближайших 15 минут
    far = insert(db, room, EMPLOYEE[0], 600, 615)
    gone = insert(db, room, EMPLOYEE[0], 30, 45)
    gone.status, gone.cancelled_by, gone.cancelled_at = BookingStatus.cancelled, gone.organizer_id, datetime.now(timezone.utc)
    db.flush()

    assert remind_due(db) == 1 and remind_due(db) == 0  # без дублей
    n = db.scalars(select(Notification).where(Notification.type == "reminder")).one()
    assert n.booking_id == soon.id and n.user_id == soon.organizer_id and far.id != n.booking_id
