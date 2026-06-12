"""Pytest fixtures: изолированная MySQL-БД `belpomoshnik_test`, роли, TestClient, токены.

Используется отдельная БД `belpomoshnik_test` в том же MySQL, что и dev-сборка.
Между тестами схема дропается и пересоздаётся (`Base.metadata.drop_all/create_all`),
так что .sql-миграции в тестах не гоняются — у ORM и миграций DDL должен совпадать.

Env vars выставляются ДО импорта backend.* (engine читает URL один раз).
"""
import os
import sys
from pathlib import Path

# Можно переопределить через BELPOMOSHNIK_TEST_DATABASE_URL.
# По умолчанию — отдельная БД `belpomoshnik_test` рядом с `belpomoshnik`.
_DEFAULT_TEST_URL = "mysql+pymysql://root:belp_root@127.0.0.1:3306/belpomoshnik_test?charset=utf8mb4"
os.environ["BELPOMOSHNIK_DATABASE_URL"] = os.environ.get(
    "BELPOMOSHNIK_TEST_DATABASE_URL", _DEFAULT_TEST_URL
)
os.environ["BELPOMOSHNIK_SECRET_KEY"] = "pytest-secret-key-256bit-aaaaaaaaaaaaaaaa"

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

# Создаём БД `belpomoshnik_test` если её нет (MySQL не умеет в `CREATE DATABASE IF NOT EXISTS`
# через SQLAlchemy URL — нужно коннектиться без указания database).
import pymysql  # noqa: E402
from urllib.parse import urlparse  # noqa: E402

from backend.config import get_database_url  # noqa: E402

_parsed = urlparse(get_database_url().replace("mysql+pymysql://", "mysql://", 1))
_admin_conn = pymysql.connect(
    host=_parsed.hostname,
    port=_parsed.port or 3306,
    user=_parsed.username or "root",
    password=_parsed.password or "",
    charset="utf8mb4",
)
try:
    with _admin_conn.cursor() as cur:
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{_parsed.path.lstrip('/').split('?')[0]}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
    _admin_conn.commit()
finally:
    _admin_conn.close()

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.app import app  # noqa: E402
from backend.auth import hash_password  # noqa: E402
from backend.bootstrap import seed_roles  # noqa: E402
from backend.database import SessionLocal, engine  # noqa: E402
from backend.models import Base, User  # noqa: E402
from backend.rate_limit import login_limiter  # noqa: E402


@pytest.fixture(autouse=True)
def reset_db():
    """Fresh schema + seeded roles + clean rate limiter before each test."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        seed_roles(db)
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
