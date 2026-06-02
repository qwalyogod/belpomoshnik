from __future__ import annotations

import json
from urllib import error, parse, request


class AdminAPIError(Exception):
    pass


class AdminAPIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8060"):
        self.base_url = base_url.rstrip("/")
        self._opener = request.build_opener(request.ProxyHandler({}))

    def _request(self, method: str, path: str, payload: dict | None = None, params: dict | None = None):
        query = f"?{parse.urlencode(params)}" if params else ""
        url = f"{self.base_url}{path}{query}"
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(url=url, data=body, method=method, headers=headers)
        try:
            with self._opener.open(req, timeout=6) as response:
                data = response.read()
                if not data:
                    return None
                return json.loads(data.decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise AdminAPIError(f"{exc.code}: {detail or exc.reason}") from exc
        except error.URLError as exc:
            raise AdminAPIError("API недоступно. Проверьте запуск backend-сервера.") from exc

    def health(self) -> bool:
        payload = self._request("GET", "/api/health")
        return bool(payload and payload.get("status") == "ok")

    def list_admin_problems(self) -> list[dict]:
        return self._request("GET", "/api/admin/problems") or []

    def list_admin_scenarios(self, problem_id: int | None = None, status_filter: str | None = None) -> list[dict]:
        params = {}
        if problem_id is not None:
            params["problem_id"] = problem_id
        if status_filter:
            params["status"] = status_filter
        return self._request("GET", "/api/admin/scenarios", params=params) or []

    def create_problem(self, payload: dict) -> dict:
        return self._request("POST", "/api/admin/problems", payload=payload)

    def update_problem(self, problem_id: int, payload: dict) -> dict:
        return self._request("PUT", f"/api/admin/problems/{problem_id}", payload=payload)

    def delete_problem(self, problem_id: int) -> None:
        self._request("DELETE", f"/api/admin/problems/{problem_id}")

    def create_scenario(self, payload: dict) -> dict:
        return self._request("POST", "/api/admin/scenarios", payload=payload)

    def update_scenario(self, scenario_id: int, payload: dict) -> dict:
        return self._request("PUT", f"/api/admin/scenarios/{scenario_id}", payload=payload)

    def delete_scenario(self, scenario_id: int) -> None:
        self._request("DELETE", f"/api/admin/scenarios/{scenario_id}")

    def verify_scenario(self, scenario_id: int) -> dict:
        return self._request("POST", f"/api/admin/scenarios/{scenario_id}/verify")

    def set_verification_notes(self, scenario_id: int, notes: str) -> dict:
        return self._request("POST", f"/api/admin/scenarios/{scenario_id}/verify-notes", payload={"notes": notes})

    def reorder_stages(self, scenario_id: int, ids: list[int]) -> None:
        self._request("PATCH", f"/api/admin/scenarios/{scenario_id}/stages/reorder", payload={"ids": ids})

    def reorder_steps(self, stage_id: int, ids: list[int]) -> None:
        self._request("PATCH", f"/api/admin/stages/{stage_id}/steps/reorder", payload={"ids": ids})

    def get_admin_scenario(self, scenario_id: int) -> dict:
        return self._request("GET", f"/api/admin/scenarios/{scenario_id}")

    def create_stage(self, scenario_id: int, payload: dict) -> dict:
        return self._request("POST", f"/api/admin/scenarios/{scenario_id}/stages", payload=payload)

    def update_stage(self, stage_id: int, payload: dict) -> dict:
        return self._request("PUT", f"/api/admin/stages/{stage_id}", payload=payload)

    def delete_stage(self, stage_id: int) -> None:
        self._request("DELETE", f"/api/admin/stages/{stage_id}")

    def create_step(self, stage_id: int, payload: dict) -> dict:
        return self._request("POST", f"/api/admin/stages/{stage_id}/steps", payload=payload)

    def update_step(self, step_id: int, payload: dict) -> dict:
        return self._request("PUT", f"/api/admin/steps/{step_id}", payload=payload)

    def delete_step(self, step_id: int) -> None:
        self._request("DELETE", f"/api/admin/steps/{step_id}")

    def list_admin_documents(self) -> list[dict]:
        return self._request("GET", "/api/admin/documents") or []

    def create_document(self, payload: dict) -> dict:
        return self._request("POST", "/api/admin/documents", payload=payload)

    def update_document(self, document_id: int, payload: dict) -> dict:
        return self._request("PUT", f"/api/admin/documents/{document_id}", payload=payload)

    def delete_document(self, document_id: int) -> None:
        self._request("DELETE", f"/api/admin/documents/{document_id}")

    def list_admin_authorities(self) -> list[dict]:
        return self._request("GET", "/api/admin/authorities") or []

    def create_authority(self, payload: dict) -> dict:
        return self._request("POST", "/api/admin/authorities", payload=payload)

    def update_authority(self, authority_id: int, payload: dict) -> dict:
        return self._request("PUT", f"/api/admin/authorities/{authority_id}", payload=payload)

    def delete_authority(self, authority_id: int) -> None:
        self._request("DELETE", f"/api/admin/authorities/{authority_id}")

    def list_admin_deadlines(self) -> list[dict]:
        return self._request("GET", "/api/admin/deadlines") or []

    def attach_step_document(self, step_id: int, document_id: int) -> dict:
        return self._request("POST", f"/api/admin/steps/{step_id}/documents/{document_id}")

    def create_related_scenario(self, payload: dict) -> dict:
        return self._request("POST", "/api/admin/related-scenarios", payload=payload)

    def delete_related_scenario(self, related_id: int) -> None:
        self._request("DELETE", f"/api/admin/related-scenarios/{related_id}")

    def create_source_reference(self, payload: dict) -> dict:
        return self._request("POST", "/api/admin/source-references", payload=payload)

    def delete_source_reference(self, source_ref_id: int) -> None:
        self._request("DELETE", f"/api/admin/source-references/{source_ref_id}")

    def create_dependency(self, payload: dict) -> dict:
        return self._request("POST", "/api/admin/dependencies", payload=payload)

    def delete_dependency(self, dependency_id: int) -> None:
        self._request("DELETE", f"/api/admin/dependencies/{dependency_id}")
