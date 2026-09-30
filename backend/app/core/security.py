import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import settings

_ph = PasswordHasher()
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _ph.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def _encode(sub: int, kind: str, ttl: timedelta, jti: uuid.UUID | None = None) -> str:
    now = datetime.now(timezone.utc)
    claims = {"sub": str(sub), "type": kind, "iat": now, "exp": now + ttl}
    if jti:
        claims["jti"] = str(jti)
    return jwt.encode(claims, settings.jwt_secret, ALGORITHM)


def create_access_token(user_id: int) -> str:
    return _encode(user_id, "access", timedelta(minutes=settings.access_ttl_minutes))


def create_refresh_token(user_id: int, jti: uuid.UUID) -> str:
    return _encode(user_id, "refresh", timedelta(days=settings.refresh_ttl_days), jti)


def decode_token(token: str, kind: str) -> dict | None:
    """Claims токена нужного типа или None, если подпись/срок/тип не подходят."""
    try:
        claims = jwt.decode(token, settings.jwt_secret, [ALGORITHM], options={"require": ["exp", "sub"]})
    except jwt.PyJWTError:
        return None
    return claims if claims.get("type") == kind else None
