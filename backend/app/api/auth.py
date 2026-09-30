from typing import Annotated

from fastapi import APIRouter, Cookie, Response

from app.api.deps import DB
from app.core.config import settings
from app.schemas import LoginIn, TokenOut
from app.services import auth

router = APIRouter(prefix="/auth", tags=["auth"])
COOKIE = "refresh_token"


def _respond(response: Response, access: str, refresh: str) -> TokenOut:
    response.set_cookie(COOKIE, refresh, max_age=settings.refresh_ttl_days * 86400, httponly=True,
                        samesite="lax", secure=settings.cookie_secure, path="/api/v1/auth")
    return TokenOut(access_token=access, expires_in=settings.access_ttl_minutes * 60)


@router.post("/login")
def login(body: LoginIn, response: Response, db: DB) -> TokenOut:
    return _respond(response, *auth.login(db, body.email, body.password))


@router.post("/refresh")
def refresh(response: Response, db: DB,
            refresh_token: Annotated[str | None, Cookie(alias=COOKIE)] = None) -> TokenOut:
    return _respond(response, *auth.refresh(db, refresh_token))


@router.post("/logout", status_code=204)
def logout(response: Response, db: DB,
           refresh_token: Annotated[str | None, Cookie(alias=COOKIE)] = None) -> None:
    auth.logout(db, refresh_token)
    response.delete_cookie(COOKIE, path="/api/v1/auth")
