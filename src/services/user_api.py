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

    # Situations & tasks
    def list_situations(self) -> list[dict]:
        return self._request("GET", "/api/user/situations") or []

    def create_situation(self, payload: dict) -> dict:
        return self._request("POST", "/api/user/situations", payload=payload)

    def get_situation(self, situation_id: str) -> dict:
        return self._request("GET", f"/api/user/situations/{situation_id}")

    def update_situation(self, situation_id: str, payload: dict) -> dict:
        return self._request("PUT", f"/api/user/situations/{situation_id}", payload=payload)

    def delete_situation(self, situation_id: str) -> None:
        self._request("DELETE", f"/api/user/situations/{situation_id}")

    def add_task(self, situation_id: str, payload: dict) -> dict:
        return self._request("POST", f"/api/user/situations/{situation_id}/tasks", payload=payload)

    def update_task(self, task_id: str, payload: dict) -> dict:
        return self._request("PATCH", f"/api/user/tasks/{task_id}", payload=payload)

    def delete_task(self, task_id: str) -> None:
        self._request("DELETE", f"/api/user/tasks/{task_id}")

    # Notifications
    def list_notifications(self) -> list[dict]:
        return self._request("GET", "/api/user/notifications") or []

    def create_notification(self, payload: dict) -> dict:
        return self._request("POST", "/api/user/notifications", payload=payload)

    def mark_notification_read(self, notification_id: str) -> dict:
        return self._request("PATCH", f"/api/user/notifications/{notification_id}/read")

    def mark_all_notifications_read(self) -> dict:
        return self._request("POST", "/api/user/notifications/read-all") or {}

    def delete_notification(self, notification_id: str) -> None:
        self._request("DELETE", f"/api/user/notifications/{notification_id}")

    # Utility (ЖКХ)
    def list_utility_accounts(self) -> list[dict]:
        return self._request("GET", "/api/user/utility/accounts") or []

    def create_utility_account(self, payload: dict) -> dict:
        return self._request("POST", "/api/user/utility/accounts", payload=payload)

    def update_utility_account(self, account_id: str, payload: dict) -> dict:
        return self._request("PUT", f"/api/user/utility/accounts/{account_id}", payload=payload)

    def delete_utility_account(self, account_id: str) -> None:
        self._request("DELETE", f"/api/user/utility/accounts/{account_id}")

    def add_utility_payment(self, account_id: str, payload: dict) -> dict:
        return self._request("POST", f"/api/user/utility/accounts/{account_id}/payments", payload=payload)

    def update_utility_payment(self, payment_id: str, payload: dict) -> dict:
        return self._request("PATCH", f"/api/user/utility/payments/{payment_id}", payload=payload)

    def delete_utility_payment(self, payment_id: str) -> None:
        self._request("DELETE", f"/api/user/utility/payments/{payment_id}")

    # Taxes
    def list_taxes(self) -> list[dict]:
        return self._request("GET", "/api/user/taxes") or []

    def create_tax(self, payload: dict) -> dict:
        return self._request("POST", "/api/user/taxes", payload=payload)

    def update_tax(self, tax_id: str, payload: dict) -> dict:
        return self._request("PUT", f"/api/user/taxes/{tax_id}", payload=payload)

    def delete_tax(self, tax_id: str) -> None:
        self._request("DELETE", f"/api/user/taxes/{tax_id}")
