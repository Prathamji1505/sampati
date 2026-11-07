from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


def make_engine(url: str, **kwargs):
    return create_engine(url, pool_pre_ping=True, **kwargs)


engine = make_engine(settings.database_url) if settings.database_url else None
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_session():
    if engine is None:
        raise RuntimeError('Configure the local database with scripts/dev.py setup first.')
    with SessionLocal() as session:
        yield session
