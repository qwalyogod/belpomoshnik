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
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user_email
from backend.auth import hash_password, verify_password
from backend.database import get_db
from backend.models import User, UserDocument, UserNote
from backend.schemas import (
    USER_NOTE_CATEGORIES,
    UserNoteCreate,
    UserNoteOut,
    UserNoteUpdate,
)
from backend.security import (
    DocumentCryptoError,
    decrypt_field,
    encrypt_field,
    encrypt_file,
    decrypt_file,
)

router = APIRouter(prefix="/api/user", tags=["user"])

# Промпт 1: сканы храним ВНЕ публичной /uploads — статический mount удалён.
# Структура: data/secure/documents/{user_id}/{doc_id}/{token}.bin (Fernet blob).
DOCUMENT_SCAN_DIR = Path(os.getenv("DOCUMENT_SCAN_DIR", "data/secure/documents"))
DOCUMENT_SCAN_MAX_BYTES = int(os.getenv("DOCUMENT_SCAN_MAX_BYTES", str(8 * 1024 * 1024)))  # 8MB
_SAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")

# Разрешённые MIME-типы для скана. Магия (magic bytes) — главная проверка.
_DOC_SCAN_ALLOWED_MIME = {
    "application/pdf",
    "application/x-pdf",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}


def _detect_scan_mime(body: bytes) -> str | None:
    """По magic bytes определить MIME. None — формат не поддерживается."""
    if body.startswith(b"%PDF-"):
        return "application/pdf"
    if body[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if body[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if body[:4] == b"RIFF" and body[8:12] == b"WEBP":
        return "image/webp"
    return None

# v1.2: папка для аватаров. Лежит ВНУТРИ data/uploads, поэтому отдаётся тем же
# StaticFiles-mount `/uploads`, что и остальной контент (отдельный mount не нужен).
# Структура: data/uploads/avatars/{user_id}/{token}.{ext}. Один аватар на юзера —
# при загрузке нового папка юзера очищается.
AVATAR_DIR = Path(os.getenv("AVATAR_DIR", "data/uploads/avatars"))
AVATAR_MAX_BYTES = int(os.getenv("AVATAR_MAX_BYTES", str(8 * 1024 * 1024)))  # 8MB
# Разрешённые форматы аватара: jpg/jpeg, png, webp. Ключ — сигнатура (magic bytes),
# значение — расширение, под которым сохраняем файл.
_AVATAR_ALLOWED_CTYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}


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
    # v1.1 (P4): до 5 адресов пользователя (label / region / district /
    # city / street / isPrimary). Хранится как JSON-строка, в адаптере
    # парсится в массив объектов.
    addresses: list[dict] = Field(default_factory=list)
    # v1.2: публичный путь к аватару (/uploads/avatars/...) или "".
    avatar_url: str = ""


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
    # v1.1 (P4): список адресов. Бэк принимает уже валидный массив,
    # нормализует и сериализует обратно в JSON-строку для хранения.
    addresses: list[dict] | None = None


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


class UserDocumentScanMeta(BaseModel):
    has_scan: bool = False
    mime_type: str = ""
    size: int = 0
    original_filename: str = ""
    uploaded_at: str = ""
    # download_url требует JWT — не публичный путь.
    download_url: str = ""


class UserDocumentOut(BaseModel):
    """Промпт 1: чувствительные поля приходят расшифрованными (только владельцу)."""
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
    # Backward-compat: оставляем поле для уже выпущенного фронта, но
    # фактически здесь пусто. UI должен смотреть на `scan`.
    scan_path: str = ""
    custom_fields_json: str = ""
    encrypted_at_rest: bool = True
    scan: UserDocumentScanMeta = Field(default_factory=UserDocumentScanMeta)


class UserEmailChangeIn(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=1, max_length=255)


class UserPasswordChangeIn(BaseModel):
    old_password: str = Field(min_length=1, max_length=255)
    new_password: str = Field(min_length=8, max_length=255)


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
    try:
        addresses = json.loads(user.addresses_json) if user.addresses_json else []
        if not isinstance(addresses, list):
            addresses = []
    except (json.JSONDecodeError, TypeError):
        addresses = []
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
        addresses=addresses,
        avatar_url=user.avatar_url,
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
    addresses = data.pop("addresses", None)
    for field, value in data.items():
        setattr(user, field, value)
    if tags is not None:
        user.interest_tags = json.dumps(tags, ensure_ascii=False)
    if addresses is not None:
        user.addresses_json = json.dumps(
            _validate_addresses_payload(addresses),
            ensure_ascii=False,
        )
    db.commit()
    db.refresh(user)
    return _profile_out(user)


@router.patch("/account/email", response_model=UserProfileOut)
def change_email(
    payload: UserEmailChangeIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    next_email = payload.email.strip().lower()
    if "@" not in next_email or "." not in next_email.split("@")[-1]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Укажите корректный email.")
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Пароль указан неверно.")
    existing = db.scalars(select(User).where(User.email == next_email, User.id != user.id)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пользователь с таким email уже существует.")
    user.email = next_email
    db.commit()
    db.refresh(user)
    return _profile_out(user)


@router.patch("/account/password")
def change_password(
    payload: UserPasswordChangeIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.old_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Старый пароль указан неверно.")
    if verify_password(payload.new_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Новый пароль должен отличаться от старого.")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"ok": True}


def _detect_avatar_ext(body: bytes) -> str | None:
    """Определить формат картинки по magic-bytes. Возвращает расширение или None."""
    if body[:3] == b"\xff\xd8\xff":
        return "jpg"
    if body[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if body[:4] == b"RIFF" and body[8:12] == b"WEBP":
        return "webp"
    return None


def _clear_avatar_dir(user_id: int) -> None:
    """Удалить все файлы аватара пользователя (один аватар на юзера)."""
    user_dir = AVATAR_DIR / str(user_id)
    if not user_dir.exists():
        return
    for item in user_dir.iterdir():
        try:
            item.unlink()
        except OSError:
            pass


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Загрузить уже обрезанный аватар (jpg/png/webp).

    Клиент присылает квадратную картинку из редактора-кропера. Сохраняем в
    `data/uploads/avatars/<user_id>/<token>.<ext>`, пишем публичный путь в
    `users.avatar_url`. Старый файл затираем. Возвращает `{ "avatar_url": ... }`.
    """
    # 1) Размер. Читаем body один раз (multipart уже в памяти).
    body = await file.read()
    if not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Файл пустой.")
    if len(body) > AVATAR_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл больше {AVATAR_MAX_BYTES // (1024 * 1024)} МБ.",
        )

    # 2) Формат: сверяем magic-bytes (надёжнее content-type, который iOS WebView
    # может прислать как application/octet-stream). content-type — мягкая проверка.
    ext = _detect_avatar_ext(body)
    ctype = (file.content_type or "").lower()
    if ext is None or (ctype and ctype not in _AVATAR_ALLOWED_CTYPES and not ctype.startswith("application/octet-stream")):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Поддерживаются только JPG, PNG и WEBP.",
        )

    # 3) Пишем новый файл, предварительно очистив старый аватар юзера.
    _clear_avatar_dir(user.id)
    user_dir = AVATAR_DIR / str(user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(12)
    target = user_dir / f"{token}.{ext}"
    target.write_bytes(body)

    # 4) Публичный путь (токен в имени = кэш-бастинг при смене аватара).
    rel_url = f"/uploads/avatars/{user.id}/{token}.{ext}"
    user.avatar_url = rel_url
    db.commit()
    db.refresh(user)
    return {"avatar_url": rel_url, "size": len(body)}


@router.delete("/avatar", status_code=status.HTTP_204_NO_CONTENT)
def delete_avatar(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Удалить аватар пользователя (файл + ссылку в БД)."""
    _clear_avatar_dir(user.id)
    user.avatar_url = ""
    db.commit()
    return None


@router.get("/settings")
def get_settings(user: User = Depends(get_current_user)):
    try:
        return json.loads(user.settings) if user.settings else {}
    except (json.JSONDecodeError, TypeError):
        return {}


# Allow-list ключей для PATCH /settings. Защищает от подделки внутренних
# флагов через этот endpoint. Расширять по мере появления новых настроек.
# Явно запрещены: role, is_admin, is_active, password, is_test_account.
_ALLOWED_SETTINGS_KEYS: set[str] = {
    "language",
    "lang",
    "theme",
    "themeMode",
    "dark_theme",
    "largeFont",
    "highContrast",
    "reminderLeadDays",
    "doc_reminder_days",
    "preferredSourceIds",
    "maskDocuments",
    "notifications",
    "address",
    "digestTime",
    "accessibility",
}


def _is_allowed_settings_key(k: str) -> bool:
    if k in _ALLOWED_SETTINGS_KEYS:
        return True
    root = k.split(".", 1)[0]
    return root in {"notifications", "accessibility", "ui", "privacy"}


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
    # Фильтруем payload по allow-list — лишние/потенциально опасные ключи
    # (например, role, is_admin) отбрасываются.
    safe = {k: v for k, v in (payload or {}).items() if _is_allowed_settings_key(k)}
    current.update(safe)
    user.settings = json.dumps(current, ensure_ascii=False)
    db.commit()
    return current


# ---------------------------------------------------------------------------
# G6 — Личные документы (CRUD, владелец-only) — Промпт 1: encryption at-rest
# ---------------------------------------------------------------------------

# Поля, которые при наличии encrypted-варианта НЕ возвращаются из plain.
# Read-путь: encrypted > plain (fallback) > "".
# Write-путь: всегда пишем в encrypted, plain зануляем.
_SENSITIVE_DOC_FIELDS = ("number", "issued_by", "comment", "custom_fields_json")


def _doc_to_out(doc: UserDocument) -> UserDocumentOut:
    """Собрать UserDocumentOut, расшифровывая чувствительные поля."""
    number = decrypt_field(doc.number_encrypted) or doc.number or ""
    issued_by = decrypt_field(doc.issued_by_encrypted) or doc.issued_by or ""
    comment = decrypt_field(doc.comment_encrypted) or doc.comment or ""
    custom = decrypt_field(doc.custom_fields_encrypted) or doc.custom_fields_json or ""

    scan_meta = UserDocumentScanMeta()
    if doc.scan_encrypted_path:
        scan_meta = UserDocumentScanMeta(
            has_scan=True,
            mime_type=doc.scan_mime_type or "application/pdf",
            size=doc.scan_size or 0,
            original_filename=doc.scan_original_filename or "",
            uploaded_at=doc.scan_uploaded_at.isoformat() if doc.scan_uploaded_at else "",
            download_url=f"/api/user/documents/{doc.id}/scan",
        )

    return UserDocumentOut(
        id=doc.id,
        title=doc.title,
        doc_type=doc.doc_type,
        number=number,
        issued_by=issued_by,
        issued_date=doc.issued_date,
        expiry_date=doc.expiry_date,
        is_sensitive=doc.is_sensitive,
        comment=comment,
        scan_path="",  # пустой: для UI обязателен `scan.download_url`
        custom_fields_json=custom,
        encrypted_at_rest=True,
        scan=scan_meta,
    )


def _apply_doc_payload(doc: UserDocument, validated: dict) -> None:
    """Записать поля документа: чувствительные → encrypted, прочие — как есть."""
    for field, value in validated.items():
        if field in _SENSITIVE_DOC_FIELDS:
            enc_attr = {
                "number": "number_encrypted",
                "issued_by": "issued_by_encrypted",
                "comment": "comment_encrypted",
                "custom_fields_json": "custom_fields_encrypted",
            }[field]
            try:
                setattr(doc, enc_attr, encrypt_field(value or ""))
            except DocumentCryptoError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Шифрование документов не настроено на сервере.",
                ) from exc
            # Plain зануляем — больше не храним чувствительное открытым текстом.
            setattr(doc, field, "")
        else:
            setattr(doc, field, value)


@router.get("/documents", response_model=list[UserDocumentOut])
def list_documents(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    docs = db.scalars(
        select(UserDocument).where(UserDocument.user_id == user.id).order_by(UserDocument.id.desc())
    ).all()
    return [_doc_to_out(d) for d in docs]


@router.post("/documents", response_model=UserDocumentOut, status_code=status.HTTP_201_CREATED)
def create_document(
    payload: UserDocumentIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    validated = _validate_doc_payload(payload.model_dump())
    # scan_path игнорируем — он управляется только через scan endpoint
    validated.pop("scan_path", None)

    non_sensitive = {k: v for k, v in validated.items() if k not in _SENSITIVE_DOC_FIELDS}
    doc = UserDocument(user_id=user.id, **non_sensitive)
    _apply_doc_payload(doc, {k: validated[k] for k in _SENSITIVE_DOC_FIELDS if k in validated})
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return _doc_to_out(doc)


@router.put("/documents/{doc_id}", response_model=UserDocumentOut)
def update_document(
    doc_id: int,
    payload: UserDocumentUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = _owned_document(db, user, doc_id)
    validated = _validate_doc_payload(payload.model_dump(exclude_none=True))
    validated.pop("scan_path", None)
    _apply_doc_payload(doc, validated)
    db.commit()
    db.refresh(doc)
    return _doc_to_out(doc)


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


def _validate_addresses_payload(addresses: list) -> list[dict]:
    """v1.1 (P4): нормализовать список адресов пользователя (до 5 шт.).

    Каждый адрес — dict с полями id, label, region, district, city, street,
    isPrimary. Невалидные элементы тихо отбрасываются; в БД уходит
    только один primary (если заявлено несколько — последний).
    """
    if not isinstance(addresses, list):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="addresses должен быть массивом.",
        )
    if len(addresses) > 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Можно сохранить не больше 5 адресов.",
        )
    normalized: list[dict] = []
    seen_ids: set[str] = set()
    primary_seen = False
    for item in addresses:
        if not isinstance(item, dict):
            continue
        entry = {
            "id": str(item.get("id", "")).strip()[:64],
            "label": str(item.get("label", "")).strip()[:80],
            "region": str(item.get("region", "")).strip()[:120],
            "district": str(item.get("district", "")).strip()[:120],
            "city": str(item.get("city", "")).strip()[:120],
            "street": str(item.get("street", "")).strip()[:255],
            "isPrimary": bool(item.get("isPrimary", False)),
        }
        # Пустые/повторные id убираем — фронт генерирует uid-ы через свою логику.
        if not entry["id"] or entry["id"] in seen_ids:
            continue
        # Пропускаем совсем пустые записи (без label и без street).
        if not entry["label"] and not entry["street"] and not entry["city"]:
            continue
        seen_ids.add(entry["id"])
        # Гарантируем, что primary только один.
        if entry["isPrimary"] and primary_seen:
            entry["isPrimary"] = False
        elif entry["isPrimary"]:
            primary_seen = True
        normalized.append(entry)
    # Если ни один не помечен primary — делаем первый.
    if normalized and not primary_seen:
        normalized[0]["isPrimary"] = True
    return normalized


def _wipe_scan_files(doc: UserDocument) -> None:
    """Удалить связанные с документом файлы скана (encrypted + legacy plain)."""
    candidates: list[Path] = []
    if doc.scan_encrypted_path:
        candidates.append(Path(doc.scan_encrypted_path))
    if doc.scan_path:
        candidates.append(Path(doc.scan_path))
    for p in candidates:
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass
        try:
            p.parent.rmdir()
        except OSError:
            pass


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = _owned_document(db, user, doc_id)
    _wipe_scan_files(doc)
    db.delete(doc)
    db.commit()


# ---------------------------------------------------------------------------
# Промпт 1 — Загрузка/выгрузка скана с шифрованием at-rest
# ---------------------------------------------------------------------------

@router.post("/documents/{doc_id}/scan")
async def upload_document_scan(
    doc_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Загрузить PDF/JPG/PNG/WEBP скан. Шифруется Fernet перед записью на диск.
    Файл хранится ВНЕ публичного /uploads. Скачивание — через защищённый
    `GET /api/user/documents/{id}/scan` (требует JWT + owner-check).
    """
    doc = db.scalars(
        select(UserDocument).where(
            UserDocument.id == doc_id,
            UserDocument.user_id == user.id,
        )
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден.")

    body = await file.read()
    if not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Файл пустой.")
    if len(body) > DOCUMENT_SCAN_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл больше {DOCUMENT_SCAN_MAX_BYTES // (1024*1024)} МБ.",
        )

    # Magic-bytes — основной канал проверки. content-type может врать.
    detected_mime = _detect_scan_mime(body)
    if detected_mime is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Поддерживаются PDF, JPG, PNG, WEBP.",
        )

    # Шифрование и запись. Файл лежит в data/secure/documents/{user}/{doc}/.
    try:
        encrypted_blob = encrypt_file(body)
    except DocumentCryptoError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Шифрование документов не настроено на сервере.",
        ) from exc

    user_dir = DOCUMENT_SCAN_DIR / str(user.id) / str(doc_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(16)
    target = user_dir / f"{token}.enc"
    target.write_bytes(encrypted_blob)

    # Чистим предыдущий файл (encrypted или legacy plain).
    old_paths = [doc.scan_encrypted_path, doc.scan_path]
    for old in old_paths:
        if not old:
            continue
        p = Path(old)
        if p.exists() and p != target:
            try:
                p.unlink()
            except OSError:
                pass

    safe_original = _SAFE_FILENAME.sub("_", (file.filename or "").strip())[:200] or "document"
    doc.scan_encrypted_path = str(target)
    doc.scan_original_filename = safe_original
    doc.scan_mime_type = detected_mime
    doc.scan_size = len(body)
    doc.scan_uploaded_at = datetime.utcnow()
    # legacy plain — обнуляем
    doc.scan_path = ""
    db.commit()
    db.refresh(doc)

    return {
        "doc_id": doc.id,
        "scan": {
            "has_scan": True,
            "mime_type": detected_mime,
            "size": len(body),
            "original_filename": safe_original,
            "uploaded_at": doc.scan_uploaded_at.isoformat() if doc.scan_uploaded_at else "",
            "download_url": f"/api/user/documents/{doc.id}/scan",
        },
    }


@router.delete("/documents/{doc_id}/scan", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_scan(
    doc_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.scalars(
        select(UserDocument).where(
            UserDocument.id == doc_id,
            UserDocument.user_id == user.id,
        )
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден.")
    _wipe_scan_files(doc)
    doc.scan_encrypted_path = ""
    doc.scan_original_filename = ""
    doc.scan_mime_type = ""
    doc.scan_size = 0
    doc.scan_uploaded_at = None
    doc.scan_path = ""
    db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Защищённый download — расшифровка в памяти, выдача StreamingResponse.
# Статический mount /uploads/documents больше НЕ подключен (см. app.py).
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/documents/{doc_id}/scan")
def download_document_scan(
    doc_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    import io  # локальный импорт — используется только здесь

    doc = _owned_document(db, user, doc_id)
    # Новый путь — encrypted blob.
    if doc.scan_encrypted_path:
        path = Path(doc.scan_encrypted_path)
        if not path.exists() or not path.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл скана не найден.")
        try:
            plaintext = decrypt_file(path.read_bytes())
        except DocumentCryptoError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось расшифровать скан.",
            ) from exc
        mime = doc.scan_mime_type or "application/octet-stream"
        ext = {
            "application/pdf": "pdf",
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
        }.get(mime, "bin")
        return StreamingResponse(
            io.BytesIO(plaintext),
            media_type=mime,
            headers={
                "Content-Disposition": f'inline; filename="document-{doc_id}.{ext}"',
                "Cache-Control": "private, no-store",
            },
        )

    # Legacy: plain PDF (для документов, созданных до миграции 0021).
    if doc.scan_path:
        full = Path(doc.scan_path)
        if not full.exists() or not full.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл скана не найден.")
        return FileResponse(
            path=str(full),
            media_type="application/pdf",
            filename=f"document-{doc_id}.pdf",
            headers={"Cache-Control": "private, no-store"},
        )

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Скан не загружен.")


# ---------------------------------------------------------------------------
# v1.1 (P4) — Пользовательские заметки (CRUD, владелец-only)
# ---------------------------------------------------------------------------

def _owned_note(db: Session, user: User, note_id: int) -> UserNote:
    note = db.scalars(
        select(UserNote).where(UserNote.id == note_id, UserNote.user_id == user.id)
    ).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заметка не найдена.")
    return note


def _validate_note_payload(payload: dict) -> dict:
    """Нормализовать входные поля заметки.

    - text: обрезаем до 1000 символов, не пустой.
    - category: если передана — должна быть в USER_NOTE_CATEGORIES;
      иначе тихо подменяется на «Общее».
    - reminder_at: либо пустая строка, либо валидный ISO yyyy-mm-dd.
    """
    text = str(payload.get("text", "")).strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Текст заметки не может быть пустым.",
        )
    payload["text"] = text[:1000]

    category = str(payload.get("category", "")).strip()
    if not category or category not in USER_NOTE_CATEGORIES:
        category = "Общее"
    payload["category"] = category

    reminder = str(payload.get("reminder_at", "")).strip()
    if reminder:
        try:
            # Принимаем yyyy-mm-dd и полный ISO.
            datetime.fromisoformat(reminder.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="reminder_at должен быть ISO датой (yyyy-mm-dd).",
            )
    payload["reminder_at"] = reminder[:40]

    return payload


@router.get("/notes", response_model=list[UserNoteOut])
def list_notes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Список заметок пользователя (новые сверху)."""
    notes = db.scalars(
        select(UserNote)
        .where(UserNote.user_id == user.id)
        .order_by(UserNote.created_at.desc())
    ).all()
    return [UserNoteOut.model_validate(n) for n in notes]


@router.post("/notes", response_model=UserNoteOut, status_code=status.HTTP_201_CREATED)
def create_note(
    payload: UserNoteCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Создать заметку. Валидация категории и reminder_at."""
    validated = _validate_note_payload(payload.model_dump())
    note = UserNote(user_id=user.id, **validated)
    db.add(note)
    db.commit()
    db.refresh(note)
    return UserNoteOut.model_validate(note)


@router.put("/notes/{note_id}", response_model=UserNoteOut)
def update_note(
    note_id: int,
    payload: UserNoteUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Обновить заметку (текст / категория / срок / флаг done)."""
    note = _owned_note(db, user, note_id)
    data = _validate_note_payload(payload.model_dump(exclude_none=True))
    for field, value in data.items():
        setattr(note, field, value)
    db.commit()
    db.refresh(note)
    return UserNoteOut.model_validate(note)


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Удалить заметку."""
    note = _owned_note(db, user, note_id)
    db.delete(note)
    db.commit()
