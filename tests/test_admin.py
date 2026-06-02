"""Admin CRUD, scenario verification, reorder, delete cascade, audit log."""
import pytest


@pytest.fixture
def problem_id(client, editor_headers):
    r = client.post("/api/admin/problems", headers=editor_headers, json={"title": "Проблема", "slug": "prob-1"})
    assert r.status_code == 201
    return r.json()["id"]


@pytest.fixture
def scenario_id(client, editor_headers, problem_id):
    r = client.post(
        "/api/admin/scenarios",
        headers=editor_headers,
        json={"problem_id": problem_id, "title": "Сценарий", "slug": "scn-1"},
    )
    assert r.status_code == 201
    return r.json()["id"]


class TestProblemCRUD:
    def test_create_and_list(self, client, editor_headers, problem_id):
        items = client.get("/api/admin/problems", headers=editor_headers).json()
        assert any(p["id"] == problem_id for p in items)

    def test_update(self, client, editor_headers, problem_id):
        r = client.put(f"/api/admin/problems/{problem_id}", headers=editor_headers, json={"title": "Изменено"})
        assert r.status_code == 200
        assert r.json()["title"] == "Изменено"

    def test_delete(self, client, editor_headers, problem_id):
        assert client.delete(f"/api/admin/problems/{problem_id}", headers=editor_headers).status_code == 204

    def test_delete_missing_404(self, client, editor_headers):
        assert client.delete("/api/admin/problems/999999", headers=editor_headers).status_code == 404


class TestScenarioVerification:
    def test_verify_sets_metadata(self, client, editor_headers, scenario_id):
        r = client.post(f"/api/admin/scenarios/{scenario_id}/verify", headers=editor_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["content_verified_at"] is not None
        assert body["verified_by"] == "editor@bel.by"

    def test_verification_notes(self, client, editor_headers, scenario_id):
        r = client.post(
            f"/api/admin/scenarios/{scenario_id}/verify-notes",
            headers=editor_headers,
            json={"notes": "Сверено с pravo.by"},
        )
        assert r.status_code == 200
        assert r.json()["verification_notes"] == "Сверено с pravo.by"


class TestReorder:
    def _stage(self, client, h, sid, title, order):
        return client.post(
            f"/api/admin/scenarios/{sid}/stages",
            headers=h,
            json={"scenario_id": sid, "title": title, "order_index": order},
        ).json()

    def test_reorder_stages(self, client, editor_headers, scenario_id):
        a = self._stage(client, editor_headers, scenario_id, "Этап A", 0)
        b = self._stage(client, editor_headers, scenario_id, "Этап B", 1)
        r = client.patch(
            f"/api/admin/scenarios/{scenario_id}/stages/reorder",
            headers=editor_headers,
            json={"ids": [b["id"], a["id"]]},
        )
        assert r.status_code == 204
        detail = client.get(f"/api/admin/scenarios/{scenario_id}", headers=editor_headers).json()
        order = [s["id"] for s in sorted(detail["stages"], key=lambda x: x["order_index"])]
        assert order == [b["id"], a["id"]]

    def test_reorder_steps(self, client, editor_headers, scenario_id):
        stage = self._stage(client, editor_headers, scenario_id, "Этап", 0)
        s1 = client.post(
            f"/api/admin/stages/{stage['id']}/steps",
            headers=editor_headers,
            json={"stage_id": stage["id"], "title": "Шаг 1", "order_index": 0},
        ).json()
        s2 = client.post(
            f"/api/admin/stages/{stage['id']}/steps",
            headers=editor_headers,
            json={"stage_id": stage["id"], "title": "Шаг 2", "order_index": 1},
        ).json()
        r = client.patch(
            f"/api/admin/stages/{stage['id']}/steps/reorder",
            headers=editor_headers,
            json={"ids": [s2["id"], s1["id"]]},
        )
        assert r.status_code == 204


class TestAuditLog:
    def test_create_and_delete_logged(self, client, editor_headers, problem_id):
        client.delete(f"/api/admin/problems/{problem_id}", headers=editor_headers)
        logs = client.get("/api/admin/audit-logs", headers=editor_headers).json()
        actions = " ".join(a.get("action", "").lower() for a in logs)
        assert "создан" in actions
        assert "удал" in actions
