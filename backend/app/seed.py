from argon2 import PasswordHasher
from sqlalchemy import select

from app.core.config import settings
from app.core.db import SessionLocal
from app.models import Equipment, Room, User, UserRole

ph = PasswordHasher()

EQUIPMENT = ["Проектор", "Экран", "Маркерная доска", "Видеоконференция", "Телефон"]
ROOMS = [  # (название, местоположение, вместимость, оборудование)
    ("Байкал", "1 этаж", 6, ["Маркерная доска", "Телефон"]),
    ("Волга", "1 этаж", 10, ["Проектор", "Экран", "Маркерная доска"]),
    ("Урал", "2 этаж", 4, ["Маркерная доска"]),
    ("Алтай", "2 этаж", 20, ["Проектор", "Экран", "Видеоконференция"]),
    ("Онега", "3 этаж", 8, ["Проектор", "Видеоконференция"]),
]
EMPLOYEES = [("Иван Петров", "ivan@example.com"), ("Мария Сидорова", "maria@example.com")]
EMPLOYEE_PASSWORD = "employee123"


def seed(db) -> None:
    """Идемпотентно: добавляет только отсутствующее."""
    have = lambda model, col, val: db.scalar(select(model).where(col == val))  # noqa: E731

    if not have(User, User.email, settings.admin_email):
        db.add(User(full_name="Администратор", email=settings.admin_email,
                    password_hash=ph.hash(settings.admin_password), role=UserRole.admin))
    for name, email in EMPLOYEES:
        if not have(User, User.email, email):
            db.add(User(full_name=name, email=email, password_hash=ph.hash(EMPLOYEE_PASSWORD)))

    eq = {n: have(Equipment, Equipment.name, n) or Equipment(name=n) for n in EQUIPMENT}
    db.add_all(eq.values())
    for name, location, capacity, items in ROOMS:
        if not have(Room, Room.name, name):
            db.add(Room(name=name, location=location, capacity=capacity,
                        equipment=[eq[i] for i in items]))
    db.commit()


if __name__ == "__main__":
    with SessionLocal() as db:
        seed(db)
    print("seed ok")
