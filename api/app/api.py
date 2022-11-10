"""Main entrypoint"""

from datetime import date

import httpx
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from loguru import logger
from pydantic import BaseModel, BaseSettings, Field
from sqlmodel import Session, SQLModel, create_engine, select

from app import tables
from app.db_helpers import commit, get_or_create


class Settings(BaseSettings):
    tmdb_api_key: str = Field(..., env="TMDB_API_TOKEN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

sqlite_file_name = "database.sqlite"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


def handle_poster_submission(poster_file: UploadFile | None) -> str | None:
    if poster_file is None:
        return None

    # todo: if poster image submitted, handle the poster file:
    # todo: resize poster image as needed
    # todo: convert to jpeg
    # todo: save poster image to disk, with unique name
    # todo: get the poster image url and store in poster_url

    poster_url = "/static/path/poster_img.jpg"
    return poster_url


class TMDBResult(BaseModel):
    id: int | None
    title: str | None
    overview: str | None
    release_date: date | str | None
    poster_path: str | None
    genre_ids: list[int]


@app.get("/search_movies/", response_model=list[TMDBResult])
async def search_movies(
    query: str = Query(..., description="Percent encoded query"),
    year: int | None = Query(None),
):

    params = {
        "api_key": settings.tmdb_api_key,
        "query": query,
        "include_adult": False,
    }
    if year is not None:
        params["year"] = year

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.themoviedb.org/3/search/movie", params=params
        )

    return resp.json()["results"]


# todo: admin only?
@app.post("/movie/", response_model=tables.MovieRead)
def create_movie(
    title: str = Form(default=...),
    year: int = Form(default=..., gt=1878),
    runtime: int = Form(default=None, index=True),
    url: str | None = Form(default=None, description="imdb url"),
    poster: UploadFile | None = File(None, description="Movie poster"),
    rating: str | None = Form(default=None, description="MPAA rating"),
    nsfw: bool = Form(default=False),
    genres: list[str] = Form(default=[]),
    session: Session = Depends(get_session),
):
    """With a single API request, get all data to create a movie

    Note: cumbersome to do manually
    """

    poster_url = handle_poster_submission(poster)

    db_movie = tables.Movie(
        title=title,
        year=year,
        runtime=runtime,
        url=url,
        poster=poster_url,
        rating=rating,
        nsfw=nsfw,
    )  # pyright: ignore [reportGeneralTypeIssues]

    # adding genres to movie
    db_genres = []
    for genre in genres:
        db_genres.append(get_or_create(session, tables.Genre, name=genre))
    db_movie.genres = db_genres

    session.add(db_movie)
    commit(session)
    session.refresh(db_movie)

    logger.info(f"Created movie: {db_movie.dict()}")

    return db_movie


@app.get("/movies/", response_model=list[tables.MovieRead])
def list_movies(session: Session = Depends(get_session)):
    movies = session.exec(select(tables.Movie)).all()
    return movies


@app.get("/movie/{movie_id}", response_model=tables.MovieRead)
def read_movie(movie_id: int, session: Session = Depends(get_session)):
    movie = session.get(tables.Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


# todo: admin only?
@app.patch("/movie/{movie_id}", response_model=tables.MovieRead)
def update_movie(
    movie_id: int,
    title: str | None = Form(default=None),
    year: int | None = Form(default=None, gt=1878),
    runtime: int | None = Form(default=None, index=True),
    url: str | None = Form(default=None, description="imdb url"),
    poster: UploadFile | None = File(None, description="Movie poster"),
    rating: str | None = Form(default=None, description="MPAA rating"),
    nsfw: bool | None = Form(default=None),
    genres: list[str] | None = Form(default=None),
    session: Session = Depends(get_session),
):

    db_movie = session.get(tables.Movie, movie_id)
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    poster_url = handle_poster_submission(poster)

    movie = tables.MovieUpdate(
        title=title,
        year=year,
        runtime=runtime,
        url=url,
        poster=poster_url,
        rating=rating,
        nsfw=nsfw,
    )
    movie_data = movie.dict(exclude_defaults=True)
    for key, value in movie_data.items():
        setattr(db_movie, key, value)

    # adding genres to movie
    if genres is not None:
        db_genres = []
        for genre in genres:
            db_genres.append(get_or_create(session, tables.Genre, name=genre))
        db_movie.genres = db_genres

    session.add(db_movie)
    commit(session)
    session.refresh(db_movie)

    logger.info(f"Updated movie: {db_movie.dict()}")
    return db_movie


@app.delete("/movie/{movie_id}")
def delete_movie(movie_id: int, session: Session = Depends(get_session)):
    movie = session.get(tables.Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    session.delete(movie)
    commit(session)

    logger.info(f"Deleted movie: {movie.dict()}")
    return {"ok": True}
