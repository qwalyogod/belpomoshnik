#!/usr/bin/env python3
"""Normalize generated Belpomoshnik content batches before validation.

The script fixes common LLM formatting mistakes without changing editorial
meaning: source strings become source objects, missing sourceIds are inferred
from official URLs, and one known malformed auto batch pattern is repaired.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IMPORT_DIR = PROJECT_ROOT / "data" / "import"

SOURCE_INFO: dict[str, dict[str, str]] = {
    "source-pravo": {
        "title": "Национальный правовой Интернет-портал",
        "url": "https://pravo.by/",
    },
    "source-portal-gov": {
        "title": "Единый портал электронных услуг",
        "url": "https://portal.gov.by/",
    },
    "source-mintrud": {
        "title": "Министерство труда и социальной защиты",
        "url": "https://mintrud.gov.by/",
    },
    "source-nalog": {
        "title": "Министерство по налогам и сборам",
        "url": "https://nalog.gov.by/",
    },
    "source-minjust": {
        "title": "Министерство юстиции",
        "url": "https://minjust.gov.by/",
    },
    "source-mvd": {
        "title": "МВД, Департамент по гражданству и миграции",
        "url": "https://mvd.gov.by/ru/structure/departament/departament-grazhdanstva-i-migratsii",
    },
    "source-gibdd": {
        "title": "ГАИ МВД",
        "url": "https://mvd.gov.by/ru/structure/gai",
    },
    "source-court": {
        "title": "Верховный Суд Республики Беларусь",
        "url": "https://court.gov.by/",
    },
    "source-nbki": {
        "title": "Реестровые сведения по недвижимости через госпортал",
        "url": "https://portal.gov.by/",
    },
    "source-minzdrav": {
        "title": "Министерство здравоохранения Республики Беларусь",
        "url": "https://minzdrav.gov.by/",
    },
    "source-raschet-erip": {
        "title": "ЕРИП",
        "url": "https://raschet.by/",
    },
    "source-egr": {
        "title": "Единый государственный регистр юридических лиц и индивидуальных предпринимателей",
        "url": "https://egr.gov.by/",
    },
    "source-nces": {
        "title": "Национальный центр электронных услуг",
        "url": "https://nces.by/",
    },
    "source-115": {
        "title": "Портал 115.бел",
        "url": "https://115.xn--90ais/",
    },
    "source-beltechosmotr": {
        "title": "РУП «Белтехосмотр»",
        "url": "https://gto.by/",
    },
    "source-president": {
        "title": "Официальный интернет-портал Президента Республики Беларусь",
        "url": "https://president.gov.by/",
    },
    "source-government": {
        "title": "Совет Министров Республики Беларусь",
        "url": "https://www.government.by/",
    },
}


def source_object(source_id: str, checked_at: str, override: dict[str, Any] | None = None) -> dict[str, str]:
    info = dict(SOURCE_INFO.get(source_id, {}))
    if override:
        info.update({k: v for k, v in override.items() if k in {"title", "url"} and isinstance(v, str) and v})
    return {
        "source_id": source_id,
        "title": info.get("title", source_id),
        "url": info.get("url", ""),
        "checked_at": checked_at,
    }


def load_json_with_repairs(path: Path) -> tuple[dict[str, Any], bool]:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text), False
    except json.JSONDecodeError:
        if path.name != "content_auto_2022_2026.json":
            raise
    repaired = text.replace('}]}},{"id"', '}]},{"id"')
    return json.loads(repaired), repaired != text


def infer_source_id_from_url(url: Any) -> str | None:
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        return None
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    if "pravo.by" in host:
        return "source-pravo"
    if "portal.gov.by" in host:
        return "source-portal-gov"
    if "mintrud.gov.by" in host:
        return "source-mintrud"
    if "nalog.gov.by" in host:
        return "source-nalog"
    if "minjust.gov.by" in host:
        return "source-minjust"
    if "court.gov.by" in host:
        return "source-court"
    if "minzdrav.gov.by" in host:
        return "source-minzdrav"
    if "raschet.by" in host:
        return "source-raschet-erip"
    if "egr.gov.by" in host:
        return "source-egr"
    if "nces.by" in host:
        return "source-nces"
    if "115." in host or "xn--90ais" in host:
        return "source-115"
    if "gto.by" in host:
        return "source-beltechosmotr"
    if "president.gov.by" in host:
        return "source-president"
    if "government.by" in host:
        return "source-government"
    if "mvd.gov.by" in host and "gai" in path:
        return "source-gibdd"
    if "mvd.gov.by" in host:
        return "source-mvd"
    return None


def iter_item_source_urls(item: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    for source in item.get("sources") or []:
        if isinstance(source, dict) and isinstance(source.get("url"), str):
            urls.append(source["url"])
    if isinstance(item.get("sourceUrl"), str):
        urls.append(item["sourceUrl"])
    source = item.get("source")
    if isinstance(source, dict) and isinstance(source.get("url"), str):
        urls.append(source["url"])
    return urls


def normalize_official_sources(data: dict[str, Any], checked_at: str) -> dict[str, dict[str, str]]:
    normalized: dict[str, dict[str, str]] = {}
    for item in data.get("official_sources_used") or []:
        if isinstance(item, str):
            normalized[item] = source_object(item, checked_at)
            continue
        if not isinstance(item, dict):
            continue
        source_id = item.get("source_id") or item.get("id")
        if not isinstance(source_id, str) or not source_id:
            continue
        normalized[source_id] = source_object(source_id, item.get("checked_at") or checked_at, item)

    for candidate in data.get("source_candidates") or []:
        if not isinstance(candidate, dict):
            continue
        source_id = infer_source_id_from_url(candidate.get("url"))
        if source_id and source_id in SOURCE_INFO:
            normalized.setdefault(source_id, source_object(source_id, candidate.get("last_checked") or checked_at, candidate))
    return normalized


def normalize_item_source_ids(item: dict[str, Any], official_sources: dict[str, dict[str, str]], checked_at: str) -> bool:
    changed = False
    ids = item.get("sourceIds")
    if not isinstance(ids, list):
        return changed
    if not ids:
        inferred: list[str] = []
        for url in iter_item_source_urls(item):
            source_id = infer_source_id_from_url(url)
            if source_id and source_id not in inferred:
                inferred.append(source_id)
        if inferred:
            item["sourceIds"] = inferred
            ids = inferred
            changed = True
    for source_id in ids:
        if isinstance(source_id, str) and source_id in SOURCE_INFO:
            official_sources.setdefault(source_id, source_object(source_id, checked_at))
    return changed


def normalize_news_media_notes(data: dict[str, Any]) -> bool:
    changed = False
    default_note = "Медиа взяты только из официальных источников или оставлены пустыми."
    for item in data.get("news_articles") or []:
        if isinstance(item, dict) and not str(item.get("media_notes") or "").strip():
            item["media_notes"] = default_note
            changed = True
    return changed


def normalize_batch_meta_category(path: Path, data: dict[str, Any]) -> bool:
    batch_meta = data.setdefault("batch_meta", {})
    if not isinstance(batch_meta, dict):
        data["batch_meta"] = batch_meta = {}
    expected_by_file = {
        "content_news_calendar_2022_2026.json": "news_calendar",
        "content_law_updates_2022_2026.json": "law_updates",
        "content_extremist_materials_2022_2026.json": "extremist_materials",
    }
    expected = expected_by_file.get(path.name)
    if expected and batch_meta.get("category_id") != expected:
        batch_meta["category_id"] = expected
        return True
    return False


def dedupe_string_list(values: Any) -> tuple[list[str], bool]:
    if not isinstance(values, list):
        return [], False
    seen: set[str] = set()
    result: list[str] = []
    changed = False
    for value in values:
        if not isinstance(value, str):
            changed = True
            continue
        key = value.strip().casefold()
        if not key:
            changed = True
            continue
        if key in seen:
            changed = True
            continue
        seen.add(key)
        result.append(value.strip())
    return result, changed


def normalize_news_tags(data: dict[str, Any]) -> bool:
    changed = False
    for item in data.get("news_articles") or []:
        if not isinstance(item, dict):
            continue
        tags, fixed = dedupe_string_list(item.get("tags"))
        if fixed:
            item["tags"] = tags
            changed = True
    return changed


def slugify(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return text or "source"


def normalize_law_source_ids(data: dict[str, Any]) -> bool:
    changed = False
    for item in data.get("law_updates") or []:
        if not isinstance(item, dict):
            continue
        source = item.get("source")
        if not isinstance(source, dict):
            continue
        current = source.get("id")
        if isinstance(current, str) and current.startswith("src-"):
            continue
        source_ids = item.get("sourceIds")
        base = ""
        if isinstance(source_ids, list) and source_ids and isinstance(source_ids[0], str):
            base = source_ids[0].replace("source-", "")
        elif isinstance(current, str) and current:
            base = current.replace("source-", "")
        elif isinstance(source.get("title"), str):
            base = source["title"]
        source["id"] = f"src-{slugify(base)}"
        changed = True
    return changed


def reject_unresolved_news(data: dict[str, Any]) -> bool:
    changed = False
    kept: list[dict[str, Any]] = []
    rejected = data.setdefault("rejected_items", [])
    for item in data.get("news_articles") or []:
        if not isinstance(item, dict):
            kept.append(item)
            continue
        if item.get("sourceIds") != []:
            kept.append(item)
            continue
        rejected.append(
            {
                "type": "news_article",
                "title": item.get("title") or "Новость без названия",
                "reason": "Новость не имеет подтвержденного официального source_id после автоматической нормализации.",
                "searched_sources": [url for url in [item.get("sourceUrl")] if isinstance(url, str) and url],
                "notes": "Проверить официальный первоисточник вручную или не импортировать материал.",
            }
        )
        changed = True
    if changed:
        data["news_articles"] = kept
    return changed


def normalize_batch(path: Path, dry_run: bool = False) -> tuple[bool, list[str]]:
    notes: list[str] = []
    data, repaired = load_json_with_repairs(path)
    changed = repaired
    if repaired:
        notes.append("repaired malformed stages JSON")

    checked_at = str((data.get("batch_meta") or {}).get("checked_at") or "2026-06-08")
    if normalize_batch_meta_category(path, data):
        changed = True
        notes.append("normalized batch_meta.category_id")
    official_sources = normalize_official_sources(data, checked_at)

    old_sources = data.get("official_sources_used")
    data["official_sources_used"] = list(official_sources.values())
    if data["official_sources_used"] != old_sources:
        changed = True
        notes.append("normalized official_sources_used")

    for group in ("problems", "news_articles", "law_updates"):
        for item in data.get(group) or []:
            if isinstance(item, dict) and normalize_item_source_ids(item, official_sources, checked_at):
                changed = True
                notes.append(f"inferred sourceIds in {group}")
    if normalize_news_media_notes(data):
        changed = True
        notes.append("filled empty news media_notes")
    if normalize_news_tags(data):
        changed = True
        notes.append("deduplicated news tags")
    if normalize_law_source_ids(data):
        changed = True
        notes.append("normalized law source ids")
    if reject_unresolved_news(data):
        changed = True
        notes.append("moved unresolved non-official news to rejected_items")

    new_sources = list(official_sources.values())
    if data.get("official_sources_used") != new_sources:
        data["official_sources_used"] = new_sources
        changed = True
        notes.append("added referenced official sources")

    if changed and not dry_run:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed, notes


def normalize_extremist_filename(dry_run: bool = False) -> list[str]:
    notes: list[str] = []
    bad = IMPORT_DIR / "content_extremist_materials_2022_2026..json"
    good = IMPORT_DIR / "content_extremist_materials_2022_2026.json"
    if bad.exists() and not good.exists():
        if not dry_run:
            bad.rename(good)
        notes.append(f"renamed {bad.name} -> {good.name}")
    return notes


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Нормализация generated JSON-батчей Белпомощника.")
    parser.add_argument("files", nargs="*", type=Path, help="Файлы для нормализации.")
    parser.add_argument("--dry-run", action="store_true", help="Показать изменения без записи.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    notes = normalize_extremist_filename(dry_run=args.dry_run)
    files = args.files or sorted(IMPORT_DIR.glob("content_*_2022_2026*.json"))
    if not files:
        print("Нет файлов content_*_2022_2026*.json.")
        return 0
    for path in files:
        if not path.exists():
            continue
        changed, file_notes = normalize_batch(path, dry_run=args.dry_run)
        status = "changed" if changed else "ok"
        print(f"{status}: {path}")
        for note in file_notes:
            print(f"  - {note}")
    for note in notes:
        print(note)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
