"""Utility (ЖКХ) accounts/payments and tax obligations — owner-isolated."""
import pytest


def _auth(client, email: str) -> dict:
    client.post("/api/auth/register", json={"email": email, "password": "user-pass-1", "name": "Tester"})
    r = client.post("/api/auth/login", data={"username": email, "password": "user-pass-1"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def h(client):
    return _auth(client, "track@bel.by")


class TestUtilityAccounts:
    def test_create_and_list(self, client, h):
        r = client.post("/api/user/utility/accounts", headers=h, json={
            "address": "ул. Независимости, 25", "account_number": "ЛС 001", "provider": "РСЦ",
        })
        assert r.status_code == 201
        acc_id = r.json()["id"]
        assert any(a["id"] == acc_id for a in client.get("/api/user/utility/accounts", headers=h).json())

    def test_update(self, client, h):
        acc_id = client.post("/api/user/utility/accounts", headers=h, json={"address": "A"}).json()["id"]
        r = client.put(f"/api/user/utility/accounts/{acc_id}", headers=h, json={"provider": "Минскводоканал"})
        assert r.json()["provider"] == "Минскводоканал"

    def test_delete(self, client, h):
        acc_id = client.post("/api/user/utility/accounts", headers=h, json={"address": "A"}).json()["id"]
        assert client.delete(f"/api/user/utility/accounts/{acc_id}", headers=h).status_code == 204


class TestUtilityPayments:
    def test_add_payment_returns_account(self, client, h):
        acc_id = client.post("/api/user/utility/accounts", headers=h, json={"address": "A"}).json()["id"]
        r = client.post(f"/api/user/utility/accounts/{acc_id}/payments", headers=h, json={
            "period": "Май 2026", "amount": 78.4, "status": "Ожидает",
        })
        assert r.status_code == 201
        assert len(r.json()["payments"]) == 1
        assert r.json()["payments"][0]["amount"] == 78.4

    def test_update_payment_status(self, client, h):
        acc_id = client.post("/api/user/utility/accounts", headers=h, json={"address": "A"}).json()["id"]
        acc = client.post(f"/api/user/utility/accounts/{acc_id}/payments", headers=h, json={"period": "Май"}).json()
        pid = acc["payments"][0]["id"]
        r = client.patch(f"/api/user/utility/payments/{pid}", headers=h, json={"status": "Оплачено", "amount": 90.0})
        assert r.json()["status"] == "Оплачено"
        assert r.json()["amount"] == 90.0

    def test_delete_payment(self, client, h):
        acc_id = client.post("/api/user/utility/accounts", headers=h, json={"address": "A"}).json()["id"]
        acc = client.post(f"/api/user/utility/accounts/{acc_id}/payments", headers=h, json={"period": "Май"}).json()
        pid = acc["payments"][0]["id"]
        assert client.delete(f"/api/user/utility/payments/{pid}", headers=h).status_code == 204

    def test_delete_account_cascades_payments(self, client, h):
        acc_id = client.post("/api/user/utility/accounts", headers=h, json={"address": "A"}).json()["id"]
        client.post(f"/api/user/utility/accounts/{acc_id}/payments", headers=h, json={"period": "Май"})
        client.delete(f"/api/user/utility/accounts/{acc_id}", headers=h)
        assert all(a["id"] != acc_id for a in client.get("/api/user/utility/accounts", headers=h).json())


class TestTaxes:
    def test_crud(self, client, h):
        r = client.post("/api/user/taxes", headers=h, json={
            "title": "Декларация", "user_type": "individual", "deadline": "2026-03-01", "amount": 0.0,
        })
        assert r.status_code == 201
        tid = r.json()["id"]
        assert any(t["id"] == tid for t in client.get("/api/user/taxes", headers=h).json())
        r = client.put(f"/api/user/taxes/{tid}", headers=h, json={"status": "Оплачено"})
        assert r.json()["status"] == "Оплачено"
        assert client.delete(f"/api/user/taxes/{tid}", headers=h).status_code == 204

    def test_title_required(self, client, h):
        assert client.post("/api/user/taxes", headers=h, json={"user_type": "ip"}).status_code == 422


class TestOwnership:
    def test_utility_isolation(self, client):
        a = _auth(client, "a-tr@bel.by")
        b = _auth(client, "b-tr@bel.by")
        acc_id = client.post("/api/user/utility/accounts", headers=a, json={"address": "Secret"}).json()["id"]
        assert client.put(f"/api/user/utility/accounts/{acc_id}", headers=b, json={"address": "x"}).status_code == 404
        assert client.delete(f"/api/user/utility/accounts/{acc_id}", headers=b).status_code == 404
        assert all(acc["id"] != acc_id for acc in client.get("/api/user/utility/accounts", headers=b).json())

    def test_tax_isolation(self, client):
        a = _auth(client, "a-tax@bel.by")
        b = _auth(client, "b-tax@bel.by")
        tid = client.post("/api/user/taxes", headers=a, json={"title": "Private"}).json()["id"]
        assert client.put(f"/api/user/taxes/{tid}", headers=b, json={"status": "x"}).status_code == 404
        assert all(t["id"] != tid for t in client.get("/api/user/taxes", headers=b).json())
