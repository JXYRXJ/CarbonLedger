from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, DeclarativeBase
from app.core.config import settings

# In SQLAlchemy 2.0, the preferred way to define models is using DeclarativeBase
class Base(DeclarativeBase):
    pass

# Configure connection pooling & pre-ping for health check
# Neon PostgreSQL database is serverless, pre_ping ensures dead connections are recycled
# If running SQLite (typically under testing), configure SQLite-compatible options
connect_args = {}
engine_kwargs = {
    "pool_recycle": 1800,
    "pool_pre_ping": True,
}

if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    from sqlalchemy.pool import StaticPool
    engine_kwargs["poolclass"] = StaticPool
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_timeout"] = 30

db_url = settings.DATABASE_URL
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    db_url,
    connect_args=connect_args,
    **engine_kwargs
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator:
    """
    FastAPI dependency that provides a transactional database session.
    Automatically closes the session after request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health() -> bool:
    """
    Executes a simple query to verify database health.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            return True
    except Exception:
        return False
