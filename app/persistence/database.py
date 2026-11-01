from contextlib import contextmanager
from typing import Iterator
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.config import get_database_url

def make_engine(url: str | None = None) -> Engine:
    # pool_pre_ping — перевіряє, що з'єднання живе, перед використанням
    return create_engine(url or get_database_url(), pool_pre_ping=True)

@contextmanager
def session_scope(engine: Engine) -> Iterator[Session]:
    """Сесія, яка сама закриється; при помилці — відкотить зміни."""
    session = sessionmaker(engine, expire_on_commit=False)()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
