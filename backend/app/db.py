from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .core.config import get_settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    url = get_settings().database_url
    engine = create_engine(url)
    if url.startswith("sqlite"):
        # SQLite FK'leri varsayılan olarak ZORLAMAZ; Postgres zorlar. Testler
        # prod'la aynı davranmazsa FK sırası hataları (ör. hesap silme) gözden
        # kaçar — bu yüzden testte de açık.
        @event.listens_for(engine, "connect")
        def _fk_on(dbapi_conn, _record):
            dbapi_conn.execute("PRAGMA foreign_keys=ON")

    return engine


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
