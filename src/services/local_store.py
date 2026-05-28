from __future__ import annotations

import json
from pathlib import Path
import shutil
from typing import Any


STORE_PATH = Path(__file__).resolve().parents[2] / "data" / "app_state.json"
BACKUP_PATH = STORE_PATH.with_name("app_state.backup.json")


def _clone(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def _merge(default: Any, loaded: Any) -> Any:
    if isinstance(default, dict):
        result = _clone(default)
        if isinstance(loaded, dict):
            for key, value in loaded.items():
                result[key] = _merge(default.get(key), value) if key in default else _clone(value)
        return result
    if isinstance(default, list):
        return _clone(loaded) if isinstance(loaded, list) else _clone(default)
    return _clone(loaded) if loaded is not None else _clone(default)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def load_app_state(default_state: dict[str, Any]) -> dict[str, Any]:
    loaded = _read_json(STORE_PATH) if STORE_PATH.exists() else None
    if loaded is None and BACKUP_PATH.exists():
        loaded = _read_json(BACKUP_PATH)
        if loaded is not None:
            try:
                STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
                STORE_PATH.write_text(json.dumps(loaded, ensure_ascii=False, indent=2), encoding="utf-8")
            except OSError:
                pass
    if loaded is None:
        return _clone(default_state)
    return _merge(default_state, loaded)


def save_app_state(state: dict[str, Any]) -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if STORE_PATH.exists():
        try:
            shutil.copy2(STORE_PATH, BACKUP_PATH)
        except OSError:
            pass
    temp_path = STORE_PATH.with_suffix(".tmp")
    temp_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(STORE_PATH)
