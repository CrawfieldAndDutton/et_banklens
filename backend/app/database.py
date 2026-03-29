from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def apply_sqlite_migrations() -> None:
    """Lightweight ALTERs for dev SQLite DBs (create_all does not add new columns)."""
    if not str(engine.url).startswith("sqlite"):
        return
    with engine.begin() as conn:
        rows = conn.execute(text("PRAGMA table_info(bsi_monitoring_runs)")).fetchall()
        names = {r[1] for r in rows}
        if not names:
            return
        if "gen_ai_summary" not in names:
            conn.execute(text("ALTER TABLE bsi_monitoring_runs ADD COLUMN gen_ai_summary TEXT"))
        if "gen_ai_model" not in names:
            conn.execute(text("ALTER TABLE bsi_monitoring_runs ADD COLUMN gen_ai_model VARCHAR(128)"))
