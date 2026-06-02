"""
G3/G6/H7 — User profile, settings и личные документы (реальная БД).

JWT-зависимость get_current_user_email уже работает (Этап H).
Все endpoint требуют валидный access-токен.
"""
from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user_email
from backend.database import get_db
from backend.models import User, UserDocument

router = APIRouter(prefix="/api/user", tags=["user"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class UserProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    name: str
    role: str = "citizen"
    city: str = ""
    region: str = ""
    district: str = ""
    address: str = ""
    employment_status: str = ""
    has_children: bool = False
    owns_property: bool = False
    has_car: bool = False
    is_renter: bool = False
    interest_tags: list[str] = Field(default_factory=list)


class UserProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    city: str | None = None
    region: str | None = None
    district: str | None = None
    address: str | None = None
    employment_status: str | None = None
    has_children: bool | None = None
    owns_property: bool | None = None
    has_car: bool | None = None
    is_renter: bool | None = None
    interest_tags: list[str] | None = None


class UserDocumentIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    doc_type: str = ""
    number: str = ""
    issued_by: str = ""
    issued_date: str = ""
    expiry_date: str = ""
    is_sensitive: bool = False
    comment: str = ""
    scan_path: str = ""


class UserDocumentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    doc_type: str | None = None
    number: str | None = None
    issued_by: str | None = None
    issued_date: str | None = None
    expiry_date: str | None = None
    is_sensitive: bool | None = None
    comment: str | None = None
    scan_path: str | None = None


class UserDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    doc_type: str
    number: str
    issued_by: str
    issued_date: str
    expiry_date: str
    is_sensitive: bool
    comment: str
    scan_path: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_current_user(email: str = Depends(get_current_user_email), db: Session = Depends(get_db)) -> User:
    user = db.scalars(select(User).where(User.email == email)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден.")
    return user


def _profile_out(user: User) -> UserProfileOut:
    try:
        tags = json.loads(user.interest_tags) if user.interest_tags else []
        if not isinstance(tags, list):
            tags = []
    except (json.JSONDecodeError, TypeError):
        tags = []
    return UserProfileOut(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role_id,
        city=user.city,
        region=user.region,
        district=user.district,
        address=user.address,
        employment_status=user.employment_status,
        has_children=user.has_children,
        owns_property=user.owns_property,
        has_car=user.has_car,
        is_renter=user.is_renter,
        interest_tags=tags,
    )


def _owned_document(db: Session, user: User, doc_id: int) -> UserDocument:
    doc = db.scalars(
        select(UserDocument).where(UserDocument.id == doc_id, UserDocument.user_id == user.id)
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден.")
    return doc


# ---------------------------------------------------------------------------
# G3 — Profile & settings
# ---------------------------------------------------------------------------

@router.get("/profile", response_model=UserProfileOut)
def get_profile(user: User = Depends(get_current_user)):
    return _profile_out(user)


@router.put("/profile", response_model=UserProfileOut)
def update_profile(
    payload: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = payload.model_dump(exclude_none=True)
    tags = data.pop("interest_tags", None)
    for field, value in data.items():
        setattr(user, field, value)
    if tags is not None:
        user.interest_tags = json.dumps(tags, ensure_ascii=False)
    db.commit()
    db.refresh(user)
    return _profile_out(user)


@router.get("/settings")
def get_settings(user: User = Depends(get_current_user)):
    try:
        return json.loads(user.settings) if user.settings else {}
    except (json.JSONDecodeError, TypeError):
        return {}


@router.patch("/settings")
def update_settings(
    payload: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        current = json.loads(user.settings) if user.settings else {}
        if not isinstance(current, dict):
            current = {}
    except (json.JSONDecodeError, TypeError):
        current = {}
    current.update(payload or {})
    user.settings = json.dumps(current, ensure_ascii=False)
    db.commit()
    return current


# ---------------------------------------------------------------------------
# G6 — Личные документы (CRUD, владелец-only)
# ---------------------------------------------------------------------------

@router.get("/documents", response_model=list[UserDocumentOut])
def list_documents(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    docs = db.scalars(
        select(UserDocument).where(UserDocument.user_id == user.id).order_by(UserDocument.id.desc())
    ).all()
    return [UserDocumentOut.model_validate(d) for d in docs]


@router.post("/documents", response_model=UserDocumentOut, status_code=status.HTTP_201_CREATED)
def create_document(
    payload: UserDocumentIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = UserDocument(user_id=user.id, **payload.model_dump())
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return UserDocumentOut.model_validate(doc)


@router.put("/documents/{doc_id}", response_model=UserDocumentOut)
def update_document(
    doc_id: int,
    payload: UserDocumentUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = _owned_document(db, user, doc_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(doc, field, value)
    db.commit()
    db.refresh(doc)
    return UserDocumentOut.model_validate(doc)


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = _owned_document(db, user, doc_id)
    db.delete(doc)
    db.commit()
