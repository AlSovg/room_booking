from fastapi import APIRouter, FastAPI

from app.api import auth, users
from app.core.errors import register_error_handlers

app = FastAPI(title="Room Booking")
register_error_handlers(app)

api = APIRouter(prefix="/api/v1")
api.include_router(auth.router)
api.include_router(users.router)


@api.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}


app.include_router(api)
