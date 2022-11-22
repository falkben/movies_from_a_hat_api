from datetime import datetime as dt

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.movies import TMDB_URL, TMDBResult
from app.tables import Genre, Movie

DUDE_DATA = {"title": "The Big Lebowski", "year": 1998, "runtime": 117}
DUDE_GENRES_DATA = ["comedy", "crime"]


@pytest.fixture
async def dude_movie(session: AsyncSession):
    movie = Movie(**DUDE_DATA)
    movie.genres = [Genre(name=g) for g in DUDE_GENRES_DATA]
    session.add(movie)
    await session.commit()
    await session.refresh(movie)
    yield movie


def test_create_movie(client: TestClient):
    # takes FORM data
    resp = client.post("/movie/", data=DUDE_DATA)
    data = resp.json()

    assert resp.status_code == 200
    assert data["id"] is not None
    assert data["title"] == DUDE_DATA["title"]
    assert data["year"] == DUDE_DATA["year"]
    assert data["runtime"] == DUDE_DATA["runtime"]
    assert dt.fromisoformat(data["created_at"]) < dt.utcnow()
    assert data["genres"] == []


async def test_create_movies_same_title_diff_year(
    client: TestClient, dude_movie: Movie
):

    resp = client.post("/movie/", data=DUDE_DATA | {"year": 1950})
    data = resp.json()

    assert resp.status_code == 200
    assert data["id"] is not None
    assert data["title"] == DUDE_DATA["title"]
    assert data["year"] == 1950
    assert data["runtime"] == DUDE_DATA["runtime"]
    assert dt.fromisoformat(data["created_at"]) < dt.utcnow()
    assert data["genres"] == []


async def test_create_movies_same_title_same_year(
    client: TestClient, dude_movie: Movie
):
    """Movie title and year is unique"""

    resp = client.post("/movie/", data=DUDE_DATA)
    assert resp.status_code == 422


def test_create_movie_genres(client: TestClient):
    # takes FORM data
    resp = client.post("/movie/", data=DUDE_DATA | {"genres": DUDE_GENRES_DATA})
    data = resp.json()

    assert resp.status_code == 200
    assert data["id"] is not None
    assert data["title"] == DUDE_DATA["title"]
    assert data["year"] == DUDE_DATA["year"]
    assert data["runtime"] == DUDE_DATA["runtime"]
    assert dt.fromisoformat(data["created_at"]) < dt.utcnow()
    assert [g["name"] for g in data["genres"]] == DUDE_GENRES_DATA


def test_create_movie_incomplete(client: TestClient):
    # no year
    resp = client.post("/movie/", data={"title": "No year movie"})
    assert resp.status_code == 422

    # no title
    resp = client.post("/movie/", data={"year": 4444})
    assert resp.status_code == 422


def test_create_movie_invalid(client: TestClient):
    # year takes an int, not a mapping/dict
    resp = client.post(
        "/movie/",
        data={
            "title": "Bad year type",
            "year": {"year": "1998"},
        },
    )
    assert resp.status_code == 422

    # year needs to be convertable to an int
    resp = client.post(
        "/movie/",
        data={
            "title": "Bad year value",
            "year": "5555_three",
        },
    )
    assert resp.status_code == 422


async def test_read_movie(client: TestClient, dude_movie: Movie):

    resp = client.get(f"/movie/{dude_movie.id}")
    data = resp.json()

    assert resp.status_code == 200
    assert data["title"] == DUDE_DATA["title"]
    assert data["year"] == DUDE_DATA["year"]
    assert data["runtime"] == DUDE_DATA["runtime"]
    assert dt.fromisoformat(data["created_at"]) < dt.utcnow()
    assert data["updated_at"] is None


async def test_update_movie(client: TestClient, dude_movie: Movie):
    resp = client.patch(f"/movie/{dude_movie.id}", data={"title": "The Dude"})
    data = resp.json()

    assert resp.status_code == 200
    assert data["title"] == "The Dude"
    assert data["runtime"] == DUDE_DATA["runtime"]
    assert data["id"] == dude_movie.id
    assert data["updated_at"] is not None

    # update the genres
    resp = client.patch(f"/movie/{dude_movie.id}", data={"genres": ["90s"]})
    assert resp.status_code == 200
    assert [g["name"] for g in resp.json()["genres"]] == ["90s"]

    # update genres with same data (instead of creating new objects we "get" existing instance)
    resp = client.patch(f"/movie/{dude_movie.id}", data={"genres": ["90s"]})
    assert resp.status_code == 200
    assert [g["name"] for g in resp.json()["genres"]] == ["90s"]


async def test_delete_movie(
    session: AsyncSession, client: TestClient, dude_movie: Movie
):

    resp = client.delete(f"/movie/{dude_movie.id}")
    assert resp.status_code == 200

    movie_in_db = await session.get(Movie, dude_movie.id)
    assert movie_in_db is None


def test_search_movies(client: TestClient, mocked_TMDB):
    resp = client.get("/search_movies/", params={"query": "big"})
    assert resp.status_code == 200
    for result_dict in resp.json():
        TMDBResult.parse_obj(result_dict)


def test_search_movies_not_found(client: TestClient, respx_mock):
    tmdb_route = respx_mock.get(TMDB_URL, name="search_tmdb_movies")
    tmdb_route.return_value = httpx.Response(404)
    resp = client.get("/search_movies/", params={"query": "big"})
    assert resp.status_code == 400
    assert resp.json() == {"detail": "Bad search params"}


def test_search_movies_tmdb_down(client: TestClient, respx_mock):
    tmdb_route = respx_mock.get(TMDB_URL, name="search_tmdb_movies")
    tmdb_route.return_value = httpx.Response(500)
    resp = client.get("/search_movies/", params={"query": "big"})
    assert resp.status_code == 504
    assert resp.json() == {"detail": "Gateway Timeout"}
