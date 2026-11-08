
import os

os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "3307")
os.environ.setdefault("DB_NAME", "test_db")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-automated-tests")

import pytest
import database

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from database import Base

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

database.engine = test_engine

database.SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)

import main


def override_get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


main.app.dependency_overrides[main.get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    main.rate_limit_buckets.clear()

    yield

    Base.metadata.drop_all(bind=test_engine)
    main.rate_limit_buckets.clear()


@pytest.fixture(autouse=True)
def mock_cloudinary_upload(monkeypatch):
    def fake_cloudinary_upload(file, **kwargs):
        return {
            "secure_url": (
                "https://res.cloudinary.com/test-cloud/"
                "image/upload/test-image.png"
            )
        }

    monkeypatch.setattr(
        main.cloudinary.uploader,
        "upload",
        fake_cloudinary_upload,
    )


@pytest.fixture
def client():
    with TestClient(main.app) as test_client:
        yield test_client
