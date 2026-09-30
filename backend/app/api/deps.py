from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AppError
from app.core.security import decode_token
from app.models import User, UserRole

DB = Annotated[Session, Depends(get_db)]
_bearer = HTTPBearer(auto_error=False)


def current_user(db: DB, creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]) -> User:
    claims = decode_token(creds.credentials, "access") if creds else None
    if claims is None:
        raise AppError(401, "UNAUTHENTICATED", "Требуется вход")
    user = db.get(User, int(claims["sub"]))  # из БД на каждый запрос: блокировка действует сразу
    if user is None:
        raise AppError(401, "UNAUTHENTICATED", "Требуется вход")
    if not user.is_active:
        raise AppError(403, "ACCOUNT_DISABLED", "Пользователь заблокирован")
    return user


def require_admin(user: Annotated[User, Depends(current_user)]) -> User:
    if user.role != UserRole.admin:
        raise AppError(403, "FORBIDDEN", "Недостаточно прав")
    return user


CurrentUser = Annotated[User, Depends(current_user)]
AdminUser = Annotated[User, Depends(require_admin)]
