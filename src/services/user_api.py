"""User API client — профиль, настройки, личные документы (JWT Bearer)."""
from __future__ import annotations

import json
from urllib import error, request


class UserAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class UserAPIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8060", access_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self._opener = request.build_opener(request.ProxyHandler({}))

    def set_token(self, access_token: str) -> None:
        self.access_token = access_token

    def _request(self, method: str, path: str, payload: dict | None = None):
        url = f"{self.base_url}{path}"
        headers = {"Accept": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        body = None
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = request.Request(url=url, data=body, method=method, headers=headers)
        try:
            with self._opener.open(req, timeout=6) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else None
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            try:
                message = json.loads(detail).get("detail", detail)
            except (json.JSONDecodeError, AttributeError):
                message = detail or exc.reason
            raise UserAPIError(str(message), status_code=exc.code) from exc
        except error.URLError as exc:
            raise UserAPIError("API недоступно. Проверьте backend-сервер.") from exc

    # Profile / settings
    def get_profile(self) -> dict:
        return self._request("GET", "/api/user/profile")

    def update_profile(self, payload: dict) -> dict:
        return self._request("PUT", "/api/user/profile", payload=payload)

    def get_settings(self) -> dict:
        return self._request("GET", "/api/user/settings") or {}

    def update_settings(self, payload: dict) -> dict:
        return self._request("PATCH", "/api/user/settings", payload=payload) or {}

    # Documents
    def list_documents(self) -> list[dict]:
        return self._request("GET", "/api/user/documents") or []

    def create_document(self, payload: dict) -> dict:
        return self._request("POST", "/api/user/documents", payload=payload)

    def update_document(self, doc_id: int, payload: dict) -> dict:
        return self._request("PUT", f"/api/user/documents/{doc_id}", payload=payload)

    def delete_document(self, doc_id: int) -> None:
        self._request("DELETE", f"/api/user/documents/{doc_id}")
