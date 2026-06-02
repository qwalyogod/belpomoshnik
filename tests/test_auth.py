"""Auth endpoint tests: register, login, RBAC, refresh, rate limiting."""


class TestRegister:
    def test_register_returns_tokens(self, client):
        r = client.post("/api/auth/register", json={"email": "new@bel.by", "password": "pass-12345", "name": "New"})
        assert r.status_code == 201
        body = r.json()
        assert body["access_token"] and body["refresh_token"]

    def test_duplicate_email_conflict(self, client):
        payload = {"email": "dup@bel.by", "password": "pass-12345", "name": "Dup"}
        client.post("/api/auth/register", json=payload)
        r = client.post("/api/auth/register", json=payload)
        assert r.status_code == 409

    def test_short_password_rejected(self, client):
        r = client.post("/api/auth/register", json={"email": "x@bel.by", "password": "short", "name": "Xenia"})
        assert r.status_code == 422  # pydantic min_length=8


class TestLogin:
    def test_login_success(self, client):
        client.post("/api/auth/register", json={"email": "a@bel.by", "password": "pass-12345", "name": "Alice"})
        r = client.post("/api/auth/login", data={"username": "a@bel.by", "password": "pass-12345"})
        assert r.status_code == 200
        assert r.json()["access_token"]

    def test_login_wrong_password(self, client):
        client.post("/api/auth/register", json={"email": "b@bel.by", "password": "pass-12345", "name": "Bob"})
        r = client.post("/api/auth/login", data={"username": "b@bel.by", "password": "WRONG"})
        assert r.status_code == 401

    def test_login_unknown_user(self, client):
        r = client.post("/api/auth/login", data={"username": "ghost@bel.by", "password": "whatever1"})
        assert r.status_code == 401


class TestMe:
    def test_me_returns_citizen(self, client, citizen_token):
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {citizen_token}"})
        assert r.status_code == 200
        assert r.json()["role"] == "citizen"

    def test_me_no_token(self, client):
        assert client.get("/api/auth/me").status_code == 401


class TestRBAC:
    def test_citizen_denied_admin(self, client, citizen_token):
        r = client.get("/api/admin/problems", headers={"Authorization": f"Bearer {citizen_token}"})
        assert r.status_code == 403

    def test_no_token_admin_unauthorized(self, client):
        assert client.get("/api/admin/problems").status_code == 401

    def test_editor_allowed_admin(self, client, editor_headers):
        assert client.get("/api/admin/problems", headers=editor_headers).status_code == 200


class TestRefresh:
    def test_refresh_rotation_revokes_old(self, client):
        client.post("/api/auth/register", json={"email": "r@bel.by", "password": "pass-12345", "name": "Rob"})
        rt = client.post("/api/auth/login", data={"username": "r@bel.by", "password": "pass-12345"}).json()["refresh_token"]
        r1 = client.post("/api/auth/refresh", json={"refresh_token": rt})
        assert r1.status_code == 200
        # old refresh token now revoked
        r2 = client.post("/api/auth/refresh", json={"refresh_token": rt})
        assert r2.status_code == 401

    def test_logout_revokes_refresh(self, client):
        client.post("/api/auth/register", json={"email": "lo@bel.by", "password": "pass-12345", "name": "LO"})
        rt = client.post("/api/auth/login", data={"username": "lo@bel.by", "password": "pass-12345"}).json()["refresh_token"]
        assert client.post("/api/auth/logout", json={"refresh_token": rt}).status_code == 204
        assert client.post("/api/auth/refresh", json={"refresh_token": rt}).status_code == 401


class TestRateLimit:
    def test_repeated_bad_logins_blocked(self, client):
        codes = [
            client.post("/api/auth/login", data={"username": "rl@bel.by", "password": "bad"}).status_code
            for _ in range(7)
        ]
        assert 429 in codes
