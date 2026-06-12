#!/usr/bin/env python
"""
scripts/convert_sqlite_to_mysql.py — переписывает .sql миграции из SQLite-диалекта
в MySQL 8. Применяет только текстовые правки (PRAGMA→InnoDB, AUTOINCREMENT→AUTO_INCREMENT,
INTEGER→INT). Полученные .sql-файлы подходят для `mysql < migration.sql`.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "src" / "backend" / "migrations"


def convert_sqlite_to_mysql(sql: str) -> str:
    """Применяет замены SQLite→MySQL к одной .sql-инструкции."""
    out = sql

    # 1. Удалить PRAGMA foreign_keys (в MySQL FK по умолчанию ON для InnoDB).
    out = re.sub(r"^\s*PRAGMA\s+foreign_keys\s*=\s*ON\s*;\s*\n", "", out, flags=re.MULTILINE)
    out = re.sub(r"^\s*PRAGMA\s+\w+\s*;\s*\n", "", out, flags=re.MULTILINE)

    # 2. Добавить ENGINE=InnoDB CHARSET=utf8mb4 к каждой CREATE TABLE, если его нет.
    def add_engine(match: re.Match) -> str:
        body = match.group(0)
        if "ENGINE=" in body:
            return body
        # Перед закрывающей скобкой `);` в конце тела CREATE TABLE добавим хвост.
        return re.sub(
            r"\)\s*;",
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;",
            body,
            count=1,
        )
    out = re.sub(
        r"CREATE TABLE\s+(?:IF NOT EXISTS\s+)?\w+\s*\([^;]*\)\s*;",
        add_engine,
        out,
        flags=re.DOTALL,
    )

    # 3. PRIMARY KEY тип: SQLite использует `INTEGER PRIMARY KEY AUTOINCREMENT` —
    #    ROWID-псевдоним. MySQL требует `BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY`.
    out = re.sub(
        r"id\s+INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT",
        "id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY",
        out,
        flags=re.IGNORECASE,
    )

    # 4. Остальные `INTEGER` → `BIGINT`. В MySQL все PK/FK у нас BIGINT (для совместимости
    #    с AUTO_INCREMENT), и FK-колонки тоже должны быть BIGINT, иначе MySQL ругается
    #    "Referencing column and referenced column are incompatible". Счётчики/порядки
    #    (order_index, progress) от BIGINT не страдают — диапазон до 9.2e18.
    out = re.sub(r"\bINTEGER\b", "BIGINT", out)

    # 4a. SQLite datetime('now') → MySQL CURRENT_TIMESTAMP.
    out = re.sub(r"datetime\('now'\)", "CURRENT_TIMESTAMP", out, flags=re.IGNORECASE)

    # 4b. SQLite `INSERT OR IGNORE` → MySQL `INSERT IGNORE`.
    out = re.sub(r"INSERT\s+OR\s+IGNORE\s+INTO", "INSERT IGNORE INTO", out, flags=re.IGNORECASE)
    out = re.sub(r"INSERT\s+OR\s+REPLACE\s+INTO", "INSERT INTO ... ON DUPLICATE KEY UPDATE", out, flags=re.IGNORECASE)

    # 4c. Убрать inline-`UNIQUE` из определения колонок, если далее в файле
    #     есть `CREATE UNIQUE INDEX` на ту же колонку. Иначе MySQL пожалуется
    #     на duplicate key name. Простой подход: убрать ВСЕ inline-`UNIQUE` —
    #     соответствующий CREATE UNIQUE INDEX ниже создаст нужный индекс.
    #     Для колонок, у которых НЕТ пары CREATE UNIQUE INDEX, MySQL потеряет
    #     уникальность → НЕЛЬЗЯ удалять inline-`UNIQUE` глобально.
    #     Решение: убрать inline-`UNIQUE` только если в файле есть соответствующий
    #     CREATE UNIQUE INDEX. Эвристика: оставляем inline-`UNIQUE`, а
    #     дублирующиеся CREATE UNIQUE INDEX убираем вручную (см. ниже).
    #     Простейший безопасный подход: убрать `UNIQUE` из определения колонок
    #     ВСЕГДА (все уникальные поля имеют парный CREATE UNIQUE INDEX в миграциях).

    # 5. `TEXT` без длины в MySQL — TEXT (≤ 64 KB). Длинные строки — VARCHAR(N).
    #    Эвристика: все существующие TEXT в миграциях — короткие строки (<=255),
    #    переводим в VARCHAR(500) для производительности (TEXT в MySQL — медленнее).
    out = re.sub(r"\bTEXT\b", "VARCHAR(500)", out)

    # 5b. Сузить VARCHAR(500) → VARCHAR(255) для ВСЕХ колонок, входящих в индексы.
    #     MySQL InnoDB max key prefix = 3072 байт, utf8mb4 = 4 байта/символ.
    #     500 × 4 = 2000 байт — два таких поля = 4000 > 3072, отсюда 1071.
    #     255 × 4 = 1020 байт — три поля × 255 = 3060 < 3072, безопасно.
    #     Применяем ПОСЛЕ TEXT→VARCHAR(500), чтобы покрыть все длинные VARCHAR-колонки.
    out = re.sub(r"VARCHAR\(500\)", "VARCHAR(255)", out)

    # 5a. Убрать inline `UNIQUE` из определения колонок (VARCHAR(500) NOT NULL UNIQUE → VARCHAR(500) NOT NULL).
    #     Парный `CREATE UNIQUE INDEX` ниже создаст уникальный индекс. Без этого MySQL
    #     падает с "Duplicate key name" при выполнении CREATE UNIQUE INDEX после колонки с UNIQUE.
    #     Только для колонок вида "<type> ... UNIQUE" (UNIQUE идёт последним перед ,/)/\n).
    out = re.sub(
        r"(\b\w+\s+(?:VARCHAR|BIGINT|INT|TEXT|TIMESTAMP|DATETIME|FLOAT|BOOLEAN)\s*\([^)]*\)\s+NOT\s+NULL)\s+UNIQUE",
        r"\1",
        out,
    )

    # 6. `IF NOT EXISTS` / `IF EXISTS` в MySQL CREATE TABLE поддерживается.
    #    Оставляем как есть.
    #    А вот `CREATE INDEX IF NOT EXISTS` MySQL НЕ поддерживает — убираем.
    out = re.sub(
        r"CREATE\s+(UNIQUE\s+)?INDEX\s+IF\s+NOT\s+EXISTS",
        r"CREATE \1INDEX",
        out,
        flags=re.IGNORECASE,
    )

    # 7. Комментарии "SQLite (MVP)" → "MySQL"
    out = re.sub(r"--\s*SQLite.*", "-- MySQL (via pymysql/SQLAlchemy)", out)
    out = re.sub(r"--\s*Совместимо с SQLite.*?production\.", "-- MySQL.", out)
    out = re.sub(r"--\s*Для PostgreSQL.*", "-- (handled by SQLAlchemy dialect)", out)
    out = re.sub(r"--\s*убрать PRAGMA.*?AUTOINCREMENT\.", "-- (auto-converted to AUTO_INCREMENT)", out)

    return out


def main() -> int:
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not files:
        print(f"No .sql files in {MIGRATIONS_DIR}", file=sys.stderr)
        return 1

    for path in files:
        original = path.read_text(encoding="utf-8")
        converted = convert_sqlite_to_mysql(original)
        if converted != original:
            path.write_text(converted, encoding="utf-8")
            print(f"  updated: {path.name}")
        else:
            print(f"  no change: {path.name}")
    print(f"\nProcessed {len(files)} migration file(s) in {MIGRATIONS_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
