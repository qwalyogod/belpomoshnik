"""
DB-agnostic bootstrap — работает на SQLite (dev) и PostgreSQL (production).

В отличие от scripts/migrate.py (raw sqlite3 + .sql, только SQLite),
здесь схема создаётся через SQLAlchemy Base.metadata.create_all, поэтому
DDL генерируется под нужный диалект автоматически.

Использование:
    # SQLite (dev) или PostgreSQL (prod) — одинаково:
    BELPOMOSHNIK_DATABASE_URL=postgresql+psycopg://user:pass@host/db \
        python -m backend.bootstrap

    # с созданием администратора:
    BELPOMOSHNIK_ADMIN_EMAIL=admin@bel.by \
    BELPOMOSHNIK_ADMIN_PASSWORD=changeme123 \
        python -m backend.bootstrap
"""
from __future__ import annotations

import os

from sqlalchemy.orm import Session

from backend.auth import hash_password
from backend.database import SessionLocal, engine
from backend.models import Base, Role, User

ROLES: list[tuple[str, str, str]] = [
    ("citizen", "Гражданин", "Обычный пользователь приложения"),
    ("content_editor", "Редактор", "Управление сценариями и контентом"),
    ("platform_admin", "Администратор", "Полный доступ к платформе"),
]


def seed_roles(db: Session) -> int:
    """Создать роли, если их нет. Возвращает число добавленных."""
    added = 0
    for rid, title, description in ROLES:
        if not db.get(Role, rid):
            db.add(Role(id=rid, title=title, description=description))
            added += 1
    db.commit()
    return added


def ensure_admin(db: Session, email: str, password: str, name: str = "Администратор") -> bool:
    """Создать platform_admin, если пользователя с таким email нет."""
    from sqlalchemy import select

    if db.scalars(select(User).where(User.email == email)).first():
        return False
    db.add(User(email=email, hashed_password=hash_password(password), name=name, role_id="platform_admin"))
    db.commit()
    return True


TEST_ACCOUNTS: list[tuple[str, str, str, str]] = [
    # (email, name, role_id, password)
    ("citizen@test.local", "Тестовый гражданин", "citizen", "Test12345!"),
    ("editor@test.local", "Тестовый редактор", "content_editor", "Test12345!"),
    ("admin@test.local", "Тестовый администратор", "platform_admin", "Test12345!"),
]


def seed_test_accounts(db: Session) -> int:
    """Создать тестовые аккаунты для UI-переключателя. Идемпотентно."""
    from sqlalchemy import select

    added = 0
    for email, name, role_id, password in TEST_ACCOUNTS:
        existing = db.scalars(select(User).where(User.email == email)).first()
        if existing:
            # Гарантируем флаг + актуальную роль (на случай переезда между БД)
            if not existing.is_test_account or existing.role_id != role_id:
                existing.is_test_account = True
                existing.role_id = role_id
                db.commit()
            continue
        db.add(User(
            email=email,
            hashed_password=hash_password(password),
            name=name,
            role_id=role_id,
            is_test_account=True,
        ))
        added += 1
    db.commit()
    return added


def bootstrap_database() -> None:
    """Создать схему + роли + тестовые аккаунты (+ опционально админа из env). Идемпотентно."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        added_roles = seed_roles(db)
        print(f"[bootstrap] схема создана; ролей добавлено: {added_roles}")
        added_test = seed_test_accounts(db)
        print(f"[bootstrap] тестовых аккаунтов добавлено: {added_test}")
        admin_email = os.getenv("BELPOMOSHNIK_ADMIN_EMAIL")
        admin_password = os.getenv("BELPOMOSHNIK_ADMIN_PASSWORD")
        if admin_email and admin_password:
            created = ensure_admin(db, admin_email, admin_password)
            print(f"[bootstrap] админ {admin_email}: {'создан' if created else 'уже существует'}")
    finally:
        db.close()
    print(f"[bootstrap] готово. URL диалект: {engine.dialect.name}")


if __name__ == "__main__":
    bootstrap_database()
