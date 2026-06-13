#!/usr/bin/env python3
"""Import Belarus institution JSON batches into backend authorities.

The script accepts the normalized contract produced for Belpomoshnik:

    {
      "institutions": [...],
      "rejected_items": [...]
    }

It also supports the older local shape:

    {
      "items": [...]
    }

Only confirmed `institutions/items` are imported. `rejected_items` stay in the
source files for editorial review and never enter the product database.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from backend.database import SessionLocal  # noqa: E402
from backend.models import Authority  # noqa: E402


IMPORT_DIR = PROJECT_ROOT / "data" / "import"
DEFAULT_GLOBS = (
    IMPORT_DIR / "*institutions*.json",
    IMPORT_DIR / "institutions" / "*.json",
)

MARKDOWN_LINK_RE = re.compile(r"^\s*\[([^\]]+)\]\((https?://[^)]+)\)\s*$", re.IGNORECASE)
SPACES_RE = re.compile(r"\s+")


def clean_text(value: Any, *, limit: int | None = None) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        value = json.dumps(value, ensure_ascii=False)
    text = str(value).strip()
    match = MARKDOWN_LINK_RE.match(text)
    if match:
        text = match.group(2).strip()
    text = SPACES_RE.sub(" ", text)
    if limit is not None:
        return text[:limit]
    return text


def clean_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    result: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = clean_text(item)
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def dumps_list(value: Any) -> str:
    return json.dumps(clean_list(value), ensure_ascii=False)


def read_items(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        items = raw.get("institutions")
        if not isinstance(items, list):
            items = raw.get("items")
    else:
        items = []
    return [item for item in (items or []) if isinstance(item, dict)]


def file_paths(args: argparse.Namespace) -> list[Path]:
    if args.files:
        paths = [Path(p).resolve() for p in args.files]
    else:
        found: set[Path] = set()
        for pattern in DEFAULT_GLOBS:
            found.update(pattern.parent.glob(pattern.name))
        paths = sorted(found)
    return [p for p in paths if p.exists() and p.is_file()]


def normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    source_urls = clean_list(item.get("source_urls"))
    website = clean_text(item.get("website") or item.get("website_url"), limit=500)
    if not website and source_urls:
        website = source_urls[0][:500]
    full_name = clean_text(item.get("full_name") or item.get("description"), limit=500)
    short_name = clean_text(item.get("short_name") or item.get("title") or item.get("name"), limit=255)
    title = short_name or full_name[:255] or "Учреждение"

    return {
        "external_id": clean_text(item.get("external_id") or item.get("id"), limit=255),
        "title": title,
        "description": full_name,
        "website_url": website,
        "phone": clean_text(item.get("phone"), limit=120),
        "email": clean_text(item.get("email"), limit=255),
        "address": clean_text(item.get("address"), limit=500),
        "working_hours": clean_text(item.get("working_hours") or item.get("hours"), limit=255),
        "type": clean_text(item.get("institution_type") or item.get("type"), limit=120),
        "region": clean_text(item.get("region"), limit=120),
        "district": clean_text(item.get("district"), limit=120),
        "city": clean_text(item.get("city"), limit=120),
        "settlement": clean_text(item.get("settlement"), limit=120),
        "services_json": dumps_list(item.get("services")),
        "tags_json": dumps_list(item.get("tags")),
        "related_scenario_categories_json": dumps_list(item.get("related_scenario_categories")),
        "related_scenarios_json": dumps_list(item.get("related_scenarios")),
        "source_ids_json": dumps_list(item.get("source_ids")),
        "source_urls_json": json.dumps(source_urls, ensure_ascii=False),
        "last_checked_at": clean_text(item.get("last_checked_at"), limit=40),
        "confidence": clean_text(item.get("confidence"), limit=40),
        "notes": clean_text(item.get("notes")),
        "is_active": bool(item.get("is_active", True)),
    }


def find_existing(db: Session, payload: dict[str, Any]) -> Authority | None:
    external_id = payload["external_id"]
    if external_id:
        found = db.scalar(select(Authority).where(Authority.external_id == external_id).limit(1))
        if found:
            return found

    title = payload["title"]
    city = payload["city"]
    address = payload["address"]
    if title and (city or address):
        return db.scalar(
            select(Authority)
            .where(
                Authority.title == title,
                Authority.city == city,
                Authority.address == address,
            )
            .limit(1)
        )
    return None


def import_payload(db: Session, payloads: Iterable[dict[str, Any]], *, dry_run: bool) -> Counter:
    counts: Counter = Counter()
    for raw_item in payloads:
        payload = normalize_item(raw_item)
        if not payload["title"]:
            counts["skipped"] += 1
            continue
        existing = find_existing(db, payload)
        if existing:
            counts["updated"] += 1
            if not dry_run:
                for key, value in payload.items():
                    setattr(existing, key, value)
        else:
            counts["created"] += 1
            if not dry_run:
                db.add(Authority(**payload))
    if not dry_run:
        db.commit()
    return counts


def run(args: argparse.Namespace) -> int:
    paths = file_paths(args)
    if not paths:
        print("[institutions] JSON-файлы не найдены.")
        return 1

    all_items: list[dict[str, Any]] = []
    print("[institutions] файлы:")
    for path in paths:
        items = read_items(path)
        all_items.extend(items)
        print(f"  - {path.relative_to(PROJECT_ROOT)}: {len(items)}")

    db = SessionLocal()
    try:
        counts = import_payload(db, all_items, dry_run=args.dry_run)
    finally:
        db.close()

    mode = "dry-run" if args.dry_run else "import"
    print(
        f"[institutions] {mode}: создано {counts['created']}, "
        f"обновлено {counts['updated']}, пропущено {counts['skipped']}"
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Импорт учреждений Беларуси в authorities.")
    parser.add_argument("files", nargs="*", help="Конкретные JSON-файлы. Если не указаны, берутся data/import/*institutions*.json.")
    parser.add_argument("--dry-run", action="store_true", help="Проверить файлы без записи в БД.")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
