"""T-NEW — Регрессионные тесты на дыры, закрытые в рамках финализации MVP.

Каждый тест привязан к конкретному фиксу из docs/PROJECT_STATUS.md.
Если вы меняли auth/api/admin и один из тестов упал — значит вы откатили защиту.
"""
from __future__ import annotations

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Локальные фикстуры
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def citizen_headers(citizen_token):
    return {"Authorization": f"Bearer {citizen_token}"}


@pytest.fixture
def citizen_user(client):
    """Возвращает (email, password, headers, tokens) для citizen-пользователя."""
    email = "citizen-test@bel.by"
    password = "citizen-pass-1"
    client.post("/api/auth/register", json={"email": email, "password": password, "name": "Test"})
    r = client.post("/api/auth/login", data={"username": email, "password": password})
    tokens = r.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    return {"email": email, "password": password, "headers": headers, "tokens": tokens}


# ─────────────────────────────────────────────────────────────────────────────
# F-SECRET-1: SECRET_KEY fail-fast
# ─────────────────────────────────────────────────────────────────────────────
class TestSecretKeyRequired:
    def test_secret_key_must_be_set(self, monkeypatch):
        """auth.py должен падать при пустом/коротком SECRET_KEY."""
        monkeypatch.delenv("BELPOMOSHNIK_SECRET_KEY", raising=False)
        with pytest.raises(RuntimeError, match="BELPOMOSHNIK_SECRET_KEY"):
            import importlib
            from backend import auth as auth_mod
            importlib.reload(auth_mod)

    def test_secret_key_rejects_known_fallback(self, monkeypatch):
        """Запрещённые заглушки ('change-me-in-production', 'secret', 'dev') блокируются."""
        for bad in ("change-me-in-production", "secret", "dev", "a" * 31):
            monkeypatch.setenv("BELPOMOSHNIK_SECRET_KEY", bad)
            with pytest.raises(RuntimeError):
                import importlib
                from backend import auth as auth_mod
                importlib.reload(auth_mod)


# ─────────────────────────────────────────────────────────────────────────────
# F-REFRESH-1: refresh принимает JSON, не form-urlencoded
# ─────────────────────────────────────────────────────────────────────────────
class TestRefreshJsonContract:
    def test_refresh_json_ok(self, client, citizen_user):
        rt = citizen_user["tokens"]["refresh_token"]
        r = client.post("/api/auth/refresh", json={"refresh_token": rt})
        assert r.status_code == 200, r.text
        body = r.json()
        assert "access_token" in body
        assert "refresh_token" in body

    def test_refresh_formdata_rejected(self, client, citizen_user):
        """Старый фронт слал form-urlencoded — теперь должен получить 422."""
        rt = citizen_user["tokens"]["refresh_token"]
        r = client.post("/api/auth/refresh", data={"refresh_token": rt})
        assert r.status_code == 422, r.text


# ─────────────────────────────────────────────────────────────────────────────
# F-LOGOUT-1: logout принимает JSON
# ─────────────────────────────────────────────────────────────────────────────
class TestLogoutJsonContract:
    def test_logout_json_ok(self, client, citizen_user):
        rt = citizen_user["tokens"]["refresh_token"]
        r = client.post("/api/auth/logout", json={"refresh_token": rt})
        assert r.status_code in (200, 204), r.text

    def test_logout_formdata_rejected(self, client, citizen_user):
        rt = citizen_user["tokens"]["refresh_token"]
        r = client.post("/api/auth/logout", data={"refresh_token": rt})
        assert r.status_code == 422, r.text


# ─────────────────────────────────────────────────────────────────────────────
# F-BOOTSTRAP-1: /api/admin/bootstrap/problems требует auth
# ─────────────────────────────────────────────────────────────────────────────
class TestBootstrapRequiresAuth:
    def test_bootstrap_problems_anonymous(self, client):
        r = client.get("/api/admin/bootstrap/problems")
        assert r.status_code in (401, 403), r.text

    def test_bootstrap_problems_citizen_forbidden(self, client, citizen_headers):
        r = client.get("/api/admin/bootstrap/problems", headers=citizen_headers)
        # citizen не должен иметь доступа к админ-эндпоинту
        assert r.status_code in (401, 403), r.text

    def test_bootstrap_problems_editor_ok(self, client, editor_headers):
        r = client.get("/api/admin/bootstrap/problems", headers=editor_headers)
        assert r.status_code == 200, r.text


# ─────────────────────────────────────────────────────────────────────────────
# F-AUDIT-1: единственный /api/admin/audit-logs
# ─────────────────────────────────────────────────────────────────────────────
class TestAuditLogsSingleEndpoint:
    def test_audit_logs_route_registered_once(self):
        """Приложение должно стартовать без AssertionError о дублях роутов."""
        from backend.app import app
        paths = [r.path for r in app.routes if hasattr(r, "path") and "audit" in r.path]
        assert paths.count("/api/admin/audit-logs") == 1, paths


# ─────────────────────────────────────────────────────────────────────────────
# F-SETTINGS-1: PATCH /settings фильтрует опасные ключи
# ─────────────────────────────────────────────────────────────────────────────
class TestSettingsAllowlist:
    def test_settings_allowlist_drops_role(self, client, citizen_headers):
        """role/is_admin/password — не должны примениться через /settings."""
        r = client.patch(
            "/api/user/settings",
            headers=citizen_headers,
            json={"role": "platform_admin", "is_admin": True, "password": "pwn", "theme": "dark"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "role" not in body
        assert "is_admin" not in body
        assert "password" not in body
        assert body.get("theme") == "dark"

    def test_settings_allowlist_drops_is_test_account(self, client, citizen_headers):
        r = client.patch(
            "/api/user/settings",
            headers=citizen_headers,
            json={"is_test_account": True, "is_active": False, "lang": "ru"},
        )
        body = r.json()
        assert "is_test_account" not in body
        assert "is_active" not in body
        assert body.get("lang") == "ru"

    def test_settings_allowlist_preserves_known(self, client, citizen_headers):
        r = client.patch(
            "/api/user/settings",
            headers=citizen_headers,
            json={"dark_theme": True, "doc_reminder_days": 45},
        )
        body = r.json()
        assert body.get("dark_theme") is True
        assert body.get("doc_reminder_days") == 45


# ─────────────────────────────────────────────────────────────────────────────
# F-ARTICLE-1: body_html санитизация
# ─────────────────────────────────────────────────────────────────────────────
class TestArticleSanitization:
    def test_sanitize_html_strips_script(self):
        from backend.api.articles import sanitize_html
        out = sanitize_html("<p>ok</p><script>alert(1)</script>")
        assert "<script" not in out.lower()
        assert "<p>ok</p>" in out

    def test_sanitize_html_strips_onclick(self):
        from backend.api.articles import sanitize_html
        out = sanitize_html('<a href="#" onclick="evil()">x</a>')
        assert "onclick" not in out.lower()
        assert "<a" in out

    def test_sanitize_html_strips_javascript_href(self):
        from backend.api.articles import sanitize_html
        out = sanitize_html('<a href="javascript:alert(1)">x</a>')
        assert "javascript:" not in out.lower()
        assert "<a" in out

    def test_sanitize_html_preserves_safe_content(self):
        from backend.api.articles import sanitize_html
        html = "<p>Привет, <strong>мир</strong>!</p><ul><li>1</li></ul>"
        assert sanitize_html(html) == html


# ─────────────────────────────────────────────────────────────────────────────
# F-SCAN-1: /api/user/documents/{id}/scan требует owner
# ─────────────────────────────────────────────────────────────────────────────
class TestDocumentScanAccess:
    def test_scan_anonymous(self, client):
        r = client.get("/api/user/documents/1/scan")
        assert r.status_code in (401, 403), r.text

    def test_scan_nonexistent(self, client, citizen_headers):
        r = client.get("/api/user/documents/999999/scan", headers=citizen_headers)
        # owner-check даёт 404 (намеренно, чтобы не палить существование id)
        assert r.status_code == 404, r.text

    def test_scan_without_scan_uploaded(self, client, citizen_headers):
        """Документ существует, но scan_path пуст → 404."""
        r = client.post(
            "/api/user/documents",
            headers=citizen_headers,
            json={"title": "Тест", "doc_type": "passport", "number": "HB1234567"},
        )
        assert r.status_code in (200, 201), r.text
        doc_id = r.json()["id"]
        r2 = client.get(f"/api/user/documents/{doc_id}/scan", headers=citizen_headers)
        assert r2.status_code == 404, r2.text


# ─────────────────────────────────────────────────────────────────────────────
# F-TESTACCT-1: /api/auth/test-accounts выключен по умолчанию
# ─────────────────────────────────────────────────────────────────────────────
class TestTestAccountsDefaultOff:
    def test_test_accounts_off_by_default(self, client, monkeypatch):
        monkeypatch.delenv("BELPOMOSHNIK_ENABLE_TEST_SWITCHER", raising=False)
        r = client.get("/api/auth/test-accounts")
        assert r.status_code == 200
        assert r.json() == [], r.text

    def test_test_accounts_on_with_flag(self, client, monkeypatch):
        monkeypatch.setenv("BELPOMOSHNIK_ENABLE_TEST_SWITCHER", "true")
        r = client.get("/api/auth/test-accounts")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)
