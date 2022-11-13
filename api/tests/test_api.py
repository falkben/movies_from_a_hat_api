from datetime import datetime as dt

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.tables import Movie

big_lebowski = {"title": "The Big Lebowski", "year": 1998, "runtime": 117}


def test_api_import():
    import app  # noqa: F401


def test_create_movie(client: TestClient):
    # takes FORM data
    resp = client.post("/movie/", data=big_lebowski)
    data = resp.json()

    assert resp.status_code == 200
    assert data["id"] is not None
    assert data["title"] == big_lebowski["title"]
    assert data["year"] == big_lebowski["year"]
    assert data["runtime"] == big_lebowski["runtime"]


def test_create_movie_incomplete(client: TestClient):
    # no year
    resp = client.post("/movie/", data={"title": "No year movie"})
    assert resp.status_code == 422


def test_create_movie_invalid(client: TestClient):
    resp = client.post(
        "/movie/",
        data={
            "title": "Bad type movie on year",
            "year": {"year": "1998"},
        },
    )
    assert resp.status_code == 422


def test_read_movie(session: Session, client: TestClient):

    movie = Movie(**big_lebowski)
    session.add(movie)
    session.commit()

    resp = client.get(f"/movie/{movie.id}")
    data = resp.json()

    assert resp.status_code == 200
    assert data["title"] == big_lebowski["title"]
    assert data["year"] == big_lebowski["year"]
    assert data["runtime"] == big_lebowski["runtime"]
    assert dt.fromisoformat(data["created_at"]) < dt.utcnow()


def test_update_movie(session: Session, client: TestClient):
    movie = Movie(**big_lebowski)
    session.add(movie)
    session.commit()

    resp = client.patch(f"/movie/{movie.id}", data={"title": "The Dude"})
    data = resp.json()

    assert resp.status_code == 200
    assert data["title"] == "The Dude"
    assert data["runtime"] == big_lebowski["runtime"]
    assert data["id"] == movie.id


def test_delete_movie(session: Session, client: TestClient):
    movie = Movie(**big_lebowski)
    session.add(movie)
    session.commit()

    resp = client.delete(f"/movie/{movie.id}")
    assert resp.status_code == 200

    movie_in_db = session.get(Movie, movie.id)
    assert movie_in_db is None


# todo: test two movies with the same title can be added
# todo: test that title is required
