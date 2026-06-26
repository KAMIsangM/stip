from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_database_url

_DATABASE_URL = get_database_url()
_IS_SQLITE = _DATABASE_URL.startswith("sqlite")

engine = create_engine(
    _DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30}
    if _IS_SQLITE
    else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Enable SQLite pragmas: foreign keys, WAL mode, busy timeout
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if _IS_SQLITE:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")       # 写前日志，允许并发读写
        cursor.execute("PRAGMA busy_timeout=5000")       # 等待锁超时 5 秒
        cursor.close()


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
