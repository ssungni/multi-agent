import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5433/cartmate_test"
)
os.environ.setdefault("JWT_SECRET", "test-secret")

import pytest
from sqlalchemy import text

from src.core.database import Base, SessionLocal, engine


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
        session.rollback()
    finally:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()
