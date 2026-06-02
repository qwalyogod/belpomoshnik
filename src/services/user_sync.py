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

def _is_server_id(value: Any) -> bool:
    """Server-сгенерированный id = uuid4().hex (32 hex-символа).

    Локальные Flet-id имеют префикс (tax-…, util-…, upay-…, sit-…) и не
    проходят эту проверку — значит объект ещё не синхронизирован.
    """
    return isinstance(value, str) and len(value) == 32 and all(c in "0123456789abcdef" for c in value)


_TAX_FIELDS = ("user_type", "title", "deadline", "receipt_path", "status", "period", "comment")


def _tax_payload(tax: dict[str, Any]) -> dict[str, Any]:
    payload = {k: tax.get(k, "") for k in _TAX_FIELDS}
    try:
        payload["amount"] = float(tax.get("amount") or 0)
    except (TypeError, ValueError):
        payload["amount"] = 0.0
    return payload


def pull_taxes(api_client) -> list[dict[str, Any]]:
    return api_client.list_taxes()


def push_tax(api_client, tax: dict[str, Any]) -> dict[str, Any]:
    """Создать (локальный id) или обновить (server id) налог. Возвращает server-объект."""
    payload = _tax_payload(tax)
    if _is_server_id(tax.get("id")):
        return api_client.update_tax(tax["id"], payload)
    return api_client.create_tax(payload)


def delete_tax(api_client, tax: dict[str, Any]) -> None:
    if _is_server_id(tax.get("id")):
        api_client.delete_tax(tax["id"])


_ACCOUNT_FIELDS = ("address", "account_number", "provider")
_PAYMENT_FIELDS = (
    "period", "readings_date", "payment_date", "status",
    "readings_deadline", "payment_deadline", "comment",
)


def _account_payload(account: dict[str, Any]) -> dict[str, Any]:
    return {k: account.get(k, "") for k in _ACCOUNT_FIELDS}


def _payment_payload(payment: dict[str, Any]) -> dict[str, Any]:
    payload = {k: payment.get(k, "") for k in _PAYMENT_FIELDS}
    try:
        payload["amount"] = float(payment.get("amount") or 0)
    except (TypeError, ValueError):
        payload["amount"] = 0.0
    return payload


def pull_utility_accounts(api_client) -> list[dict[str, Any]]:
    return api_client.list_utility_accounts()


def pull_utility(api_client) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Разложить вложенный ответ API в плоские (accounts, payments) для Flet."""
    accounts: list[dict[str, Any]] = []
    payments: list[dict[str, Any]] = []
    for acc in api_client.list_utility_accounts():
        accounts.append({"id": acc["id"], **{k: acc.get(k, "") for k in _ACCOUNT_FIELDS}})
        for p in acc.get("payments", []) or []:
            payments.append({**p, "account_id": acc["id"]})
    return accounts, payments


def push_utility_account(api_client, account: dict[str, Any]) -> dict[str, Any]:
    """Создать/обновить счёт. Возвращает server-счёт (с payments)."""
    payload = _account_payload(account)
    if _is_server_id(account.get("id")):
        return api_client.update_utility_account(account["id"], payload)
    return api_client.create_utility_account(payload)


def delete_utility_account(api_client, account: dict[str, Any]) -> None:
    if _is_server_id(account.get("id")):
        api_client.delete_utility_account(account["id"])


def push_utility_payment(api_client, payment: dict[str, Any], account_server_id: str) -> dict[str, Any] | None:
    """Создать/обновить платёж. Для создания нужен server-id счёта.

    Возвращает server-платёж при создании (id меняется) либо None,
    если счёт ещё не синхронизирован.
    """
    payload = _payment_payload(payment)
    if _is_server_id(payment.get("id")):
        return api_client.update_utility_payment(payment["id"], payload)
    if not _is_server_id(account_server_id):
        return None
    account = api_client.add_utility_payment(account_server_id, payload)
    new_payments = account.get("payments", []) or []
    # последний добавленный платёж с совпадающим периодом
    for p in reversed(new_payments):
        if p.get("period") == payload.get("period"):
            return {**p, "account_id": account_server_id}
    return None


def delete_utility_payment(api_client, payment: dict[str, Any]) -> None:
    if _is_server_id(payment.get("id")):
        api_client.delete_utility_payment(payment["id"])


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
