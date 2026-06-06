"""
G3/G6/H7 — User profile, settings и личные документы (реальная БД).

JWT-зависимость get_current_user_email уже работает (Этап H).
Все endpoint требуют валидный access-токен.
"""
from __future__ import annotations

import json
import os
import re
import secrets
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user_email
from backend.database import get_db
from backend.models import User, UserDocument

router = APIRouter(prefix="/api/user", tags=["user"])

# v0.3: папка для сканов документов. Создаётся при первом аплоаде.
# Структура: data/uploads/documents/{user_id}/{doc_id}/{token}.pdf
DOCUMENT_SCAN_DIR = Path(os.getenv("DOCUMENT_SCAN_DIR", "data/uploads/documents"))
DOCUMENT_SCAN_MAX_BYTES = int(os.getenv("DOCUMENT_SCAN_MAX_BYTES", str(5 * 1024 * 1024)))  # 5MB
_SAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")


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
    # v0.4: кастомные поля для doc_type='other'. JSON-строка с массивом
    # {name, value}. Ограничиваем 2000 символами на стороне БД; тут
    # дополнительно валидируем — должна быть либо пустая строка, либо
    # валидный JSON.
    custom_fields_json: str = Field(default="", max_length=2000)


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
    custom_fields_json: str | None = Field(default=None, max_length=2000)


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
    custom_fields_json: str = ""


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
    doc = UserDocument(user_id=user.id, **_validate_doc_payload(payload.model_dump()))
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
    validated = _validate_doc_payload(payload.model_dump(exclude_none=True))
    for field, value in validated.items():
        setattr(doc, field, value)
    db.commit()
    db.refresh(doc)
    return UserDocumentOut.model_validate(doc)


def _validate_doc_payload(payload: dict) -> dict:
    """v0.4: проверить, что custom_fields_json — пустая строка или валидный JSON
    массив объектов {name, value}. Без проверки фронт мог бы сохранить мусор."""
    raw = (payload.get("custom_fields_json") or "").strip()
    if not raw:
        payload["custom_fields_json"] = ""
        return payload
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"custom_fields_json не валидный JSON: {exc}",
        ) from exc
    if not isinstance(parsed, list):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="custom_fields_json должен быть массивом.",
        )
    # Мягкая нормализация: убеждаемся, что элементы — dict с name/value
    normalized: list[dict] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()[:120]
        value = str(item.get("value", "")).strip()[:500]
        if not name:
            continue
        normalized.append({"name": name, "value": value})
    payload["custom_fields_json"] = json.dumps(normalized, ensure_ascii=False)
    return payload


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = _owned_document(db, user, doc_id)
    # Подчищаем связанные PDF сканы
    if doc.scan_path:
        scan_full = Path(doc.scan_path)
        if scan_full.exists():
            try:
                scan_full.unlink()
            except OSError:
                pass
        # и родительскую папку (если пустая)
        try:
            scan_full.parent.rmdir()
        except OSError:
            pass
    db.delete(doc)
    db.commit()


# ---------------------------------------------------------------------------
# v0.3 — Загрузка скана документа (PDF)
# ---------------------------------------------------------------------------

@router.post("/documents/{doc_id}/scan")
async def upload_document_scan(
    doc_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Загрузить PDF-скан к документу. Только владелец.

    Сохраняет в `<DOCUMENT_SCAN_DIR>/<user_id>/<doc_id>/<token>.pdf`,
    пишет относительный путь в `UserDocument.scan_path`. Возвращает
    публичный URL для превью (`/uploads/documents/...`).
    """
    # 1) Ownership check — общий helper не используется потому что мы хотим
    # отдать 404 (а не 403) на чужих, чтобы не палить существование id.
    doc = db.scalars(
        select(UserDocument).where(
            UserDocument.id == doc_id,
            UserDocument.user_id == user.id,
        )
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден.")

    # 2) Content-Type — только PDF. iOS Safari WebView может прислать
    # application/octet-stream если пользователь ткнул «Открыть в…», поэтому
    # дополнительно проверяем расширение.
    ctype = (file.content_type or "").lower()
    filename = file.filename or ""
    is_pdf = ctype in ("application/pdf", "application/x-pdf") or filename.lower().endswith(".pdf")
    if not is_pdf:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Поддерживается только PDF.",
        )

    # 3) Читаем в памяти и проверяем размер. multipart уже отдал body,
    # поэтому дополнительного чтения не делаем.
    body = await file.read()
    if not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Файл пустой.")
    if len(body) > DOCUMENT_SCAN_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл больше {DOCUMENT_SCAN_MAX_BYTES // (1024*1024)} МБ.",
        )
    # Magic-bytes: %PDF-
    if not body.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Содержимое файла не похоже на PDF.",
        )

    # 4) Куда пишем: data/uploads/documents/<user_id>/<doc_id>/<token>.pdf
    user_dir = DOCUMENT_SCAN_DIR / str(user.id) / str(doc_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(12)
    target = user_dir / f"{token}.pdf"
    target.write_bytes(body)

    # 5) Старое (если было) — удалить
    if doc.scan_path:
        old = Path(doc.scan_path)
        if old.exists() and old != target:
            try:
                old.unlink()
            except OSError:
                pass

    # 6) Путь в БД храним относительным (для переносимости между окружениями)
    rel_path = str(target)
    doc.scan_path = rel_path
    db.commit()
    db.refresh(doc)

    return {
        "doc_id": doc.id,
        "scan_url": f"/uploads/documents/{user.id}/{doc.id}/{token}.pdf",
        "scan_size": len(body),
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
    }


@router.delete("/documents/{doc_id}/scan", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_scan(
    doc_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Удалить скан документа (но не сам документ)."""
    doc = db.scalars(
        select(UserDocument).where(
            UserDocument.id == doc_id,
            UserDocument.user_id == user.id,
        )
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден.")
    if doc.scan_path:
        p = Path(doc.scan_path)
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass
        try:
            p.parent.rmdir()
        except OSError:
            pass
    doc.scan_path = ""
    db.commit()
