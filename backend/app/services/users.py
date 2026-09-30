import secrets

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import hash_password, verify_password
from app.models import User, UserRole
from app.schemas import PasswordChange, UserCreate, UserUpdate
from app.services.auth import revoke_all


def _temp_password() -> str:
    return secrets.token_urlsafe(9)


def get(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise AppError(404, "NOT_FOUND", "Пользователь не найден")
    return user


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.full_name)))


def create(db: Session, data: UserCreate) -> tuple[User, str]:
    password = _temp_password()
    user = User(full_name=data.full_name, email=data.email, role=data.role,
                password_hash=hash_password(password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if e.orig.sqlstate != "23505":  # unique_violation по lower(email)
            raise
        raise AppError(409, "EMAIL_TAKEN", "Пользователь с таким email уже есть") from e
    return user, password


def update(db: Session, actor: User, user_id: int, data: UserUpdate) -> User:
    user = get(db, user_id)
    if user.id == actor.id and (data.is_active is False or (data.role and data.role != UserRole.admin)):
        raise AppError(409, "SELF_LOCKOUT", "Нельзя заблокировать или разжаловать самого себя")  # BR-13
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    return user


def reset_password(db: Session, user_id: int) -> tuple[User, str]:
    user = get(db, user_id)
    password = _temp_password()
    user.password_hash = hash_password(password)
    user.failed_attempts, user.locked_until = 0, None
    revoke_all(db, user.id)
    db.commit()
    return user, password


def change_password(db: Session, user: User, data: PasswordChange) -> None:
    if not verify_password(data.old_password, user.password_hash):
        raise AppError(422, "WRONG_PASSWORD", "Текущий пароль указан неверно")
    user.password_hash = hash_password(data.new_password)
    revoke_all(db, user.id)
    db.commit()
