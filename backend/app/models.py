import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Identity,
    Index, Integer, Text, func, text,
)
from sqlalchemy.dialects.postgresql import ExcludeConstraint, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

TZ = DateTime(timezone=True)  # всегда timestamptz, иначе SQLAlchemy создаст WITHOUT TIME ZONE
ID = BigInteger


class UserRole(enum.StrEnum):
    employee = "employee"
    admin = "admin"


class BookingStatus(enum.StrEnum):
    active = "active"
    cancelled = "cancelled"


class NotificationType(enum.StrEnum):
    reminder = "reminder"
    changed = "changed"
    cancelled = "cancelled"


class Base(DeclarativeBase):
    pass


def pk() -> Mapped[int]:
    return mapped_column(ID, Identity(always=True), primary_key=True)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(full_name) BETWEEN 1 AND 200", name="ck_users_full_name"),
        Index("users_email_uq", func.lower(text("email")), unique=True),
    )

    id: Mapped[int] = pk()
    full_name: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(Text)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), server_default="employee")
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    failed_attempts: Mapped[int] = mapped_column(Integer, server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(TZ)
    created_at: Mapped[datetime] = mapped_column(TZ, server_default=func.now())


class RoomEquipment(Base):
    __tablename__ = "room_equipment"

    room_id: Mapped[int] = mapped_column(ID, ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True)
    equipment_id: Mapped[int] = mapped_column(ID, ForeignKey("equipment.id", ondelete="RESTRICT"), primary_key=True)


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[int] = pk()
    name: Mapped[str] = mapped_column(Text, unique=True)


class Room(Base):
    __tablename__ = "rooms"
    __table_args__ = (CheckConstraint("capacity > 0", name="ck_rooms_capacity"),)

    id: Mapped[int] = pk()
    name: Mapped[str] = mapped_column(Text, unique=True)
    location: Mapped[str | None] = mapped_column(Text)
    capacity: Mapped[int] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))

    equipment: Mapped[list[Equipment]] = relationship(secondary="room_equipment")


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("length(title) BETWEEN 1 AND 200", name="ck_bookings_title"),
        CheckConstraint("attendees >= 1", name="ck_bookings_attendees"),
        CheckConstraint("start_at < end_at", name="ck_bookings_order"),
        CheckConstraint(
            "end_at - start_at BETWEEN interval '15 minutes' AND interval '8 hours'",
            name="ck_bookings_duration",
        ),
        CheckConstraint(
            "extract(epoch FROM start_at)::bigint % 900 = 0 AND extract(epoch FROM end_at)::bigint % 900 = 0",
            name="ck_bookings_aligned",
        ),
        ExcludeConstraint(
            ("room_id", "="),
            (func.tstzrange(text("start_at"), text("end_at"), "[)"), "&&"),
            where=text("status = 'active'"),
            name="bookings_no_overlap",
            using="gist",
        ),
        Index("bookings_organizer_idx", "organizer_id", text("start_at DESC")),
        Index("bookings_start_idx", "start_at", postgresql_where=text("status = 'active'")),
    )

    id: Mapped[int] = pk()
    room_id: Mapped[int] = mapped_column(ID, ForeignKey("rooms.id"))
    organizer_id: Mapped[int] = mapped_column(ID, ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(Text)
    attendees: Mapped[int] = mapped_column(Integer)
    start_at: Mapped[datetime] = mapped_column(TZ)
    end_at: Mapped[datetime] = mapped_column(TZ)
    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus, name="booking_status"), server_default="active")
    cancelled_by: Mapped[int | None] = mapped_column(ID, ForeignKey("users.id"))
    cancelled_at: Mapped[datetime | None] = mapped_column(TZ)
    created_at: Mapped[datetime] = mapped_column(TZ, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TZ, server_default=func.now(), onupdate=func.now())

    organizer: Mapped[User] = relationship(foreign_keys=[organizer_id], lazy="joined")


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("notifications_user_idx", "user_id", text("created_at DESC")),)

    id: Mapped[int] = pk()
    user_id: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType, name="notification_type"))
    booking_id: Mapped[int | None] = mapped_column(ID, ForeignKey("bookings.id", ondelete="SET NULL"))
    message: Mapped[str] = mapped_column(Text)
    dedupe_key: Mapped[str | None] = mapped_column(Text, unique=True)
    is_read: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(TZ, server_default=func.now())


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime] = mapped_column(TZ)
    revoked_at: Mapped[datetime | None] = mapped_column(TZ)
