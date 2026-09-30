from fastapi import APIRouter, Depends

from app.api.deps import DB, AdminUser, CurrentUser, require_admin
from app.schemas import PasswordChange, UserCreate, UserOut, UserUpdate, UserWithPassword
from app.services import users

router = APIRouter(tags=["users"])


@router.get("/me")
def me(user: CurrentUser) -> UserOut:
    return user


@router.post("/me/password", status_code=204)
def change_password(body: PasswordChange, user: CurrentUser, db: DB) -> None:
    users.change_password(db, user, body)


admin = APIRouter(prefix="/users", dependencies=[Depends(require_admin)])


@admin.get("")
def list_users(db: DB) -> list[UserOut]:
    return users.list_users(db)


@admin.post("", status_code=201)
def create_user(body: UserCreate, db: DB) -> UserWithPassword:
    user, password = users.create(db, body)
    return UserWithPassword(user=user, temporary_password=password)


@admin.patch("/{user_id}")
def update_user(user_id: int, body: UserUpdate, actor: AdminUser, db: DB) -> UserOut:
    return users.update(db, actor, user_id, body)


@admin.post("/{user_id}/reset-password")
def reset_password(user_id: int, db: DB) -> UserWithPassword:
    user, password = users.reset_password(db, user_id)
    return UserWithPassword(user=user, temporary_password=password)


router.include_router(admin)
