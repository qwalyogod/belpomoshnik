"""Pytest fixtures: isolated temp DB, seeded roles, TestClient, auth tokens.

Env vars set BEFORE importing backend (engine reads them at import time).
"""
import os
import sys
import tempfile
from pathlib import Path

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["BELPOMOSHNIK_DATABASE_URL"] = f"sqlite:///{_tmp.name}"
os.environ["BELPOMOSHNIK_SECRET_KEY"] = "pytest-secret-key-256bit-aaaaaaaaaaaaaaaa"

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.app import app  # noqa: E402
from backend.auth import hash_password  # noqa: E402
from backend.database import SessionLocal, engine  # noqa: E402
from backend.models import Base, Role, User  # noqa: E402
from backend.rate_limit import login_limiter  # noqa: E402

_ROLES = [("citizen", "Гражданин"), ("content_editor", "Редактор"), ("platform_admin", "Администратор")]


@pytest.fixture(autouse=True)
def reset_db():
    """Fresh schema + seeded roles + clean rate limiter before each test."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        for rid, title in _ROLES:
            db.add(Role(id=rid, title=title))
        db.commit()
    finally:
        db.close()
    login_limiter._log.clear()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:  # context manager runs lifespan (scheduler)
        yield c


def _make_user(email: str, password: str, role_id: str, name: str = "User") -> None:
    db = SessionLocal()
    try:
        db.add(User(email=email, hashed_password=hash_password(password), name=name, role_id=role_id))
        db.commit()
    finally:
        db.close()


@pytest.fixture
def citizen_token(client):
    client.post("/api/auth/register", json={"email": "citizen@bel.by", "password": "citizen-pass-1", "name": "Citizen"})
    r = client.post("/api/auth/login", data={"username": "citizen@bel.by", "password": "citizen-pass-1"})
    return r.json()["access_token"]


@pytest.fixture
def editor_token(client):
    _make_user("editor@bel.by", "editor-pass-1", "content_editor", "Editor")
    r = client.post("/api/auth/login", data={"username": "editor@bel.by", "password": "editor-pass-1"})
    return r.json()["access_token"]


@pytest.fixture
def editor_headers(editor_token):
    return {"Authorization": f"Bearer {editor_token}"}


def pytest_sessionfinish(session, exitstatus):
    try:
        os.unlink(_tmp.name)
    except OSError:
        pass
