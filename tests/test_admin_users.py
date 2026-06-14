"""Prompt 7: управление пользователями и ролями в админке."""


def _register(client, email="user@bel.by", password="user-pass-1", name="Пользователь"):
    r = client.post("/api/auth/register", json={"email": email, "password": password, "name": name})
    assert r.status_code == 201
    return r.json()


def _user_id(client, admin_headers, email):
    users = client.get("/api/admin/users", headers=admin_headers, params={"search": email}).json()
    assert users
    return users[0]["id"]


def test_citizen_has_no_admin_access(client, citizen_token):
    h = {"Authorization": f"Bearer {citizen_token}"}
    r = client.get("/api/admin/dashboard/stats", headers=h)
    assert r.status_code == 403


def test_editor_cannot_manage_users(client, editor_headers, admin_headers):
    _register(client)
    uid = _user_id(client, admin_headers, "user@bel.by")

    assert client.get("/api/admin/users", headers=editor_headers).status_code == 403
    assert client.patch("/api/admin/users/%s/role" % uid, headers=editor_headers, json={"role": "content_editor"}).status_code == 403
    assert client.patch("/api/admin/users/%s/active" % uid, headers=editor_headers, json={"is_active": False}).status_code == 403
    assert client.delete("/api/admin/users/%s" % uid, headers=editor_headers).status_code == 403


def test_admin_lists_filters_and_changes_role(client, admin_headers):
    _register(client, email="role-target@bel.by", name="Role Target")
    uid = _user_id(client, admin_headers, "role-target@bel.by")

    filtered = client.get("/api/admin/users", headers=admin_headers, params={"search": "role-target", "limit": 1}).json()
    assert len(filtered) == 1
    assert filtered[0]["email"] == "role-target@bel.by"

    r = client.patch(f"/api/admin/users/{uid}/role", headers=admin_headers, json={"role": "content_editor"})
    assert r.status_code == 200
    assert r.json()["role_id"] == "content_editor"
    assert r.json()["situations_count"] == 0
    assert r.json()["documents_count"] == 0

    logs = client.get("/api/admin/audit-logs", headers=admin_headers, params={"entity_type": "user"}).json()
    assert any(log["event_type"] == "role_change" for log in logs)


def test_admin_block_unblock_and_soft_delete(client, admin_headers):
    _register(client, email="block-me@bel.by", password="block-pass-1")
    uid = _user_id(client, admin_headers, "block-me@bel.by")

    r = client.patch(f"/api/admin/users/{uid}/active", headers=admin_headers, json={"is_active": False})
    assert r.status_code == 200
    assert r.json()["is_active"] is False
    login = client.post("/api/auth/login", data={"username": "block-me@bel.by", "password": "block-pass-1"})
    assert login.status_code == 401

    r = client.patch(f"/api/admin/users/{uid}/active", headers=admin_headers, json={"is_active": True})
    assert r.status_code == 200
    assert r.json()["is_active"] is True

    assert client.delete(f"/api/admin/users/{uid}", headers=admin_headers).status_code == 204
    users = client.get("/api/admin/users", headers=admin_headers, params={"search": "block-me@bel.by"}).json()
    assert users[0]["is_active"] is False


def test_admin_self_protection(client, admin_headers):
    admin = client.get("/api/admin/users", headers=admin_headers, params={"search": "admin@bel.by"}).json()[0]
    uid = admin["id"]

    assert client.patch(f"/api/admin/users/{uid}/role", headers=admin_headers, json={"role": "citizen"}).status_code == 400
    assert client.patch(f"/api/admin/users/{uid}/active", headers=admin_headers, json={"is_active": False}).status_code == 400
    assert client.delete(f"/api/admin/users/{uid}", headers=admin_headers).status_code == 400


def test_admin_can_create_user_notification(client, admin_headers):
    _register(client, email="notify@bel.by")
    uid = _user_id(client, admin_headers, "notify@bel.by")

    r = client.post(
        f"/api/admin/users/{uid}/notifications",
        headers=admin_headers,
        json={"title": "Проверка", "description": "Сообщение от администратора", "notification_type": "system"},
    )
    assert r.status_code == 200
    assert r.json()["notifications_count"] == 1
