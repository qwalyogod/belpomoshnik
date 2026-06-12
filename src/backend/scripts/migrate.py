"""
Применяет нумерованные .sql-миграции к MySQL 8 (через PyMySQL).

Идемпотентно: применённые миграции отмечаются в таблице `schema_migrations`.

Использование:
    python -m backend.scripts.migrate

URL читается из `BELPOMOSHNIK_DATABASE_URL` (см. backend.config). По умолчанию —
локальный MySQL из docker-compose.

Ожидаемый формат URL: mysql+pymysql://user:password@host:port/database?charset=utf8mb4
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import pymysql

from backend.config import get_database_url

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"


def _parse_mysql_url(url: str) -> dict:
    """SQLAlchemy-URL → kwargs для pymysql.connect()."""
    if not url.startswith("mysql+pymysql://"):
        raise SystemExit(
            f"migrate.py поддерживает только MySQL (mysql+pymysql://...). Получено: {url!r}"
        )
    # Отрезаем диалектный префикс, чтобы корректно парсить query (charset и т.п.)
    parsed = urlparse(url.replace("mysql+pymysql://", "mysql://", 1))
    if not parsed.hostname or not parsed.path.lstrip("/"):
        raise SystemExit(f"Не удалось распарсить host/database из URL: {url!r}")
    return {
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "user": parsed.username or "root",
        "password": parsed.password or "",
        "database": parsed.path.lstrip("/").split("?")[0],
        "charset": "utf8mb4",
        "autocommit": False,
    }


def _split_statements(sql: str) -> list[str]:
    """Грубый сплиттер SQL на отдельные statements по `;`.\n\n    PyMySQL не умеет в executescript (это фича sqlite3), поэтому делим руками.\n    Комментарии `-- ...` и пустые строки игнорируем. Для наших .sql-миграций этого\n    достаточно — CREATE TABLE / INSERT без вложенных точек с запятой.\n    """
    cleaned_lines: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        cleaned_lines.append(line)
    cleaned = "\n".join(cleaned_lines)
    return [stmt.strip() for stmt in cleaned.split(";") if stmt.strip()]


def _ensure_database(kwargs: dict) -> None:
    """Создать БД, если её нет (без указания database). Подключаемся к серверу."""
    server_kwargs = {k: v for k, v in kwargs.items() if k != "database"}
    conn = pymysql.connect(**server_kwargs)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{kwargs['database']}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
    finally:
        conn.close()


def run() -> None:
    url = get_database_url()
    kwargs = _parse_mysql_url(url)
    _ensure_database(kwargs)

    if not MIGRATIONS_DIR.is_dir():
        print(f"Каталог миграций не найден: {MIGRATIONS_DIR}")
        return

    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not files:
        print("Миграции не найдены.")
        return

    conn = pymysql.connect(**kwargs)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    name VARCHAR(255) NOT NULL PRIMARY KEY,
                    applied_at DATETIME NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            cur.execute("SELECT name FROM schema_migrations")
            applied = {row[0] for row in cur.fetchall()}

            applied_count = 0
            for migration in files:
                if migration.name in applied:
                    continue
                sql = migration.read_text(encoding="utf-8")
                statements = _split_statements(sql)
                for stmt in statements:
                    cur.execute(stmt)
                cur.execute(
                    "INSERT INTO schema_migrations (name, applied_at) VALUES (%s, %s)",
                    (migration.name, datetime.now(timezone.utc).replace(tzinfo=None)),
                )
                applied_count += 1
                print(f"[OK] Применена миграция: {migration.name}")
        conn.commit()
        print(f"Готово. Новых миграций: {applied_count}.")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
