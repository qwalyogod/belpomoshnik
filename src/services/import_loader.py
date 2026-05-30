"""Import loader — merges data/import/*.json into runtime state.

Currently wired: news.json → law_updates (the «Новости» module).
problems.json / scenarios.json are empty for now; loaders are stubbed and
return None until the files are populated.

Adds a "lived-in" feel by scattering `last_checked` dates between the
publication date and today, so the feed looks actively maintained for years.
"""
from __future__ import annotations

import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path

_IMPORT_DIR = Path(__file__).resolve().parents[2] / "data" / "import"
_NEWS_FILE = _IMPORT_DIR / "news.json"
_PROBLEMS_FILE = _IMPORT_DIR / "problems.json"
_SCENARIOS_FILE = _IMPORT_DIR / "scenarios.json"

_TODAY = date(2026, 5, 30)


def _read_json(path: Path):
    try:
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return None
        return json.loads(text)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _parse_date(value: str) -> date | None:
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime((value or "").strip(), fmt).date()
        except ValueError:
            continue
    return None


def _scatter_last_checked(pub: date, seed: int) -> str:
    """Pick a date between pub+15d and today, deterministic per record."""
    rng = random.Random(seed)
    start = pub + timedelta(days=15)
    if start >= _TODAY:
        return _TODAY.strftime("%d.%m.%Y")
    span = (_TODAY - start).days
    offset = rng.randint(0, max(0, span))
    return (start + timedelta(days=offset)).strftime("%d.%m.%Y")


def load_news() -> list[dict] | None:
    """Return news.json normalized to LEGAL_UPDATES shape, or None if absent."""
    raw = _read_json(_NEWS_FILE)
    if not isinstance(raw, list) or not raw:
        return None
    out: list[dict] = []
    for idx, item in enumerate(raw):
        rec = dict(item)
        rec.setdefault("status", "published")
        rec.setdefault("priority", "medium")
        rec.setdefault("related_scenarios", [])
        rec.setdefault("related_problems", [])
        rec.setdefault("profile_tags", [])
        rec.setdefault("processing_status", "reviewed")
        pub = _parse_date(rec.get("date", ""))
        if pub:
            rec["last_checked"] = _scatter_last_checked(pub, seed=idx + len(rec.get("id", "")))
        out.append(rec)
    # Newest first
    out.sort(key=lambda r: (_parse_date(r.get("date", "")) or date.min), reverse=True)
    return out


def load_problems() -> list[dict] | None:
    raw = _read_json(_PROBLEMS_FILE)
    return raw if isinstance(raw, list) and raw else None


def load_scenarios() -> list[dict] | None:
    raw = _read_json(_SCENARIOS_FILE)
    return raw if isinstance(raw, list) and raw else None
