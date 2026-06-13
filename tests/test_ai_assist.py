"""Тесты AI content-ассистента: без GROQ_API_KEY возвращается fallback (не 500)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.auth import hash_password
from backend.database import SessionLocal
from backend.models import User


@pytest.fixture
def editor_token(monkeypatch):
    """Создаёт редактора и возвращает его access_token. Без GROQ_API_KEY."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    db = SessionLocal()
    try:
        from sqlalchemy import select
        existing = db.scalar(select(User).where(User.email == "ai-test@bel.by"))
        if not existing:
            db.add(User(
                email="ai-test@bel.by",
                hashed_password=hash_password("Test12345!"),
                name="AI Tester",
                role_id="content_editor",
            ))
            db.commit()
    finally:
        db.close()
    with TestClient(app) as c:
        r = c.post("/api/auth/login", data={"username": "ai-test@bel.by", "password": "Test12345!"})
        assert r.status_code == 200, r.text
        return r.json()["access_token"]


def test_ai_assist_generate_fallback(editor_token):
    """Без GROQ_API_KEY: fallback на локальный canned-текст."""
    with TestClient(app) as c:
        r = c.post(
            "/api/admin/assistant/content",
            headers={"Authorization": f"Bearer {editor_token}"},
            json={
                "mode": "generate",
                "kind": "news",
                "current_title": "Тестовая новость",
                "current_summary": "",
                "current_body_html": "",
                "hint": "Электронные рецепты в Беларуси с 1 июля 2026 года.",
            },
        )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["title"] == "Тестовая новость"
    assert "Электронные рецепты" in data["body_html"] or "Электронные рецепты" in data["summary"]
    assert data["source"] in ("llm", "local")


def test_ai_assist_rewrite_preserves_input(editor_token):
    """Без LLM: rewrite возвращает fallback с sanitized HTML."""
    with TestClient(app) as c:
        r = c.post(
            "/api/admin/assistant/content",
            headers={"Authorization": f"Bearer {editor_token}"},
            json={
                "mode": "rewrite",
                "kind": "news",
                "current_title": "Заголовок",
                "current_summary": "Краткое описание",
                "current_body_html": "<p>Привет, <script>alert(1)</script>мир!</p>",
            },
        )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "script" not in data["body_html"].lower()
    assert data["summary"] == "Краткое описание"


def test_ai_assist_requires_editor_role():
    """Гость/без токена: 401/403."""
    with TestClient(app) as c:
        r = c.post(
            "/api/admin/assistant/content",
            json={"mode": "generate", "kind": "news", "current_title": "x", "current_summary": "", "current_body_html": ""},
        )
    assert r.status_code in (401, 403)


def test_ai_assist_translate_fallback(editor_token):
    """Без GROQ: translate возвращает оригинал + пометку о недоступности перевода."""
    with TestClient(app) as c:
        r = c.post(
            "/api/admin/assistant/content",
            headers={"Authorization": f"Bearer {editor_token}"},
            json={
                "mode": "translate",
                "kind": "news",
                "current_title": "Заголовок",
                "current_summary": "Краткое описание",
                "current_body_html": "<p>Привет, мир!</p>",
            },
        )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "Привет, мир!" in data["body_html"]
    assert "script" not in data["body_html"].lower()
    assert "iframe" not in data["body_html"].lower()
    assert data["source"] in ("llm", "local")
    assert data["summary"] == "Краткое описание"
