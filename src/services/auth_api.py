"""Auth API client — register / login / refresh via FastAPI backend (JWT)."""
from __future__ import annotations

import json
from urllib import error, parse, request


class AuthAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class AuthAPIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8060"):
        self.base_url = base_url.rstrip("/")
        self._opener = request.build_opener(request.ProxyHandler({}))

    def _post(self, path: str, *, json_body: dict | None = None, form_body: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        if form_body is not None:
            data = parse.urlencode(form_body).encode("utf-8")
            headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        else:
            data = json.dumps(json_body or {}).encode("utf-8")
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
        req = request.Request(url=url, data=data, method="POST", headers=headers)
        try:
            with self._opener.open(req, timeout=6) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else {}
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            try:
                parsed = json.loads(detail)
                message = parsed.get("detail", detail)
            except (json.JSONDecodeError, AttributeError):
                message = detail or exc.reason
            raise AuthAPIError(str(message), status_code=exc.code) from exc
        except error.URLError as exc:
            raise AuthAPIError("Сервер авторизации недоступен.") from exc

    def health(self) -> bool:
        try:
            url = f"{self.base_url}/api/health"
            req = request.Request(url=url, method="GET", headers={"Accept": "application/json"})
            with self._opener.open(req, timeout=4) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return bool(payload and payload.get("status") == "ok")
        except (error.URLError, json.JSONDecodeError):
            return False

    def register(self, name: str, email: str, password: str) -> dict:
        """POST /api/auth/register → {access_token, refresh_token, ...}"""
        return self._post("/api/auth/register", json_body={
            "name": name,
            "email": email,
            "password": password,
        })

    def login(self, email: str, password: str) -> dict:
        """POST /api/auth/login (OAuth2 form) → {access_token, refresh_token, ...}"""
        return self._post("/api/auth/login", form_body={
            "username": email,
            "password": password,
        })

    def list_test_accounts(self) -> list[dict]:
        """GET /api/auth/test-accounts — список seed-аккаунтов для UI-переключателя."""
        try:
            url = f"{self.base_url}/api/auth/test-accounts"
            req = request.Request(url=url, method="GET", headers={"Accept": "application/json"})
            with self._opener.open(req, timeout=4) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) or []
        except (error.URLError, error.HTTPError, json.JSONDecodeError):
            return []

    def oauth(self, provider: str, email: str, name: str) -> dict:
        """
        Demo OAuth flow for Google / Yandex.
        Real flow needs provider client_id/secret + redirect. For the diploma
        we issue a backend JWT for the demo identity via the register endpoint.
        """
        return self._post("/api/auth/register", json_body={
            "name": name,
            "email": email,
            "password": f"{provider}-oauth-demo-secret",
        })
