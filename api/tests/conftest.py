from unittest.mock import patch

import pytest
import respx
from faker import Faker
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import Engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.pool import StaticPool

from app.api import app
from app.db import get_session
from app.movies import TMDB_URL


@pytest.fixture(autouse=True)
def monkeypatch_settings_env_vars(monkeypatch):
    monkeypatch.setenv("TMDB_API_TOKEN", "TESTING")


@pytest.fixture(name="engine")
def engine_fixture():
    """create an in memory sqlite database"""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # after we switch to alembic instead of app startup event, need to initialize tables
    # from sqlmodel import SQLModel
    # SQLModel.metadata.create_all(engine)

    yield engine


@pytest.fixture(autouse=True)
def patch_engine(engine: Engine):
    """patch the app engine so that events use this value"""
    with patch("app.db.engine", engine):
        yield


@pytest.fixture(name="session")
async def session_fixture(engine: Engine):
    """This session fixture is used in our tests when we need to access the db"""
    async_session_factory = sessionmaker(
        engine,
        class_=AsyncSession,  # pyright: ignore [reportGeneralTypeIssues]
        expire_on_commit=False,
    )
    async with async_session_factory() as session:
        yield session


@pytest.fixture(name="client")
async def client_fixture(session: Session):
    """Create the test client

    Overrides the session dependency in our endpoints to use this session instead

    Note that because we create the database tables with a startup event
    (using create_db_and_tables), this fixture must occur in the parameter list before
    other database access fixtures.

    E.g. works:

    def my_test_func(client: TestClient, dude_movie: Movie): ...

    Doesn't work, because dude_movie fixture tries to access database tables:

    def my_test_func(dude_movie: Movie, client: TestClient): ...
    """

    def get_session_override():
        return session

    # Set the dependency override in the app.dependency_overrides dictionary.
    app.dependency_overrides[get_session] = get_session_override

    # context manager runs the app startup/shutdown/lifespan events
    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def mocked_TMDB():

    fake = Faker()
    fake.set_arguments("title", {"max_nb_chars": 50})
    fake.set_arguments("overview", {"nb_words": 30})
    fake.set_arguments("poster", {"text": "???????????????????????????.jpg"})
    fake_tmdb_json = (
        '{ "results": '
        + fake.json(
            data_columns={
                "id": "pyint",
                "title": "text:title",
                "overview": "sentence:overview",
                "release_date": "date",
                "poster_path": "lexify:poster",
                "genre_ids": ["pyint", "pyint", "pyint"],
            },
            num_rows=10,
        )
        + "}"
    )

    with respx.mock(assert_all_called=False) as respx_mock:
        tmdb_route = respx_mock.get(TMDB_URL, name="search_tmdb_movies")
        tmdb_route.return_value = Response(200, text=fake_tmdb_json)
        yield respx_mock
