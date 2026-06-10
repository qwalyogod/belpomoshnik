from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from backend import schemas
from backend.database import SessionLocal
from backend.models import ExtremistEntry

router = APIRouter(prefix="/api/extremist-entries", tags=["extremist"])


def _json_list(raw: str) -> list[str]:
    try:
        value = json.loads(raw or "[]")
        return [str(x) for x in value] if isinstance(value, list) else []
    except (TypeError, ValueError):
        return []


def _to_out(item: ExtremistEntry) -> schemas.ExtremistEntryOut:
    return schemas.ExtremistEntryOut(
        id=item.id,
        title=item.title,
        category=item.category,
        source_url=item.source_url,
        source_name=item.source_name,
        included_at=item.included_at,
        last_checked_at=item.last_checked_at,
        short_description=item.short_description,
        cover_url=item.cover_url,
        media_urls=_json_list(item.media_urls),
        attachment_urls=_json_list(item.attachment_urls),
        filters_json=item.filters_json,
        status=item.status,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get("", response_model=list[schemas.ExtremistEntryOut])
def list_extremist_entries(
    category: str | None = Query(default=None),
):
    """Публичное read-only чтение опубликованных записей раздела."""
    with SessionLocal() as db:
        stmt = (
            select(ExtremistEntry)
            .where(ExtremistEntry.status == "published")
            .order_by(ExtremistEntry.updated_at.desc())
        )
        if category:
            stmt = stmt.where(ExtremistEntry.category == category)
        return [_to_out(item) for item in db.scalars(stmt).all()]


@router.get("/{entry_id}", response_model=schemas.ExtremistEntryOut)
def get_extremist_entry(entry_id: int):
    """Публичная детальная карточка опубликованной записи."""
    with SessionLocal() as db:
        entry = db.scalar(
            select(ExtremistEntry).where(
                ExtremistEntry.id == entry_id,
                ExtremistEntry.status == "published",
            )
        )
        if entry is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Запись не найдена или ещё не опубликована.",
            )
        return _to_out(entry)
