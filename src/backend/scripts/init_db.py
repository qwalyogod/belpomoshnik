"""
Инициализация БД, dialect-aware.

- SQLite (dev): применяет .sql миграции (scripts/migrate.py).
- PostgreSQL / прочее (prod): создаёт схему через SQLAlchemy + сидит роли
  (backend.bootstrap), т.к. .sql-миграции написаны под SQLite.
"""
from backend.database import engine


def run() -> None:
    if engine.dialect.name == "sqlite":
        from backend.scripts.migrate import run as run_migrations
        run_migrations()
    else:
        from backend.bootstrap import bootstrap_database
        bootstrap_database()


if __name__ == "__main__":
    run()
