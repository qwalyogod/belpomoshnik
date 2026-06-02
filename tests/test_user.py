"""User profile, settings, personal documents (ownership-isolated)."""
import pytest


def _register_login(client, email: str) -> dict:
    client.post("/api/auth/register", json={"email": email, "password": "user-pass-1", "name": "Tester"})
    r = client.post("/api/auth/login", data={"username": email, "password": "user-pass-1"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def user_headers(client):
    return _register_login(client, "u@bel.by")


class TestProfile:
    def test_get_profile(self, client, user_headers):
        r = client.get("/api/user/profile", headers=user_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["email"] == "u@bel.by"
        assert body["role"] == "citizen"

    def test_update_profile(self, client, user_headers):
        r = client.put(
            "/api/user/profile",
            headers=user_headers,
            json={"city": "Минск", "has_children": True, "interest_tags": ["family", "taxes"]},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["city"] == "Минск"
        assert body["has_children"] is True
        assert body["interest_tags"] == ["family", "taxes"]

    def test_profile_requires_auth(self, client):
        assert client.get("/api/user/profile").status_code == 401


class TestSettings:
    def test_default_empty(self, client, user_headers):
        r = client.get("/api/user/settings", headers=user_headers)
        assert r.status_code == 200
        assert r.json() == {}

    def test_patch_merges(self, client, user_headers):
        client.patch("/api/user/settings", headers=user_headers, json={"dark_theme": True})
        client.patch("/api/user/settings", headers=user_headers, json={"doc_reminder_days": 45})
        r = client.get("/api/user/settings", headers=user_headers)
        body = r.json()
        assert body["dark_theme"] is True
        assert body["doc_reminder_days"] == 45


class TestDocuments:
    def test_crud_lifecycle(self, client, user_headers):
        # create
        r = client.post(
            "/api/user/documents",
            headers=user_headers,
            json={"title": "Паспорт", "doc_type": "passport", "number": "MP1234567", "expiry_date": "2030-01-01"},
        )
        assert r.status_code == 201
        doc_id = r.json()["id"]
        # list
        r = client.get("/api/user/documents", headers=user_headers)
        assert any(d["id"] == doc_id for d in r.json())
        # update
        r = client.put(f"/api/user/documents/{doc_id}", headers=user_headers, json={"comment": "Продлён"})
        assert r.status_code == 200
        assert r.json()["comment"] == "Продлён"
        # delete
        assert client.delete(f"/api/user/documents/{doc_id}", headers=user_headers).status_code == 204
        r = client.get("/api/user/documents", headers=user_headers)
        assert all(d["id"] != doc_id for d in r.json())

    def test_update_missing_404(self, client, user_headers):
        assert client.put("/api/user/documents/999999", headers=user_headers, json={"comment": "x"}).status_code == 404

    def test_ownership_isolation(self, client):
        a = _register_login(client, "owner-a@bel.by")
        b = _register_login(client, "owner-b@bel.by")
        doc_id = client.post("/api/user/documents", headers=a, json={"title": "A-doc"}).json()["id"]
        # B must not see or touch A's document
        assert all(d["id"] != doc_id for d in client.get("/api/user/documents", headers=b).json())
        assert client.put(f"/api/user/documents/{doc_id}", headers=b, json={"comment": "hack"}).status_code == 404
        assert client.delete(f"/api/user/documents/{doc_id}", headers=b).status_code == 404
        # A still owns it
        assert any(d["id"] == doc_id for d in client.get("/api/user/documents", headers=a).json())
