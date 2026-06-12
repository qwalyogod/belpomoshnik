"""
Инициализация MySQL-БД: применяет нумерованные .sql-миграции (migrate.py) +
создаёт роли/тест-аккаунты через SQLAlchemy (bootstrap).

Шаг 1 — миграции: дают актуальную DDL-схему (hand-written, c FK и индексами).
Шаг 2 — bootstrap: дополняет ролями и тестовыми аккаунтами, идемпотентно.

Запускать:
    python -m backend.scripts.init_db
"""
from backend.bootstrap import bootstrap_database
from backend.scripts.migrate import run as run_migrations


def run() -> None:
    run_migrations()
    bootstrap_database()


if __name__ == "__main__":
    run()
