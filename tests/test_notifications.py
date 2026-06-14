"""In-app notification center and deduplication."""


def _headers(client, email="notifications@bel.by"):
    client.post("/api/auth/register", json={"email": email, "password": "user-pass-1", "name": "Tester"})
    token = client.post("/api/auth/login", data={"username": email, "password": "user-pass-1"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_in_app_notification_is_always_created(client):
    headers = _headers(client)
    result = client.post("/api/user/push/test", headers=headers)
    assert result.status_code == 200
    assert result.json()["in_app_created"] is True
    assert result.json()["system_delivered"] is False
    assert result.json()["reason"] == "permission_not_granted"
    assert any(item["title"] == "Тестовое уведомление" for item in client.get("/api/user/notifications", headers=headers).json())


def test_dedupe_key_returns_existing_notification(client):
    headers = _headers(client, "dedupe@bel.by")
    payload = {"title": "Один раз", "dedupe_key": "same-event", "route": "/documents"}
    first = client.post("/api/user/notifications", headers=headers, json=payload)
    second = client.post("/api/user/notifications", headers=headers, json=payload)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    rows = client.get("/api/user/notifications", headers=headers).json()
    assert len([row for row in rows if row["dedupe_key"] == "same-event"]) == 1


def test_read_delete_and_owner_isolation(client):
    owner = _headers(client, "notification-owner@bel.by")
    stranger = _headers(client, "notification-stranger@bel.by")
    item = client.post("/api/user/notifications", headers=owner, json={"title": "Личное"}).json()
    assert all(row["id"] != item["id"] for row in client.get("/api/user/notifications", headers=stranger).json())
    assert client.patch(f"/api/user/notifications/{item['id']}/read", headers=stranger).status_code == 404
    assert client.delete(f"/api/user/notifications/{item['id']}", headers=owner).status_code == 204
