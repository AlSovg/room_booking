from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DB, CurrentUser, require_admin
from app.schemas import EquipmentIn, EquipmentOut, RoomCreate, RoomOut, RoomUpdate
from app.services import rooms

router = APIRouter(tags=["rooms"])
EquipmentIds = Annotated[list[int], Query()]


@router.get("/rooms")
def list_rooms(db: DB, _: CurrentUser, min_capacity: Annotated[int, Query(ge=1)] = 1,
               equipment_ids: EquipmentIds = [], include_inactive: bool = False) -> list[RoomOut]:
    return rooms.list_rooms(db, min_capacity=min_capacity, equipment_ids=equipment_ids,
                            include_inactive=include_inactive)


@router.get("/rooms/{room_id}")
def get_room(room_id: int, db: DB, _: CurrentUser) -> RoomOut:
    return rooms.get_room(db, room_id)


@router.post("/rooms", status_code=201, dependencies=[Depends(require_admin)])
def create_room(body: RoomCreate, db: DB) -> RoomOut:
    return rooms.create_room(db, body)


@router.patch("/rooms/{room_id}", dependencies=[Depends(require_admin)])
def update_room(room_id: int, body: RoomUpdate, db: DB) -> RoomOut:
    return rooms.update_room(db, room_id, body)


@router.get("/equipment")
def list_equipment(db: DB, _: CurrentUser) -> list[EquipmentOut]:
    return rooms.list_equipment(db)


@router.post("/equipment", status_code=201, dependencies=[Depends(require_admin)])
def create_equipment(body: EquipmentIn, db: DB) -> EquipmentOut:
    return rooms.create_equipment(db, body)


@router.patch("/equipment/{equipment_id}", dependencies=[Depends(require_admin)])
def update_equipment(equipment_id: int, body: EquipmentIn, db: DB) -> EquipmentOut:
    return rooms.update_equipment(db, equipment_id, body)


@router.delete("/equipment/{equipment_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_equipment(equipment_id: int, db: DB) -> None:
    rooms.delete_equipment(db, equipment_id)
