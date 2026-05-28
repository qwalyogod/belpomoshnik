import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "belpomoshnik.db"


def get_database_url() -> str:
    return os.getenv("BELPOMOSHNIK_DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

