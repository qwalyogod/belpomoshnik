import os
from pathlib import Path


def get_database_url() -> str:
    """
    Возвращает URL для подключения к MySQL.

    По умолчанию — локальный MySQL 8 в docker-compose (localhost:3306,
    user=root, password=belp_root, database=belpomoshnik).

    Переопределяется переменной BELPOMOSHNIK_DATABASE_URL в .env.
    """
    return os.getenv(
        "BELPOMOSHNIK_DATABASE_URL",
        "mysql+pymysql://root:belp_root@127.0.0.1:3306/belpomoshnik?charset=utf8mb4",
    )


def get_upload_dir() -> str:
    """
    Директория для пользовательских загрузок (изображения к статьям, сканы и т.п.).

    По умолчанию — `<корень проекта>/data/uploads`. Переопределяется через
    `BELPOMOSHNIK_UPLOAD_DIR` в .env (полезно для docker-volume в проде).
    """
    custom = os.getenv("BELPOMOSHNIK_UPLOAD_DIR")
    if custom:
        return custom
    # src/backend/config.py → подняться на 2 уровня до корня проекта
    return str(Path(__file__).resolve().parents[2] / "data" / "uploads")
