from datetime import datetime as dt

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.tables import Movie

DUDE_DATA = {"title": "The Big Lebowski", "year": 1998, "runtime": 117}
DUDE_GENRES_DATA = ["comedy", "crime"]


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


def test_create_movies_same_title_diff_year(session: Session, client: TestClient):

    movie = Movie(**DUDE_DATA)
    session.add(movie)
    session.commit()

    resp = client.post("/movie/", data=DUDE_DATA | {"year": 1950})
    data = resp.json()

    assert resp.status_code == 200
    assert data["id"] is not None
    assert data["title"] == DUDE_DATA["title"]
    assert data["year"] == 1950
    assert data["runtime"] == DUDE_DATA["runtime"]
    assert dt.fromisoformat(data["created_at"]) < dt.utcnow()
    assert data["genres"] == []


def test_create_movies_same_title_same_year(session: Session, client: TestClient):
    """Movie title and year is unique"""

    movie = Movie(**DUDE_DATA)
    session.add(movie)
    session.commit()

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


def test_read_movie(session: Session, client: TestClient):

    movie = Movie(**DUDE_DATA)
    session.add(movie)
    session.commit()

    resp = client.get(f"/movie/{movie.id}")
    data = resp.json()

    assert resp.status_code == 200
    assert data["title"] == DUDE_DATA["title"]
    assert data["year"] == DUDE_DATA["year"]
    assert data["runtime"] == DUDE_DATA["runtime"]
    assert dt.fromisoformat(data["created_at"]) < dt.utcnow()
    assert data["updated_at"] is None


def test_update_movie(session: Session, client: TestClient):
    movie = Movie(**DUDE_DATA)
    session.add(movie)
    session.commit()

    resp = client.patch(f"/movie/{movie.id}", data={"title": "The Dude"})
    data = resp.json()

    assert resp.status_code == 200
    assert data["title"] == "The Dude"
    assert data["runtime"] == DUDE_DATA["runtime"]
    assert data["id"] == movie.id
    assert data["updated_at"] is not None


def test_delete_movie(session: Session, client: TestClient):
    movie = Movie(**DUDE_DATA)
    session.add(movie)
    session.commit()

    resp = client.delete(f"/movie/{movie.id}")
    assert resp.status_code == 200

    movie_in_db = session.get(Movie, movie.id)
    assert movie_in_db is None


# todo: test search movies on TMDB w/ mocked response

# def test_search_movies(client: TestClient):
#     resp = client.get("/search_movies/", params={"query": "big"})
#     assert resp.status_code == 200
