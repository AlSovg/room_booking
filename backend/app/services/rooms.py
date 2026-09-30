from datetime import datetime

from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.errors import AppError
from app.domain import rules
from app.models import Booking, BookingStatus, Equipment, Room
from app.schemas import EquipmentIn, RoomCreate, RoomUpdate


def _commit(db: Session, code: str, message: str) -> None:
    """Коммит; unique_violation (23505) и foreign_key_violation (23503) → 409 с понятным кодом."""
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if e.orig.sqlstate not in ("23505", "23503"):
            raise
        raise AppError(409, code, message) from e


def filtered_rooms(*, min_capacity: int = 1, equipment_ids: list[int] = (), include_inactive: bool = False):
    """Запрос комнат по вместимости и оборудованию (нужны все выбранные позиции)."""
    q = select(Room).where(Room.capacity >= min_capacity)
    if not include_inactive:
        q = q.where(Room.is_active)
    for eid in set(equipment_ids):
        q = q.where(Room.equipment.any(Equipment.id == eid))
    return q


def list_rooms(db: Session, **filters) -> list[Room]:
    q = filtered_rooms(**filters).options(selectinload(Room.equipment)).order_by(Room.name)
    return list(db.scalars(q))


def available_rooms(db: Session, start: datetime, end: datetime, *, min_capacity: int = 1,
                    equipment_ids: list[int] = ()) -> list[Room]:
    """Активные комнаты без активной брони, пересекающей [start, end) (docs/02-design.md, п. 5.4)."""
    rules.check_interval(start, end, settings.tz, settings.work_start, settings.work_end)
    busy = exists().where(Booking.room_id == Room.id, Booking.status == BookingStatus.active,
                          Booking.start_at < end, Booking.end_at > start)
    q = (filtered_rooms(min_capacity=min_capacity, equipment_ids=equipment_ids).where(~busy)
         .options(selectinload(Room.equipment)).order_by(Room.capacity, Room.name))
    return list(db.scalars(q))


def get_room(db: Session, room_id: int) -> Room:
    room = db.get(Room, room_id)
    if room is None:
        raise AppError(404, "NOT_FOUND", "Комната не найдена")
    return room


def _equipment(db: Session, ids: list[int]) -> list[Equipment]:
    items = list(db.scalars(select(Equipment).where(Equipment.id.in_(ids)))) if ids else []
    if len(items) != len(set(ids)):
        raise AppError(404, "NOT_FOUND", "Оборудование не найдено")
    return items


def create_room(db: Session, data: RoomCreate) -> Room:
    room = Room(**data.model_dump(exclude={"equipment_ids"}), equipment=_equipment(db, data.equipment_ids))
    db.add(room)
    _commit(db, "ROOM_NAME_TAKEN", "Комната с таким названием уже есть")
    return room


def update_room(db: Session, room_id: int, data: RoomUpdate) -> Room:
    room = get_room(db, room_id)
    if data.equipment_ids is not None:
        room.equipment = _equipment(db, data.equipment_ids)
    for k, v in data.model_dump(exclude_unset=True, exclude={"equipment_ids"}).items():
        setattr(room, k, v)
    _commit(db, "ROOM_NAME_TAKEN", "Комната с таким названием уже есть")
    return room


def list_equipment(db: Session) -> list[Equipment]:
    return list(db.scalars(select(Equipment).order_by(Equipment.name)))


def _get_equipment(db: Session, equipment_id: int) -> Equipment:
    item = db.get(Equipment, equipment_id)
    if item is None:
        raise AppError(404, "NOT_FOUND", "Оборудование не найдено")
    return item


def create_equipment(db: Session, data: EquipmentIn) -> Equipment:
    item = Equipment(name=data.name)
    db.add(item)
    _commit(db, "EQUIPMENT_NAME_TAKEN", "Такое оборудование уже есть")
    return item


def update_equipment(db: Session, equipment_id: int, data: EquipmentIn) -> Equipment:
    item = _get_equipment(db, equipment_id)
    item.name = data.name
    _commit(db, "EQUIPMENT_NAME_TAKEN", "Такое оборудование уже есть")
    return item


def delete_equipment(db: Session, equipment_id: int) -> None:
    db.delete(_get_equipment(db, equipment_id))
    _commit(db, "EQUIPMENT_IN_USE", "Оборудование используется в комнатах")
