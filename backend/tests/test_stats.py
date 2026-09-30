from tests.conftest import ADMIN, EMPLOYEE, auth
from tests.test_bookings import API, create, room  # noqa: F401

DAY = {"from": "2030-01-15", "to": "2030-01-15"}  # вторник


def get(client, h, path, **params):
    return client.get(f"{API}/stats/{path}", headers=h, params={**DAY, **params})


def test_stats_numbers_csv_and_access(client, room):
    emp, adm = auth(client, EMPLOYEE), auth(client, ADMIN)
    create(client, emp, room, "08:00", "14:00")  # AC-16: 6 ч из 12
    gone = create(client, emp, room, "15:00", "15:30").json()
    client.post(f"{API}/bookings/{gone['id']}/cancel", headers=emp)

    rooms = {x["name"]: x for x in get(client, adm, "rooms").json()}
    r = rooms.pop("Волга")
    assert r["bookings"] == 1 and r["booked_minutes"] == 360 and r["utilization"] == 0.5
    assert rooms and all(x["booked_minutes"] == 0 and x["utilization"] == 0 for x in rooms.values())  # без броней — ноль

    peaks = {(c["weekday"], c["hour"]): c["booked_minutes"] for c in get(client, adm, "peak-hours").json()}
    assert peaks[(2, 8)] == 60 and peaks[(2, 13)] == 60 and (2, 14) not in peaks and len(peaks) == 6

    u = get(client, adm, "users").json()[0]
    assert (u["total"], u["active"], u["cancelled"], u["hours"], u["cancel_rate"]) == (2, 1, 1, 6.0, 0.5)
    assert get(client, adm, "summary").json() == {"total": 2, "cancelled": 1, "cancel_rate": 0.5,
                                                  "avg_duration_minutes": 360.0}

    csv = get(client, adm, "rooms", format="csv")
    assert csv.headers["content-type"].startswith("text/csv") and csv.text.startswith("﻿room_id;name;")
    assert get(client, emp, "summary").status_code == 403  # AC-15
    assert get(client, adm, "summary", **{"to": "2029-01-01"}).status_code == 422
