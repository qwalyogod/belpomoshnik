from __future__ import annotations

import json
from urllib import error, request


class PublicAPIError(Exception):
    pass


class PublicAPIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8060"):
        self.base_url = base_url.rstrip("/")
        self._opener = request.build_opener(request.ProxyHandler({}))

    def _request(self, path: str):
        url = f"{self.base_url}{path}"
        req = request.Request(url=url, method="GET", headers={"Accept": "application/json"})
        try:
            with self._opener.open(req, timeout=6) as response:
                data = response.read()
                if not data:
                    return None
                return json.loads(data.decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise PublicAPIError(f"{exc.code}: {detail or exc.reason}") from exc
        except error.URLError as exc:
            raise PublicAPIError("Public API недоступно.") from exc

    def health(self) -> bool:
        payload = self._request("/api/health")
        return bool(payload and payload.get("status") == "ok")

    def get_scenario(self, slug: str) -> dict:
        return self._request(f"/api/scenarios/{slug}")

    def get_problems(self) -> list[dict]:
        """G4 — публичный список опубликованных проблем из backend."""
        return self._request("/api/problems") or []

    def get_law_updates(self) -> list[dict]:
        """G4 — публичный список закон-апдейтов со статусом APPLIED из backend."""
        return self._request("/api/law-updates") or []

    def get_authorities(self) -> list[dict]:
        """G4 — справочник учреждений из backend."""
        return self._request("/api/authorities") or []

    def get_documents(self) -> list[dict]:
        """G4 — справочник документов из backend."""
        return self._request("/api/documents") or []
