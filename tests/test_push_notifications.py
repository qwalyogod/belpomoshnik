"""Native push token ownership, safety and graceful no-credentials mode."""

from backend.notifications.service import safe_push_payload


def _headers(client, email):
    client.post("/api/auth/register", json={"email": email, "password": "user-pass-1", "name": "Tester"})
    token = client.post("/api/auth/login", data={"username": email, "password": "user-pass-1"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_token_is_idempotent_and_masked(client):
    headers = _headers(client, "push@bel.by")
    payload = {"token": "native-device-token-1234567890", "platform": "ios", "device_label": "iPhone"}
    first = client.post("/api/user/push/native-token", headers=headers, json=payload)
    second = client.post("/api/user/push/native-token", headers=headers, json=payload)
    assert first.status_code == 201
    assert second.status_code == 201
    status = client.get("/api/user/push/status", headers=headers).json()
    assert status["registered"] is True
    assert len(status["tokens"]) == 1
    assert "native-device-token" not in str(status)
    assert status["tokens"][0]["token_masked"].startswith("••••")


def test_user_cannot_see_other_users_tokens(client):
    owner = _headers(client, "push-owner@bel.by")
    stranger = _headers(client, "push-stranger@bel.by")
    client.post("/api/user/push/native-token", headers=owner, json={"token": "owner-native-token-123456", "platform": "android"})
    other_status = client.get("/api/user/push/status", headers=stranger).json()
    assert other_status["registered"] is False
    assert other_status["tokens"] == []


def test_no_credentials_returns_skipped_not_error(client, monkeypatch):
    for key in ("FCM_SERVER_KEY", "FCM_CREDENTIALS_JSON", "APNS_KEY_PATH"):
        monkeypatch.delenv(key, raising=False)
    headers = _headers(client, "push-skipped@bel.by")
    client.patch("/api/user/settings", headers=headers, json={"notifications": {
        "system_notifications_enabled": True,
        "native_push_enabled": True,
        "security_enabled": True,
    }})
    client.post("/api/user/push/native-token", headers=headers, json={"token": "native-token-no-credentials-123", "platform": "android"})
    result = client.post("/api/user/push/test", headers=headers)
    assert result.status_code == 200
    assert result.json()["in_app_created"] is True
    assert result.json()["system_delivered"] is False
    assert result.json()["reason"] == "credentials_not_configured"
    assert result.json()["native_push_ready"] is False


def test_safe_payload_excludes_personal_data():
    class Notification:
        id = "n1"
        notification_type = "doc_expiry"
        route = "/documents"
        title = "Паспорт MP1234567"
        description = "Адрес и номер документа"

    payload = safe_push_payload(Notification())
    serialized = str(payload)
    assert "MP1234567" not in serialized
    assert "Адрес" not in serialized
    assert payload["body"] == "У вас есть новое уведомление"
