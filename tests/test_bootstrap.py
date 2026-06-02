"""Tests for DB-agnostic bootstrap (roles + admin seeding)."""
from sqlalchemy import select

from backend.bootstrap import ensure_admin, seed_roles
from backend.database import SessionLocal
from backend.models import Role, User


class TestSeedRoles:
    def test_roles_present_after_reset(self):
        # reset_db fixture already seeded roles
        db = SessionLocal()
        try:
            ids = {r.id for r in db.scalars(select(Role)).all()}
        finally:
            db.close()
        assert {"citizen", "content_editor", "platform_admin"} <= ids

    def test_seed_roles_idempotent(self):
        db = SessionLocal()
        try:
            added = seed_roles(db)  # already seeded by fixture
            assert added == 0
        finally:
            db.close()


class TestEnsureAdmin:
    def test_creates_platform_admin(self):
        db = SessionLocal()
        try:
            created = ensure_admin(db, "root@bel.by", "root-pass-123")
            assert created is True
            user = db.scalars(select(User).where(User.email == "root@bel.by")).first()
            assert user.role_id == "platform_admin"
        finally:
            db.close()

    def test_admin_idempotent(self):
        db = SessionLocal()
        try:
            ensure_admin(db, "root2@bel.by", "root-pass-123")
            again = ensure_admin(db, "root2@bel.by", "root-pass-123")
            assert again is False
        finally:
            db.close()
