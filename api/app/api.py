"""Main entrypoint"""

from datetime import date
from functools import lru_cache

import fastapi.openapi.utils
import httpx
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app import config, tables
from app.db_helpers import commit, get_or_create
from app.patch import get_request_body_with_explode

# monkeypatch to fix swaggerui explode arguments
fastapi.openapi.utils.get_openapi_operation_request_body = get_request_body_with_explode


TMDB_URL = "https://api.themoviedb.org/3/search/movie"


database_conn_str = "sqlite+aiosqlite:///database.sqlite"
engine = create_async_engine(database_conn_str, echo=False)


# todo: replace with Alembic
async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session():
    async_session_factory = sessionmaker(
        engine,
        class_=AsyncSession,  # pyright: ignore [reportGeneralTypeIssues]
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        yield session


@lru_cache
def get_settings():
    """dependency for returning settings"""
    return config.Settings()


app = FastAPI()


@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()


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
    settings: config.Settings = Depends(get_settings),
):

    params = {
        "api_key": settings.tmdb_api_key,
        "query": query,
        "include_adult": False,
    }
    if year is not None:
        params["year"] = year

    async with httpx.AsyncClient() as client:
        resp = await client.get(TMDB_URL, params=params)

    if 400 <= resp.status_code < 500:
        # error in user submission
        logger.error(
            "Error from TMDB search. Search: %s, Response: %s", params, resp.text
        )
        raise HTTPException(400, "Bad search params")

    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error(
            "Error from TMDB search. Search: %s, Response: %s", params, e.response.text
        )
        raise HTTPException(504)

    return resp.json()["results"]


# todo: admin only?
@app.post("/movie/", response_model=tables.MovieRead)
async def create_movie(
    title: str = Form(default=...),
    year: int = Form(default=..., gt=1878),
    runtime: int = Form(default=None, index=True),
    url: str | None = Form(default=None, description="imdb url"),
    poster: UploadFile | None = File(None, description="Movie poster"),
    rating: str | None = Form(default=None, description="MPAA rating"),
    nsfw: bool = Form(default=False),
    genres: list[str] = Form(default=[]),
    session: AsyncSession = Depends(get_session),
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
        db_genres.append(await get_or_create(session, tables.Genre, name=genre))
    db_movie.genres = db_genres

    session.add(db_movie)
    await commit(session)
    await session.refresh(db_movie)

    logger.info(f"Created movie: {db_movie.dict()}")

    return db_movie


@app.get("/movies/", response_model=list[tables.MovieRead])
async def list_movies(session: AsyncSession = Depends(get_session)):
    movies = (await session.execute(select(tables.Movie))).scalars().unique().all()
    return movies


@app.get("/movie/{movie_id}", response_model=tables.MovieRead)
async def read_movie(movie_id: int, session: AsyncSession = Depends(get_session)):
    movie = await session.get(tables.Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


# todo: admin only?
@app.patch("/movie/{movie_id}", response_model=tables.MovieRead)
async def update_movie(
    movie_id: int,
    title: str | None = Form(default=None),
    year: int | None = Form(default=None, gt=1878),
    runtime: int | None = Form(default=None, index=True),
    url: str | None = Form(default=None, description="imdb url"),
    poster: UploadFile | None = File(None, description="Movie poster"),
    rating: str | None = Form(default=None, description="MPAA rating"),
    nsfw: bool | None = Form(default=None),
    genres: list[str] | None = Form(default=None),
    session: AsyncSession = Depends(get_session),
):

    db_movie = await session.get(tables.Movie, movie_id)
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
            db_genres.append(await get_or_create(session, tables.Genre, name=genre))
        db_movie.genres = db_genres

    # todo: avoid add/commit if no data changed
    session.add(db_movie)
    await commit(session)
    await session.refresh(db_movie)

    logger.info(f"Updated movie: {db_movie.dict()}")
    return db_movie


@app.delete("/movie/{movie_id}")
async def delete_movie(movie_id: int, session: AsyncSession = Depends(get_session)):
    movie = await session.get(tables.Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    await session.delete(movie)
    await commit(session)

    logger.info(f"Deleted movie: {movie.dict()}")
    return {"ok": True}
