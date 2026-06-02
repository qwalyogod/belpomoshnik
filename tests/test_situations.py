"""Personal situations, tasks (progress sync), notifications — owner-isolated."""
import pytest


def _auth(client, email: str) -> dict:
    client.post("/api/auth/register", json={"email": email, "password": "user-pass-1", "name": "Tester"})
    r = client.post("/api/auth/login", data={"username": email, "password": "user-pass-1"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def h(client):
    return _auth(client, "sit@bel.by")


class TestSituationCRUD:
    def test_create_with_tasks(self, client, h):
        r = client.post("/api/user/situations", headers=h, json={
            "template_id": "childbirth",
            "title": "Рождение ребёнка",
            "category": "Семья",
            "tasks": [{"title": "Получить справку"}, {"title": "Подать заявление"}],
        })
        assert r.status_code == 201
        body = r.json()
        assert body["progress"] == 0
        assert body["status"] == "Не начата"
        assert len(body["tasks"]) == 2

    def test_list_and_get(self, client, h):
        sid = client.post("/api/user/situations", headers=h, json={"title": "S"}).json()["id"]
        assert any(s["id"] == sid for s in client.get("/api/user/situations", headers=h).json())
        assert client.get(f"/api/user/situations/{sid}", headers=h).json()["id"] == sid

    def test_update(self, client, h):
        sid = client.post("/api/user/situations", headers=h, json={"title": "S"}).json()["id"]
        r = client.put(f"/api/user/situations/{sid}", headers=h, json={"title": "Изменено", "category": "ЖКХ"})
        assert r.json()["title"] == "Изменено"
        assert r.json()["category"] == "ЖКХ"

    def test_delete_cascades_tasks(self, client, h):
        sid = client.post("/api/user/situations", headers=h, json={"title": "S", "tasks": [{"title": "T"}]}).json()["id"]
        assert client.delete(f"/api/user/situations/{sid}", headers=h).status_code == 204
        assert client.get(f"/api/user/situations/{sid}", headers=h).status_code == 404


class TestProgressSync:
    def _make(self, client, h):
        return client.post("/api/user/situations", headers=h, json={
            "title": "Plan", "tasks": [{"title": "A"}, {"title": "B"}],
        }).json()

    def test_complete_one_updates_progress(self, client, h):
        sit = self._make(client, h)
        task_id = sit["tasks"][0]["id"]
        client.patch(f"/api/user/tasks/{task_id}", headers=h, json={"completed": True})
        refreshed = client.get(f"/api/user/situations/{sit['id']}", headers=h).json()
        assert refreshed["progress"] == 50
        assert refreshed["status"] == "В процессе"

    def test_complete_all_marks_done(self, client, h):
        sit = self._make(client, h)
        for t in sit["tasks"]:
            client.patch(f"/api/user/tasks/{t['id']}", headers=h, json={"completed": True})
        refreshed = client.get(f"/api/user/situations/{sit['id']}", headers=h).json()
        assert refreshed["progress"] == 100
        assert refreshed["status"] == "Завершена"

    def test_add_task_recomputes(self, client, h):
        sit = self._make(client, h)
        client.patch(f"/api/user/tasks/{sit['tasks'][0]['id']}", headers=h, json={"completed": True})
        # 1/2 = 50%; add a 3rd task -> 1/3 = 33%
        r = client.post(f"/api/user/situations/{sit['id']}/tasks", headers=h, json={"title": "C"})
        assert r.json()["progress"] == 33

    def test_delete_task_recomputes(self, client, h):
        sit = self._make(client, h)
        client.patch(f"/api/user/tasks/{sit['tasks'][0]['id']}", headers=h, json={"completed": True})
        # remove the incomplete one -> 1/1 = 100%
        client.delete(f"/api/user/tasks/{sit['tasks'][1]['id']}", headers=h)
        refreshed = client.get(f"/api/user/situations/{sit['id']}", headers=h).json()
        assert refreshed["progress"] == 100


class TestOwnership:
    def test_cannot_access_others_situation(self, client):
        a = _auth(client, "a-sit@bel.by")
        b = _auth(client, "b-sit@bel.by")
        sid = client.post("/api/user/situations", headers=a, json={"title": "Secret", "tasks": [{"title": "T"}]}).json()["id"]
        assert client.get(f"/api/user/situations/{sid}", headers=b).status_code == 404
        assert client.delete(f"/api/user/situations/{sid}", headers=b).status_code == 404

    def test_cannot_touch_others_task(self, client):
        a = _auth(client, "a2-sit@bel.by")
        b = _auth(client, "b2-sit@bel.by")
        sit = client.post("/api/user/situations", headers=a, json={"title": "S", "tasks": [{"title": "T"}]}).json()
        tid = sit["tasks"][0]["id"]
        assert client.patch(f"/api/user/tasks/{tid}", headers=b, json={"completed": True}).status_code == 404


class TestNotifications:
    def test_create_list_read_flow(self, client, h):
        nid = client.post("/api/user/notifications", headers=h, json={"title": "Срок завтра"}).json()["id"]
        items = client.get("/api/user/notifications", headers=h).json()
        assert any(n["id"] == nid and n["is_read"] is False for n in items)
        assert client.patch(f"/api/user/notifications/{nid}/read", headers=h).json()["is_read"] is True

    def test_read_all(self, client, h):
        client.post("/api/user/notifications", headers=h, json={"title": "N1"})
        client.post("/api/user/notifications", headers=h, json={"title": "N2"})
        assert client.post("/api/user/notifications/read-all", headers=h).json()["updated"] >= 2
        assert all(n["is_read"] for n in client.get("/api/user/notifications", headers=h).json())

    def test_delete(self, client, h):
        nid = client.post("/api/user/notifications", headers=h, json={"title": "Del"}).json()["id"]
        assert client.delete(f"/api/user/notifications/{nid}", headers=h).status_code == 204

    def test_ownership(self, client):
        a = _auth(client, "a-notif@bel.by")
        b = _auth(client, "b-notif@bel.by")
        nid = client.post("/api/user/notifications", headers=a, json={"title": "Private"}).json()["id"]
        assert client.patch(f"/api/user/notifications/{nid}/read", headers=b).status_code == 404
        assert all(n["id"] != nid for n in client.get("/api/user/notifications", headers=b).json())
