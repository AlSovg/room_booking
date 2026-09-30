import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AppError
from app.core.security import (
    create_access_token, create_refresh_token, decode_token, verify_password,
)
from app.models import RefreshToken, User


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _unauthenticated() -> AppError:
    return AppError(401, "UNAUTHENTICATED", "Требуется вход")


def _issue(db: Session, user: User) -> tuple[str, str]:
    """Новая пара (access, refresh); refresh сохраняется в БД для ротации и отзыва."""
    jti = uuid.uuid4()
    db.add(RefreshToken(id=jti, user_id=user.id,
                        expires_at=_now() + timedelta(days=settings.refresh_ttl_days)))
    db.commit()
    return create_access_token(user.id), create_refresh_token(user.id, jti)


def login(db: Session, email: str, password: str) -> tuple[str, str]:
    user = db.scalar(select(User).where(func.lower(User.email) == email.strip().lower()))
    if user is None:
        raise AppError(401, "INVALID_CREDENTIALS", "Неверный email или пароль")

    now = _now()
    if user.locked_until and user.locked_until > now:
        retry = int((user.locked_until - now).total_seconds()) + 1
        raise AppError(429, "TOO_MANY_ATTEMPTS", "Слишком много попыток входа, повторите позже",
                       headers={"Retry-After": str(retry)})

    if not verify_password(password, user.password_hash):
        user.failed_attempts += 1
        if user.failed_attempts >= settings.max_failed_attempts:
            user.failed_attempts = 0
            user.locked_until = now + timedelta(minutes=settings.lockout_minutes)
        db.commit()
        raise AppError(401, "INVALID_CREDENTIALS", "Неверный email или пароль")

    if not user.is_active:
        raise AppError(403, "ACCOUNT_DISABLED", "Пользователь заблокирован")

    user.failed_attempts, user.locked_until = 0, None
    return _issue(db, user)


def refresh(db: Session, token: str | None) -> tuple[str, str]:
    claims = decode_token(token, "refresh") if token else None
    if claims is None:
        raise _unauthenticated()
    row = db.scalar(select(RefreshToken).where(RefreshToken.id == uuid.UUID(claims["jti"]))
                    .with_for_update())
    if row is None or row.revoked_at or row.expires_at <= _now():
        raise _unauthenticated()
    user = db.get(User, row.user_id)
    if user is None or not user.is_active:
        raise AppError(403, "ACCOUNT_DISABLED", "Пользователь заблокирован")
    row.revoked_at = _now()  # ротация: старый токен больше не действует
    return _issue(db, user)


def logout(db: Session, token: str | None) -> None:
    claims = decode_token(token, "refresh") if token else None
    if claims:
        db.execute(update(RefreshToken).where(RefreshToken.id == uuid.UUID(claims["jti"]),
                                              RefreshToken.revoked_at.is_(None))
                   .values(revoked_at=_now()))
        db.commit()


def revoke_all(db: Session, user_id: int) -> None:
    """Отозвать все refresh-токены пользователя (смена/сброс пароля). Коммит — на вызывающем."""
    db.execute(update(RefreshToken).where(RefreshToken.user_id == user_id,
                                          RefreshToken.revoked_at.is_(None))
               .values(revoked_at=_now()))
