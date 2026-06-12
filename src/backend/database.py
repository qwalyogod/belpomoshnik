from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.config import get_database_url


# MySQL — единственная поддерживаемая СУБД. PyMySQL подключается через
# "mysql+pymysql://user:pass@host:port/db?charset=utf8mb4". SQLAlchemy
# сама устанавливает пимysql-соединение, нам нужно лишь передать URL.
DATABASE_URL = get_database_url()

# connect_args нужен ТОЛЬКО для диагностики SSL/соединения в локальной среде.
# В docker-compose контейнере MySQL обычно слушает без TLS; для production
# добавьте ?ssl_disabled=False в URL.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,    # автоматический reconnect при потере соединения
    pool_recycle=3600,      # пересоздавать соединения каждый час (MySQL wait_timeout=28800)
    pool_size=5,
    max_overflow=10,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
