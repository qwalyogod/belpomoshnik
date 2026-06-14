"""
G8/G9 — ЖКХ-трекер (счета + платежи) и налоговые обязательства.

JWT обязателен, доступ только к своим объектам. ID — серверные uuid.
"""
from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.api.user import get_current_user
from backend.database import get_db
from backend.models import (
    TaxObligation,
    User,
    UtilityAccount,
    UtilityPayment,
    UtilityRequest,
)

router = APIRouter(prefix="/api/user", tags=["trackers"])


def _new_id() -> str:
    return uuid.uuid4().hex


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PaymentIn(BaseModel):
    period: str = ""
    readings_date: str = ""
    payment_date: str = ""
    amount: float = 0.0
    status: str = "Ожидает"
    readings_deadline: str = ""
    payment_deadline: str = ""
    comment: str = ""
    # Промпт 2: breakdown как сериализованный JSON-массив.
    breakdown_json: str = "[]"
    source: str = "manual"
    receipt_path: str = ""


class PaymentUpdate(BaseModel):
    period: str | None = None
    readings_date: str | None = None
    payment_date: str | None = None
    amount: float | None = None
    status: str | None = None
    readings_deadline: str | None = None
    payment_deadline: str | None = None
    comment: str | None = None
    breakdown_json: str | None = None
    source: str | None = None
    receipt_path: str | None = None


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    account_id: str
    period: str
    readings_date: str
    payment_date: str
    amount: float
    status: str
    readings_deadline: str
    payment_deadline: str
    comment: str
    breakdown_json: str = "[]"
    source: str = "manual"
    receipt_path: str = ""


class AccountIn(BaseModel):
    address: str = ""
    account_number: str = ""
    provider: str = ""
    # Промпт 2: расширение модели.
    label: str = ""
    service_types: list[str] = Field(default_factory=list)
    payer_name: str = ""
    manual_mode: bool = True
    last_sync_note: str = ""


class AccountUpdate(BaseModel):
    address: str | None = None
    account_number: str | None = None
    provider: str | None = None
    label: str | None = None
    service_types: list[str] | None = None
    payer_name: str | None = None
    manual_mode: bool | None = None
    last_sync_note: str | None = None


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    address: str
    account_number: str
    provider: str
    payments: list[PaymentOut] = Field(default_factory=list)
    label: str = ""
    # Промпт 2: возвращаем как массив строк (десериализуем из service_types JSON).
    service_types: list[str] = Field(default_factory=list)
    payer_name: str = ""
    manual_mode: bool = True
    last_sync_note: str = ""


class TaxIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    user_type: str = "individual"
    deadline: str = ""
    amount: float = 0.0
    receipt_path: str = ""
    status: str = "Предстоит"
    period: str = ""
    comment: str = ""
    # Промпт 2: расширение.
    tax_type: str = "other"
    source: str = "manual"
    recipient: str = ""
    unp: str = ""
    notice_number: str = ""
    payment_code: str = ""
    paid_at: str = ""
    external_url: str = ""
    help_text: str = ""


class TaxUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    user_type: str | None = None
    deadline: str | None = None
    amount: float | None = None
    receipt_path: str | None = None
    status: str | None = None
    period: str | None = None
    comment: str | None = None
    tax_type: str | None = None
    source: str | None = None
    recipient: str | None = None
    unp: str | None = None
    notice_number: str | None = None
    payment_code: str | None = None
    paid_at: str | None = None
    external_url: str | None = None
    help_text: str | None = None


class TaxOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_type: str
    title: str
    deadline: str
    amount: float
    receipt_path: str
    status: str
    period: str
    comment: str
    tax_type: str = "other"
    source: str = "manual"
    recipient: str = ""
    unp: str = ""
    notice_number: str = ""
    payment_code: str = ""
    paid_at: str = ""
    external_url: str = ""
    help_text: str = ""


# Промпт 2: заявки ЖКХ 115.
_UTILITY_REQUEST_CATEGORIES = {"water", "heating", "electricity", "waste_yard", "entrance", "elevator", "other"}
_UTILITY_REQUEST_STATUSES = {"draft", "sent", "in_progress", "resolved", "rejected"}


class UtilityRequestIn(BaseModel):
    account_id: str | None = None
    address: str = ""
    title: str = Field(min_length=1, max_length=255)
    category: str = "other"
    description: str = ""
    status: str = "draft"
    external_number: str = ""
    external_url: str = ""
    target_service: str = ""


class UtilityRequestUpdate(BaseModel):
    account_id: str | None = None
    address: str | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = None
    description: str | None = None
    status: str | None = None
    external_number: str | None = None
    external_url: str | None = None
    target_service: str | None = None


class UtilityRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    account_id: str | None = None
    address: str
    title: str
    category: str
    description: str
    status: str
    external_number: str
    external_url: str
    target_service: str
    created_at: str | None = None
    updated_at: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _owned_account(db: Session, user: User, account_id: str) -> UtilityAccount:
    acc = db.scalars(
        select(UtilityAccount).where(UtilityAccount.id == account_id, UtilityAccount.user_id == user.id)
    ).first()
    if not acc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Лицевой счёт не найден.")
    return acc


def _owned_payment(db: Session, user: User, payment_id: str) -> UtilityPayment:
    pay = db.scalars(
        select(UtilityPayment)
        .join(UtilityAccount, UtilityPayment.account_id == UtilityAccount.id)
        .where(UtilityPayment.id == payment_id, UtilityAccount.user_id == user.id)
    ).first()
    if not pay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платёж не найден.")
    return pay


def _owned_tax(db: Session, user: User, tax_id: str) -> TaxObligation:
    tax = db.scalars(
        select(TaxObligation).where(TaxObligation.id == tax_id, TaxObligation.user_id == user.id)
    ).first()
    if not tax:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Обязательство не найдено.")
    return tax


def _owned_request(db: Session, user: User, request_id: str) -> UtilityRequest:
    req = db.scalars(
        select(UtilityRequest).where(UtilityRequest.id == request_id, UtilityRequest.user_id == user.id)
    ).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена.")
    return req


def _decode_service_types(raw: str) -> list[str]:
    try:
        value = json.loads(raw or "[]")
        return [str(x) for x in value] if isinstance(value, list) else []
    except (ValueError, TypeError):
        return []


def _account_out(acc: UtilityAccount) -> AccountOut:
    return AccountOut(
        id=acc.id,
        address=acc.address,
        account_number=acc.account_number,
        provider=acc.provider,
        payments=[PaymentOut.model_validate(p) for p in acc.payments],
        label=acc.label or "",
        service_types=_decode_service_types(acc.service_types),
        payer_name=acc.payer_name or "",
        manual_mode=bool(acc.manual_mode),
        last_sync_note=acc.last_sync_note or "",
    )


def _request_out(req: UtilityRequest) -> UtilityRequestOut:
    return UtilityRequestOut(
        id=req.id,
        account_id=req.account_id,
        address=req.address,
        title=req.title,
        category=req.category,
        description=req.description,
        status=req.status,
        external_number=req.external_number,
        external_url=req.external_url,
        target_service=req.target_service,
        created_at=req.created_at.isoformat() if req.created_at else None,
        updated_at=req.updated_at.isoformat() if req.updated_at else None,
    )


# ---------------------------------------------------------------------------
# G8 — Utility accounts + payments
# ---------------------------------------------------------------------------

@router.get("/utility/accounts", response_model=list[AccountOut])
def list_accounts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    accounts = db.scalars(
        select(UtilityAccount).where(UtilityAccount.user_id == user.id).order_by(UtilityAccount.created_at.desc())
    ).all()
    return [_account_out(a) for a in accounts]


def _normalize_account_payload(data: dict) -> dict:
    """service_types в БД хранится как JSON-строка; в API — массив."""
    if "service_types" in data and isinstance(data["service_types"], list):
        data["service_types"] = json.dumps(data["service_types"], ensure_ascii=False)
    return data


@router.post("/utility/accounts", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = _normalize_account_payload(payload.model_dump())
    acc = UtilityAccount(id=_new_id(), user_id=user.id, **data)
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return _account_out(acc)


@router.put("/utility/accounts/{account_id}", response_model=AccountOut)
def update_account(
    account_id: str, payload: AccountUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    acc = _owned_account(db, user, account_id)
    data = _normalize_account_payload(payload.model_dump(exclude_none=True))
    for field, value in data.items():
        setattr(acc, field, value)
    db.commit()
    db.refresh(acc)
    return _account_out(acc)


@router.delete("/utility/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(_owned_account(db, user, account_id))
    db.commit()


@router.post("/utility/accounts/{account_id}/payments", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def add_payment(
    account_id: str, payload: PaymentIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    acc = _owned_account(db, user, account_id)
    db.add(UtilityPayment(id=_new_id(), account_id=acc.id, **payload.model_dump()))
    db.commit()
    db.refresh(acc)
    return _account_out(acc)


@router.patch("/utility/payments/{payment_id}", response_model=PaymentOut)
def update_payment(
    payment_id: str, payload: PaymentUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    pay = _owned_payment(db, user, payment_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(pay, field, value)
    db.commit()
    db.refresh(pay)
    return PaymentOut.model_validate(pay)


@router.delete("/utility/payments/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(payment_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(_owned_payment(db, user, payment_id))
    db.commit()


# ---------------------------------------------------------------------------
# G9 — Tax obligations
# ---------------------------------------------------------------------------

@router.get("/taxes", response_model=list[TaxOut])
def list_taxes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.scalars(
        select(TaxObligation).where(TaxObligation.user_id == user.id).order_by(TaxObligation.created_at.desc())
    ).all()
    return [TaxOut.model_validate(t) for t in items]


@router.post("/taxes", response_model=TaxOut, status_code=status.HTTP_201_CREATED)
def create_tax(payload: TaxIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tax = TaxObligation(id=_new_id(), user_id=user.id, **payload.model_dump())
    db.add(tax)
    db.commit()
    db.refresh(tax)
    return TaxOut.model_validate(tax)


@router.put("/taxes/{tax_id}", response_model=TaxOut)
def update_tax(tax_id: str, payload: TaxUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tax = _owned_tax(db, user, tax_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(tax, field, value)
    db.commit()
    db.refresh(tax)
    return TaxOut.model_validate(tax)


@router.delete("/taxes/{tax_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tax(tax_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(_owned_tax(db, user, tax_id))
    db.commit()


# ---------------------------------------------------------------------------
# Промпт 2 — Заявки 115 (UtilityRequest)
# ---------------------------------------------------------------------------

@router.get("/utility/requests", response_model=list[UtilityRequestOut])
def list_utility_requests(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.scalars(
        select(UtilityRequest)
        .where(UtilityRequest.user_id == user.id)
        .order_by(UtilityRequest.created_at.desc())
    ).all()
    return [_request_out(r) for r in items]


def _validate_request_fields(data: dict) -> None:
    if "category" in data and data["category"] not in _UTILITY_REQUEST_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Категория должна быть одной из: {sorted(_UTILITY_REQUEST_CATEGORIES)}",
        )
    if "status" in data and data["status"] not in _UTILITY_REQUEST_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Статус должен быть одним из: {sorted(_UTILITY_REQUEST_STATUSES)}",
        )


@router.post("/utility/requests", response_model=UtilityRequestOut, status_code=status.HTTP_201_CREATED)
def create_utility_request(
    payload: UtilityRequestIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = payload.model_dump()
    _validate_request_fields(data)
    # Если account_id указан — проверяем владельца.
    if data.get("account_id"):
        _owned_account(db, user, data["account_id"])
    req = UtilityRequest(id=_new_id(), user_id=user.id, **data)
    db.add(req)
    db.commit()
    db.refresh(req)
    return _request_out(req)


@router.put("/utility/requests/{request_id}", response_model=UtilityRequestOut)
def update_utility_request(
    request_id: str,
    payload: UtilityRequestUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    req = _owned_request(db, user, request_id)
    data = payload.model_dump(exclude_none=True)
    _validate_request_fields(data)
    if data.get("account_id"):
        _owned_account(db, user, data["account_id"])
    for field, value in data.items():
        setattr(req, field, value)
    db.commit()
    db.refresh(req)
    return _request_out(req)


@router.delete("/utility/requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_utility_request(
    request_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.delete(_owned_request(db, user, request_id))
    db.commit()
