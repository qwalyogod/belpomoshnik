"""Pure mapper tests for Flet <-> backend document field translation."""
from services.user_sync import document_from_api, document_to_api


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
