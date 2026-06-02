"""
G8/G9 — ЖКХ-трекер (счета + платежи) и налоговые обязательства.

JWT обязателен, доступ только к своим объектам. ID — серверные uuid.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.api.user import get_current_user
from backend.database import get_db
from backend.models import TaxObligation, User, UtilityAccount, UtilityPayment

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


class PaymentUpdate(BaseModel):
    period: str | None = None
    readings_date: str | None = None
    payment_date: str | None = None
    amount: float | None = None
    status: str | None = None
    readings_deadline: str | None = None
    payment_deadline: str | None = None
    comment: str | None = None


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


class AccountIn(BaseModel):
    address: str = ""
    account_number: str = ""
    provider: str = ""


class AccountUpdate(BaseModel):
    address: str | None = None
    account_number: str | None = None
    provider: str | None = None


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    address: str
    account_number: str
    provider: str
    payments: list[PaymentOut] = Field(default_factory=list)


class TaxIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    user_type: str = "individual"
    deadline: str = ""
    amount: float = 0.0
    receipt_path: str = ""
    status: str = "Предстоит"
    period: str = ""
    comment: str = ""


class TaxUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    user_type: str | None = None
    deadline: str | None = None
    amount: float | None = None
    receipt_path: str | None = None
    status: str | None = None
    period: str | None = None
    comment: str | None = None


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


# ---------------------------------------------------------------------------
# G8 — Utility accounts + payments
# ---------------------------------------------------------------------------

@router.get("/utility/accounts", response_model=list[AccountOut])
def list_accounts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    accounts = db.scalars(
        select(UtilityAccount).where(UtilityAccount.user_id == user.id).order_by(UtilityAccount.created_at.desc())
    ).all()
    return [AccountOut.model_validate(a) for a in accounts]


@router.post("/utility/accounts", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    acc = UtilityAccount(id=_new_id(), user_id=user.id, **payload.model_dump())
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return AccountOut.model_validate(acc)


@router.put("/utility/accounts/{account_id}", response_model=AccountOut)
def update_account(
    account_id: str, payload: AccountUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    acc = _owned_account(db, user, account_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(acc, field, value)
    db.commit()
    db.refresh(acc)
    return AccountOut.model_validate(acc)


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
    return AccountOut.model_validate(acc)


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
