import asyncio
import logging

from app.core.db import SessionLocal
from app.services import notifications

log = logging.getLogger(__name__)
INTERVAL = 30  # секунд; погрешность напоминания до INTERVAL (docs/02-design.md, п. 6)


def _tick() -> None:
    with SessionLocal() as db:
        notifications.remind_due(db)


async def run() -> None:
    while True:
        try:
            await asyncio.to_thread(_tick)
        except Exception:  # тик не должен убивать планировщик
            log.exception("reminder tick failed")
        await asyncio.sleep(INTERVAL)
