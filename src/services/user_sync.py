"""
Мост между локальным форматом Flet-состояния и форматом backend API.

Имена полей в клиенте (document_type, document_number, issuer, issue_date)
отличаются от backend (doc_type, number, issued_by, issued_date). Здесь —
чистые мапперы + оркестрация pull/push через UserAPIClient.

Вычисляемые поля (status, icon, details) на клиенте не отправляются и
пересчитываются после загрузки соответствующими хелперами main.py.
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Documents (поля Flet != backend)
# ---------------------------------------------------------------------------

_DOC_FLET_TO_API = {
    "title": "title",
    "document_type": "doc_type",
    "document_number": "number",
    "issuer": "issued_by",
    "issue_date": "issued_date",
    "expiry_date": "expiry_date",
    "comment": "comment",
    "scan_path": "scan_path",
}


def document_to_api(doc: dict[str, Any]) -> dict[str, Any]:
    """Flet-документ -> payload backend (без вычисляемых status/icon/details)."""
    payload = {api_key: doc.get(flet_key, "") for flet_key, api_key in _DOC_FLET_TO_API.items()}
    payload["is_sensitive"] = bool(doc.get("is_sensitive", False))
    return payload


def document_from_api(api_doc: dict[str, Any]) -> dict[str, Any]:
    """Backend-документ -> Flet-документ (status/icon/details пересчитать на клиенте)."""
    flet = {flet_key: api_doc.get(api_key, "") for flet_key, api_key in _DOC_FLET_TO_API.items()}
    flet["id"] = api_doc.get("id")
    flet["is_sensitive"] = bool(api_doc.get("is_sensitive", False))
    return flet


def pull_documents(api_client) -> list[dict[str, Any]]:
    """Загрузить все документы пользователя в Flet-формате."""
    return [document_from_api(d) for d in api_client.list_documents()]


def push_document(api_client, doc: dict[str, Any]) -> dict[str, Any]:
    """Создать (нет числового id) или обновить документ. Возвращает Flet-формат."""
    payload = document_to_api(doc)
    doc_id = doc.get("id")
    if isinstance(doc_id, int):
        result = api_client.update_document(doc_id, payload)
    else:
        result = api_client.create_document(payload)
    return document_from_api(result)


def delete_document(api_client, doc: dict[str, Any]) -> None:
    doc_id = doc.get("id")
    if isinstance(doc_id, int):
        api_client.delete_document(doc_id)


# ---------------------------------------------------------------------------
# Taxes / utility / notifications / situations — имена полей совпадают с API,
# мапперы — тонкие проходы (оставлены для единообразия и будущих отличий).
# ---------------------------------------------------------------------------

def pull_taxes(api_client) -> list[dict[str, Any]]:
    return api_client.list_taxes()


def pull_utility_accounts(api_client) -> list[dict[str, Any]]:
    return api_client.list_utility_accounts()


def pull_notifications(api_client) -> list[dict[str, Any]]:
    return api_client.list_notifications()


def pull_situations(api_client) -> list[dict[str, Any]]:
    return api_client.list_situations()


def pull_all(api_client) -> dict[str, Any]:
    """Полная выгрузка пользовательских данных в формате для Flet-состояния."""
    return {
        "documents": pull_documents(api_client),
        "situations": pull_situations(api_client),
        "notifications": pull_notifications(api_client),
        "utility_accounts": pull_utility_accounts(api_client),
        "taxes": pull_taxes(api_client),
    }
