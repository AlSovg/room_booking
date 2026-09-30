from datetime import datetime
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints

from app.models import BookingStatus, NotificationType, UserRole

Email = Annotated[str, StringConstraints(strip_whitespace=True, max_length=254,
                                         pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]
Password = Annotated[str, Field(min_length=8, max_length=128)]
FullName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class LoginIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserCreate(BaseModel):
    full_name: FullName
    email: Email
    role: UserRole = UserRole.employee


class UserUpdate(BaseModel):
    full_name: FullName | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: Password


class UserWithPassword(BaseModel):
    user: UserOut
    temporary_password: str


Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class EquipmentIn(BaseModel):
    name: Name


class EquipmentOut(EquipmentIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class RoomCreate(BaseModel):
    name: Name
    location: str | None = Field(None, max_length=200)
    capacity: int = Field(gt=0, le=1000)
    description: str | None = Field(None, max_length=2000)
    is_active: bool = True
    equipment_ids: list[int] = []


class RoomUpdate(BaseModel):
    name: Name | None = None
    location: str | None = Field(None, max_length=200)
    capacity: int | None = Field(None, gt=0, le=1000)
    description: str | None = Field(None, max_length=2000)
    is_active: bool | None = None
    equipment_ids: list[int] | None = None


class RoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str | None
    capacity: int
    description: str | None
    is_active: bool
    equipment: list[EquipmentOut]


Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class BookingCreate(BaseModel):
    room_id: int
    title: Title
    start_at: AwareDatetime
    end_at: AwareDatetime
    attendees: int = Field(ge=1, le=1000)


class BookingUpdate(BaseModel):
    room_id: int | None = None
    title: Title | None = None
    start_at: AwareDatetime | None = None
    end_at: AwareDatetime | None = None
    attendees: int | None = Field(None, ge=1, le=1000)


class OrganizerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    title: str
    start_at: datetime
    end_at: datetime
    attendees: int
    status: BookingStatus
    organizer: OrganizerOut
    can_edit: bool = False  # считается на сервере для текущего пользователя


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: NotificationType
    booking_id: int | None
    message: str
    is_read: bool
    created_at: datetime


class UnreadCount(BaseModel):
    count: int


class RoomStat(BaseModel):
    room_id: int
    name: str
    bookings: int
    booked_minutes: int
    utilization: float  # занято / доступно (рабочие часы × дни периода)


class PeakCell(BaseModel):
    weekday: int  # ISO: 1 = понедельник
    hour: int
    bookings: int
    booked_minutes: int


class UserStat(BaseModel):
    user_id: int
    full_name: str
    total: int
    active: int
    cancelled: int
    hours: float
    cancel_rate: float


class StatsSummary(BaseModel):
    total: int
    cancelled: int
    cancel_rate: float
    avg_duration_minutes: float
