"""Deadline rules create one in-app item and respect preferences."""

from datetime import date, timedelta

from backend.database import SessionLocal
from backend.notifications.rules import generate_document_expiry_notifications, generate_task_due_notifications


def _headers(client, email):
    client.post("/api/auth/register", json={"email": email, "password": "user-pass-1", "name": "Tester"})
    token = client.post("/api/auth/login", data={"username": email, "password": "user-pass-1"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_document_rule_creates_once(client):
    headers = _headers(client, "rule-doc@bel.by")
    expiry = (date.today() + timedelta(days=5)).isoformat()
    client.post("/api/user/documents", headers=headers, json={"title": "Паспорт", "expiry_date": expiry})
    db = SessionLocal()
    try:
        assert generate_document_expiry_notifications(db) == 1
        assert generate_document_expiry_notifications(db) == 0
    finally:
        db.close()
    rows = client.get("/api/user/notifications", headers=headers).json()
    assert len([row for row in rows if row["notification_type"] == "doc_expiry"]) == 1


def test_document_preference_disables_rule(client):
    headers = _headers(client, "rule-disabled@bel.by")
    client.patch("/api/user/settings", headers=headers, json={"notifications": {"doc_expiry_enabled": False}})
    expiry = (date.today() + timedelta(days=5)).isoformat()
    client.post("/api/user/documents", headers=headers, json={"title": "Паспорт", "expiry_date": expiry})
    db = SessionLocal()
    try:
        assert generate_document_expiry_notifications(db) == 0
    finally:
        db.close()


def test_task_rule_links_to_situation(client):
    headers = _headers(client, "rule-task@bel.by")
    due = (date.today() + timedelta(days=3)).isoformat()
    situation = client.post("/api/user/situations", headers=headers, json={
        "title": "Получение документа",
        "tasks": [{"title": "Подать заявление", "due_date": due}],
    }).json()
    db = SessionLocal()
    try:
        assert generate_task_due_notifications(db) == 1
    finally:
        db.close()
    row = next(item for item in client.get("/api/user/notifications", headers=headers).json() if item["notification_type"] == "task_due")
    assert row["route"] == f"/situations/{situation['id']}"
