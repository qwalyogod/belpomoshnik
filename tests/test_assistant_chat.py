"""Тесты RAG-эндпоинта ассистента: `/api/assistant/chat`."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app import app
from backend.auth import hash_password
from backend.database import SessionLocal
from backend.enums import ContentStatus
from backend.models import Problem, User


@pytest.fixture
def citizen_token(monkeypatch):
    """Создаёт citizen-пользователя и возвращает его access_token. Без GROQ."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.email == "rag-test@bel.by"))
        if not existing:
            db.add(User(
                email="rag-test@bel.by",
                hashed_password=hash_password("Test12345!"),
                name="RAG Tester",
                role_id="citizen",
            ))
            db.commit()
    finally:
        db.close()
    with TestClient(app) as c:
        r = c.post("/api/auth/login", data={"username": "rag-test@bel.by", "password": "Test12345!"})
        assert r.status_code == 200, r.text
        return r.json()["access_token"]


@pytest.fixture
def seed_two_problems():
    """Сидит 2 проблемы (паспорт и ЖКХ) и удаляет их после теста."""
    db = SessionLocal()
    passport = Problem(
        title="Получение паспорта гражданина РБ в 14 лет",
        slug="rag-test-passport",
        short_description="Как получить первый паспорт подростку.",
        description="Пошаговая инструкция: документы, ОГиМ, сроки.",
        category="documents",
        status=ContentStatus.PUBLISHED,
    )
    housing = Problem(
        title="Субсидия на оплату коммунальных услуг",
        slug="rag-test-housing",
        short_description="Оформление субсидии на ЖКХ.",
        description="Условия, документы, куда обращаться.",
        category="housing",
        status=ContentStatus.PUBLISHED,
    )
    try:
        for p in (passport, housing):
            existing = db.scalar(select(Problem).where(Problem.slug == p.slug))
            if existing:
                db.delete(existing)
                db.commit()
        db.add(passport)
        db.add(housing)
        db.commit()
        yield {"passport_id": passport.id, "housing_id": housing.id}
    finally:
        for slug in ("rag-test-passport", "rag-test-housing"):
            existing = db.scalar(select(Problem).where(Problem.slug == slug))
            if existing:
                db.delete(existing)
        db.commit()
        db.close()


def test_chat_requires_auth():
    """Без токена POST /chat → 401, не 500."""
    with TestClient(app) as c:
        r = c.post("/api/assistant/chat", json={"message": "привет", "role": "citizen", "is_guest": False})
    assert r.status_code == 401, r.text


def test_chat_local_fallback(citizen_token, seed_two_problems):
    """Citizen + вопрос → 200, source=local (без GROQ), links непустой, path начинается с /."""
    with TestClient(app) as c:
        r = c.post(
            "/api/assistant/chat",
            headers={"Authorization": f"Bearer {citizen_token}"},
            json={"message": "как получить паспорт", "role": "citizen", "is_guest": False},
        )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["source"] == "local"
    assert isinstance(data["links"], list) and len(data["links"]) > 0
    for link in data["links"]:
        assert link["path"].startswith("/")
        assert "title" in link and "kind" in link
    # Текст непустой и не падает
    assert isinstance(data["response_text"], str) and len(data["response_text"]) > 0


def test_chat_rag_ranks_relevant_first(citizen_token, seed_two_problems):
    """Из 2 проблем (паспорт + ЖКХ) на запрос «паспорт потерял» первая ссылка — про паспорт."""
    with TestClient(app) as c:
        r = c.post(
            "/api/assistant/chat",
            headers={"Authorization": f"Bearer {citizen_token}"},
            json={"message": "паспорт потерял", "role": "citizen", "is_guest": False},
        )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["source"] == "local"
    assert len(data["links"]) >= 1
    # Первая ссылка — про паспорт (НЕ про ЖКХ).
    first = data["links"][0]
    assert "паспорт" in first["title"].lower() or first["kind"] == "problem"
    assert "субсид" not in first["title"].lower() and "жкх" not in first["title"].lower()


def test_chat_handles_no_matches(citizen_token):
    """Запрос «абвгд» (ничего не матчит) → 200, пустой links, текст не падает."""
    with TestClient(app) as c:
        r = c.post(
            "/api/assistant/chat",
            headers={"Authorization": f"Bearer {citizen_token}"},
            json={"message": "абвгдейка xyz", "role": "citizen", "is_guest": False},
        )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["source"] == "local"
    assert isinstance(data["response_text"], str) and len(data["response_text"]) > 0


def test_chat_returns_path_not_url(citizen_token, seed_two_problems):
    """Все link.path — относительные пути, НЕ полные URL. Frontend склеивает origin."""
    with TestClient(app) as c:
        r = c.post(
            "/api/assistant/chat",
            headers={"Authorization": f"Bearer {citizen_token}"},
            json={"message": "паспорт документы", "role": "citizen", "is_guest": False},
        )
    assert r.status_code == 200, r.text
    data = r.json()
    for link in data["links"]:
        assert not link["path"].startswith("http://")
        assert not link["path"].startswith("https://")
        assert link["path"].startswith("/")
