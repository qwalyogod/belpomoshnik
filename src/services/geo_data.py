"""Geo reference loader — regions/districts + government institutions.

Reads data/import/regions.json and data/import/institutions.json once,
normalizes institution types to the app's short canonical set, and exposes
helpers for cascading region → district pickers and institution matching.
"""
from __future__ import annotations

import json
from pathlib import Path

_IMPORT_DIR = Path(__file__).resolve().parents[2] / "data" / "import"
_REGIONS_FILE = _IMPORT_DIR / "regions.json"
_INSTITUTIONS_FILE = _IMPORT_DIR / "institutions.json"

# Canonical short type → substrings that may appear in raw file values
_TYPE_MATCHERS: list[tuple[str, tuple[str, ...]]] = [
    ("ЗАГС", ("загс",)),
    ("Служба одно окно", ("одно окно", "одного окна")),
    ("Налоговая инспекция", ("налог", "имнс")),
    ("ОГиМ", ("огим", "гражданств", "миграц")),
    ("Поликлиника", ("поликлин", "больниц", "амбулатор")),
    ("Суд", ("суд",)),
    ("Орган социальной защиты", ("соц", "труд", "занятост")),
    ("ЖКХ / РСЦ", ("жкх", "рсц", "расчётно", "расчетно")),
    ("Исполком", ("исполком", "исполнительн")),
]

_cache: dict = {"regions": None, "institutions": None}


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def normalize_institution_type(raw: str) -> str:
    low = (raw or "").lower()
    for canonical, needles in _TYPE_MATCHERS:
        if any(n in low for n in needles):
            return canonical
    return raw or "Учреждение"


# ---------------------------------------------------------------------------
# Regions / districts
# ---------------------------------------------------------------------------

def load_regions() -> list[dict]:
    if _cache["regions"] is None:
        data = _read_json(_REGIONS_FILE)
        _cache["regions"] = data if isinstance(data, list) else []
    return _cache["regions"]


def region_names() -> list[str]:
    return [r.get("region", "") for r in load_regions() if r.get("region")]


def districts_for(region: str) -> list[str]:
    for r in load_regions():
        if r.get("region") == region:
            return [d.get("name", "") for d in r.get("districts", []) if d.get("name")]
    return []


def city_for_district(region: str, district: str) -> str:
    for r in load_regions():
        if r.get("region") == region:
            for d in r.get("districts", []):
                if d.get("name") == district:
                    return d.get("center") or district
    return district


# ---------------------------------------------------------------------------
# Institutions
# ---------------------------------------------------------------------------

def load_institutions() -> list[dict]:
    if _cache["institutions"] is None:
        raw = _read_json(_INSTITUTIONS_FILE)
        if isinstance(raw, dict):
            items = raw.get("items", [])
        elif isinstance(raw, list):
            items = raw
        else:
            items = []
        normalized: list[dict] = []
        for it in items:
            inst = dict(it)
            inst["institution_type"] = normalize_institution_type(inst.get("institution_type", ""))
            normalized.append(inst)
        _cache["institutions"] = normalized
    return _cache["institutions"]


def institutions_for_region(region: str, district: str | None = None) -> list[dict]:
    items = [i for i in load_institutions() if i.get("region") == region]
    if district:
        narrowed = [i for i in items if i.get("district") == district or i.get("city") == district]
        return narrowed or items
    return items


def institutions_by_type(institution_type: str, region: str | None = None) -> list[dict]:
    canonical = normalize_institution_type(institution_type)
    items = [i for i in load_institutions() if i.get("institution_type") == canonical]
    if region:
        items = [i for i in items if i.get("region") == region]
    return items


def has_geo_data() -> bool:
    return bool(load_regions()) and bool(load_institutions())
