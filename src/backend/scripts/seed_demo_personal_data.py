"""
Промпт 1 — Идемпотентный seed демонстрационных «Моих документов» для всех пользователей.

Запуск:
    PYTHONPATH=src .venv/bin/python -m backend.scripts.seed_demo_personal_data

Скрипт:
- идёт по всем активным пользователям (кроме guest@*);
- для каждого создаёт набор демо-документов, если ещё нет (по `doc_type+title`);
- значения детерминированы от `user.id` (повторный запуск не плодит хаос);
- чувствительные поля шифруются через `backend.security.document_crypto`;
- для части документов генерируется минимальный PDF-скан с пометкой
  «DEMO SCAN — NOT A REAL DOCUMENT», шифруется и сохраняется в DOCUMENT_SCAN_DIR.

Перед запуском должна быть установлена `BELPOMOSHNIK_DOCUMENT_MASTER_KEY`
(см. .env.example).
"""
from __future__ import annotations

import json
import random
import secrets
import sys
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import select

# Загружаем .env как в обычном запуске backend.
from dotenv import load_dotenv

load_dotenv()

from backend.database import SessionLocal
from backend.models import User, UserDocument
from backend.security import (
    DocumentCryptoError,
    encrypt_field,
    encrypt_file,
    is_crypto_configured,
)
from backend.api.user import DOCUMENT_SCAN_DIR


# Карта документов: ключ — (doc_type, title). Каждое значение — функция,
# которая по rng генерирует поля и решает, нужен ли скан.
def _today() -> datetime:
    return datetime.utcnow()


def _make_pdf_blob(label: str) -> bytes:
    """Простейший валидный 1-страничный PDF с надписью.
    Достаточно для UI-предпросмотра (PDF viewer / iframe)."""
    text = label.replace("(", "[").replace(")", "]")
    body = (
        f"BT /F1 18 Tf 60 750 Td (DEMO SCAN — NOT A REAL DOCUMENT) Tj "
        f"0 -40 Td /F1 12 Tf ({text}) Tj ET"
    ).encode("latin-1", errors="replace")
    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
    )
    stream = b"<< /Length " + str(len(body)).encode() + b" >>\nstream\n" + body + b"\nendstream"
    objects.append(stream)
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref_offset = len(pdf)
    pdf += b"xref\n0 " + str(len(objects) + 1).encode() + b"\n"
    pdf += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        pdf += f"{off:010d} 00000 n \n".encode()
    pdf += b"trailer\n<< /Size " + str(len(objects) + 1).encode() + b" /Root 1 0 R >>\n"
    pdf += b"startxref\n" + str(xref_offset).encode() + b"\n%%EOF\n"
    return bytes(pdf)


def _det_rng(seed_key: str) -> random.Random:
    """Детерминированный rng от user.id+email — повторный запуск даёт те же значения."""
    return random.Random(seed_key)


def _doc_set_for_user(user: User) -> list[dict]:
    """Список документов, который должен быть у конкретного пользователя."""
    rng = _det_rng(f"{user.id}:{user.email}")
    today = _today()
    docs: list[dict] = []

    # Паспорт — у всех.
    issued_year = today.year - rng.randint(2, 15)
    docs.append({
        "doc_type": "passport",
        "title": "Паспорт гражданина Республики Беларусь",
        "number": f"MP{rng.randint(1000000, 9999999)}",
        "issued_by": f"Отдел по гражданству и миграции (г. {user.city or 'Минск'})",
        "issued_date": f"{issued_year}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
        "expiry_date": f"{issued_year + 10}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
        "is_sensitive": True,
        "comment": "Демонстрационная запись",
        "make_scan": True,
    })

    # ID-карта.
    docs.append({
        "doc_type": "other",
        "title": "ID-карта (биометрический документ)",
        "number": f"ID{rng.randint(100000, 999999)}{chr(65 + rng.randint(0, 25))}",
        "issued_by": "МВД Республики Беларусь",
        "issued_date": f"{issued_year}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
        "expiry_date": f"{issued_year + 10}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
        "is_sensitive": True,
        "make_scan": False,
        "custom_fields": [
            {"name": "Чип NFC", "value": "включён"},
            {"name": "Электронная подпись", "value": "не оформлена"},
        ],
    })

    if user.has_car:
        docs.append({
            "doc_type": "driver",
            "title": "Водительское удостоверение",
            "number": f"AB{rng.randint(100000, 999999)}",
            "issued_by": "ГАИ МВД (демо)",
            "issued_date": f"{today.year - rng.randint(1, 9)}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
            "expiry_date": f"{today.year + rng.randint(2, 9)}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
            "is_sensitive": True,
            "make_scan": True,
        })

    if user.has_children:
        docs.append({
            "doc_type": "birth",
            "title": "Свидетельство о рождении ребёнка",
            "number": f"I-БМ {rng.randint(100000, 999999)}",
            "issued_by": "ЗАГС (демо)",
            "issued_date": f"{today.year - rng.randint(1, 12)}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
            "expiry_date": "",
            "is_sensitive": True,
            "make_scan": False,
        })

    if user.owns_property or user.is_renter:
        docs.append({
            "doc_type": "housing",
            "title": "Договор найма / документ на жильё",
            "number": f"ДЖ-{rng.randint(10000, 99999)}",
            "issued_by": "ЖЭУ / БТИ (демо)",
            "issued_date": f"{today.year - rng.randint(0, 6)}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
            "expiry_date": "",
            "is_sensitive": False,
            "comment": "Демо-данные, не реальный договор",
            "make_scan": True,
        })

    docs.append({
        "doc_type": "medical",
        "title": "Медицинская справка (форма 1)",
        "number": f"МС-{rng.randint(100000, 999999)}",
        "issued_by": "Поликлиника №3 (демо)",
        "issued_date": (today - timedelta(days=rng.randint(30, 300))).strftime("%Y-%m-%d"),
        "expiry_date": (today + timedelta(days=rng.randint(20, 60))).strftime("%Y-%m-%d"),
        "is_sensitive": False,
        "make_scan": False,
    })

    # Один документ «скоро истекает» — ярко в UI.
    docs.append({
        "doc_type": "other",
        "title": "УНП физического лица (демо)",
        "number": f"{rng.randint(100000000, 999999999)}",
        "issued_by": "МНС",
        "issued_date": f"{today.year - rng.randint(3, 10)}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
        "expiry_date": (today + timedelta(days=rng.randint(7, 20))).strftime("%Y-%m-%d"),
        "is_sensitive": True,
        "comment": "Срок действия истекает в течение месяца",
        "make_scan": False,
    })

    docs.append({
        "doc_type": "receipt",
        "title": "Страховой полис (бессрочный, демо)",
        "number": f"ПС-{rng.randint(100000, 999999)}",
        "issued_by": "Белгосстрах (демо)",
        "issued_date": (today - timedelta(days=rng.randint(60, 800))).strftime("%Y-%m-%d"),
        "expiry_date": "",
        "is_sensitive": False,
        "make_scan": False,
    })

    return docs


def _existing_doc_keys(db, user: User) -> set[tuple[str, str]]:
    rows = db.scalars(
        select(UserDocument).where(UserDocument.user_id == user.id)
    ).all()
    return {(r.doc_type or "", r.title or "") for r in rows}


def _save_scan_for_doc(doc: UserDocument, user: User) -> int | None:
    """Сгенерировать demo PDF, зашифровать, сохранить, обновить metadata. Возвращает размер."""
    pdf_bytes = _make_pdf_blob(f"{doc.title} | user {user.id}")
    try:
        encrypted_blob = encrypt_file(pdf_bytes)
    except DocumentCryptoError as exc:
        print(f"[!] Не могу зашифровать скан: {exc}")
        return None
    user_dir = DOCUMENT_SCAN_DIR / str(user.id) / str(doc.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(16)
    target = user_dir / f"{token}.enc"
    target.write_bytes(encrypted_blob)

    doc.scan_encrypted_path = str(target)
    doc.scan_original_filename = f"demo-{doc.doc_type or 'document'}.pdf"
    doc.scan_mime_type = "application/pdf"
    doc.scan_size = len(pdf_bytes)
    doc.scan_uploaded_at = datetime.utcnow()
    return len(pdf_bytes)


def main() -> int:
    if not is_crypto_configured():
        print(
            "[!] BELPOMOSHNIK_DOCUMENT_MASTER_KEY не задан. Сгенерируй ключ:\n"
            '    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"\n'
            "и положи в .env, затем повтори запуск."
        )
        return 1

    with SessionLocal() as db:
        users = db.scalars(
            select(User).where(User.is_active == True)  # noqa: E712
        ).all()
        users = [u for u in users if not u.email.startswith("guest@")]

        total_users = 0
        total_docs = 0
        total_scans = 0
        for user in users:
            existing = _existing_doc_keys(db, user)
            wanted = _doc_set_for_user(user)
            created_for_user = 0

            for spec in wanted:
                key = (spec["doc_type"], spec["title"])
                if key in existing:
                    continue
                doc = UserDocument(
                    user_id=user.id,
                    title=spec["title"],
                    doc_type=spec["doc_type"],
                    issued_date=spec["issued_date"],
                    expiry_date=spec.get("expiry_date") or "",
                    is_sensitive=bool(spec.get("is_sensitive", False)),
                    # legacy plain — пусто
                    number="",
                    issued_by="",
                    comment="",
                    custom_fields_json="",
                    scan_path="",
                )
                # Шифрованные поля
                doc.number_encrypted = encrypt_field(spec.get("number", ""))
                doc.issued_by_encrypted = encrypt_field(spec.get("issued_by", ""))
                doc.comment_encrypted = encrypt_field(spec.get("comment", ""))
                custom = spec.get("custom_fields")
                if custom:
                    doc.custom_fields_encrypted = encrypt_field(
                        json.dumps(custom, ensure_ascii=False)
                    )
                db.add(doc)
                db.flush()  # нужен id для пути скана

                if spec.get("make_scan"):
                    size = _save_scan_for_doc(doc, user)
                    if size is not None:
                        total_scans += 1

                created_for_user += 1

            if created_for_user:
                db.commit()
                total_docs += created_for_user
                total_users += 1
                print(f"  + user #{user.id} ({user.email}): {created_for_user} docs")
            else:
                print(f"  · user #{user.id} ({user.email}): already seeded")

        print(
            f"\nDone. Users touched: {total_users}, docs created: {total_docs}, scans created: {total_scans}."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
