"""Pure mapper tests for Flet <-> backend field translation + sync routing."""
from services.user_sync import (
    _is_server_id,
    document_from_api,
    document_to_api,
    delete_tax,
    pull_utility,
    push_tax,
    push_utility_payment,
)


class _StubClient:
    """Records calls to verify push/delete routing without a real server."""
    def __init__(self):
        self.calls = []

    def create_tax(self, payload):
        self.calls.append(("create", payload))
        return {"id": "a" * 32, **payload}

    def update_tax(self, tax_id, payload):
        self.calls.append(("update", tax_id, payload))
        return {"id": tax_id, **payload}

    def delete_tax(self, tax_id):
        self.calls.append(("delete", tax_id))


class TestServerIdDetection:
    def test_uuid_hex_is_server_id(self):
        assert _is_server_id("a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6") is True

    def test_local_prefixed_id_is_not(self):
        assert _is_server_id("tax-1717171717") is False
        assert _is_server_id("util-1") is False

    def test_non_string_is_not(self):
        assert _is_server_id(7) is False
        assert _is_server_id(None) is False


class TestTaxSyncRouting:
    def test_local_id_creates(self):
        c = _StubClient()
        result = push_tax(c, {"id": "tax-123", "title": "Декларация"})
        assert c.calls[0][0] == "create"
        assert len(result["id"]) == 32

    def test_server_id_updates(self):
        c = _StubClient()
        sid = "f" * 32
        push_tax(c, {"id": sid, "title": "Декларация", "status": "Оплачено"})
        assert c.calls[0][0] == "update"
        assert c.calls[0][1] == sid

    def test_delete_only_for_server_id(self):
        c = _StubClient()
        delete_tax(c, {"id": "tax-123"})  # local-only -> no API call
        delete_tax(c, {"id": "e" * 32})
        assert [call[0] for call in c.calls] == ["delete"]


class _UtilStub:
    def list_utility_accounts(self):
        return [{
            "id": "a" * 32, "address": "ул. X", "account_number": "ЛС1", "provider": "РСЦ",
            "payments": [
                {"id": "b" * 32, "period": "Май", "amount": 10.0},
                {"id": "c" * 32, "period": "Июнь", "amount": 20.0},
            ],
        }]


class TestPullUtilitySplit:
    def test_flattens_nested_payments(self):
        accounts, payments = pull_utility(_UtilStub())
        assert len(accounts) == 1 and accounts[0]["id"] == "a" * 32
        assert "payments" not in accounts[0]
        assert len(payments) == 2
        assert all(p["account_id"] == "a" * 32 for p in payments)


class TestUtilityPaymentRouting:
    def test_create_needs_server_account(self):
        class _C:
            def __init__(self):
                self.added = []
            def add_utility_payment(self, acc_id, payload):
                self.added.append((acc_id, payload))
                return {"id": acc_id, "payments": [{**payload, "id": "d" * 32}]}
        c = _C()
        # local account id -> cannot create payment yet
        assert push_utility_payment(c, {"id": "upay-1", "period": "Май"}, "util-1") is None
        assert c.added == []
        # server account id -> creates
        result = push_utility_payment(c, {"id": "upay-1", "period": "Май"}, "a" * 32)
        assert result is not None and len(c.added) == 1


class TestDocumentMapper:
    def test_flet_to_api_field_names(self):
        flet = {
            "title": "Паспорт",
            "document_type": "passport",
            "document_number": "MP1234567",
            "issuer": "ОГиМ Минск",
            "issue_date": "2024-05-20",
            "expiry_date": "2034-05-20",
            "comment": "основной",
            "scan_path": "data/private_uploads/p.enc",
            "is_sensitive": True,
            # computed client-only fields must be dropped:
            "status": "Активен",
            "icon": "BADGE",
            "details": "...",
        }
        api = document_to_api(flet)
        assert api == {
            "title": "Паспорт",
            "doc_type": "passport",
            "number": "MP1234567",
            "issued_by": "ОГиМ Минск",
            "issued_date": "2024-05-20",
            "expiry_date": "2034-05-20",
            "comment": "основной",
            "scan_path": "data/private_uploads/p.enc",
            "is_sensitive": True,
        }
        assert "status" not in api and "icon" not in api and "details" not in api

    def test_api_to_flet_field_names(self):
        api = {
            "id": 7,
            "title": "Медкнижка",
            "doc_type": "medical",
            "number": "MB-9",
            "issued_by": "Поликлиника №1",
            "issued_date": "2023-01-10",
            "expiry_date": "2025-01-10",
            "comment": "",
            "scan_path": "",
            "is_sensitive": False,
        }
        flet = document_from_api(api)
        assert flet["id"] == 7
        assert flet["document_type"] == "medical"
        assert flet["document_number"] == "MB-9"
        assert flet["issuer"] == "Поликлиника №1"
        assert flet["issue_date"] == "2023-01-10"

    def test_roundtrip_preserves_data(self):
        original = {
            "id": 3,
            "title": "ВУ",
            "document_type": "license",
            "document_number": "AB123",
            "issuer": "ГАИ",
            "issue_date": "2020-06-01",
            "expiry_date": "2030-06-01",
            "comment": "кат. B",
            "scan_path": "x.enc",
            "is_sensitive": True,
        }
        # Flet -> API -> Flet (id re-attached by from_api)
        api = document_to_api(original)
        api["id"] = original["id"]
        restored = document_from_api(api)
        for key in ("document_type", "document_number", "issuer", "issue_date", "expiry_date", "comment", "scan_path", "is_sensitive"):
            assert restored[key] == original[key]

    def test_missing_fields_default_empty(self):
        api = document_to_api({"title": "X"})
        assert api["doc_type"] == ""
        assert api["is_sensitive"] is False
