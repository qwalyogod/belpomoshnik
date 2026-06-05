from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from backend.config import DEFAULT_DB_PATH


def run() -> None:
    from backend.config import get_database_url

    if not get_database_url().startswith("sqlite"):
        raise SystemExit(
            "migrate.py поддерживает только SQLite (.sql-миграции). "
            "Для PostgreSQL используйте: python -m backend.bootstrap"
        )

    db_path = Path(DEFAULT_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    migrations_dir = Path(__file__).resolve().parents[1] / "migrations"
    files = sorted(migrations_dir.glob("*.sql"))
    if not files:
        print("Миграции не найдены.")
        return

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                name TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """
        )
        applied = {row[0] for row in conn.execute("SELECT name FROM schema_migrations").fetchall()}

        applied_count = 0
        for migration in files:
            if migration.name in applied:
                continue
            sql = migration.read_text(encoding="utf-8")
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO schema_migrations (name, applied_at) VALUES (?, ?)",
                (migration.name, datetime.now(timezone.utc).isoformat()),
            )
            applied_count += 1
            print(f"[OK] Применена миграция: {migration.name}")

        conn.commit()
        print(f"Готово. Новых миграций: {applied_count}.")
    finally:
        conn.close()


if __name__ == "__main__":
    run()

