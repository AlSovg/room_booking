import asyncio
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse

from app import scheduler
from app.api import auth, bookings, notifications, rooms, stats, users
from app.core.config import settings
from app.core.errors import register_error_handlers

@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(scheduler.run()) if settings.scheduler_enabled else None
    yield
    if task:
        task.cancel()


app = FastAPI(title="Room Booking", lifespan=lifespan)
register_error_handlers(app)

api = APIRouter(prefix="/api/v1")
api.include_router(auth.router)
api.include_router(users.router)
api.include_router(rooms.router)
api.include_router(bookings.router)
api.include_router(notifications.router)
api.include_router(stats.router)


@api.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}


app.include_router(api)

if settings.static_dir:  # прод-образ: SPA раздаётся тем же процессом
    static = Path(settings.static_dir)

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        file = (static / path).resolve()
        if file.is_file() and static.resolve() in file.parents:
            return FileResponse(file)
        return FileResponse(static / "index.html")
