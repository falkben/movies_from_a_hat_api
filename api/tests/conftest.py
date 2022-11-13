from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.future import Engine
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from app.api import app, get_session


@pytest.fixture(autouse=True)
def monkeypatch_settings_env_vars(monkeypatch):
    monkeypatch.setenv("TMDB_API_TOKEN", "TESTING")


@pytest.fixture(name="engine")
def engine_fixture():
    """create an in memory sqlite database"""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    # after we switch to alembic instead of app startup event, need to initialize tables
    # from sqlmodel import SQLModel
    # SQLModel.metadata.create_all(engine)

    yield engine


@pytest.fixture(autouse=True)
def patch_engine(engine: Engine):
    """patch the app engine so that events use this value"""
    with patch("app.api.engine", engine):
        yield


@pytest.fixture(name="session")
def session_fixture(engine: Engine):
    """This session fixture is used in our tests when we need to access the db"""
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create the test client

    Overrides the session dependency in our endpoints to use this session instead
    """

    def get_session_override():
        return session

    # Set the dependency override in the app.dependency_overrides dictionary.
    app.dependency_overrides[get_session] = get_session_override

    # context manager runs the app startup/shutdown/lifespan events
    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
