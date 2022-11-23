from datetime import date

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app import db, tables
from app.config import Settings, get_settings
from app.db_helpers import commit, get_object_or_404, get_or_create

router = APIRouter()


class TMDBSearchResult(BaseModel):
    id: int | None
    title: str | None
    overview: str | None
    release_date: date | str | None
    poster_path: str | None
    genre_ids: list[int]


@router.get("/search_movies/", response_model=list[TMDBSearchResult])
async def search_movies(
    query: str = Query(..., description="Percent encoded query"),
    year: int | None = Query(None),
    settings: Settings = Depends(get_settings),
):

    params = {
        "api_key": settings.tmdb_api_key,
        "query": query,
        "include_adult": False,
    }
    if year is not None:
        params["year"] = year

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.tmdb_api_url}/search/movie", params=params)

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
@router.post("/movie/", response_model=tables.MovieRead)
async def create_movie(
    movie: tables.MovieCreate,
    genres: list[str] = Body(default=[]),
    session: AsyncSession = Depends(db.get_session),
):
    """Create a movie by passing params

    Note: we will also support creating movies by passing a TMDB id
    """

    db_movie = tables.Movie.from_orm(movie)

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


@router.get("/movies/", response_model=list[tables.MovieRead])
async def list_movies(session: AsyncSession = Depends(db.get_session)):
    movies = (await session.execute(select(tables.Movie))).scalars().unique().all()
    return movies


@router.get("/movie/{movie_id}", response_model=tables.MovieRead)
async def read_movie(movie_id: int, session: AsyncSession = Depends(db.get_session)):
    movie = await get_object_or_404(session, tables.Movie, movie_id)
    return movie


# todo: admin only?
@router.patch("/movie/{movie_id}", response_model=tables.MovieRead)
async def update_movie(
    movie_id: int,
    movie: tables.MovieUpdate | None = None,
    genres: list[str] | None = Body(default=None),
    session: AsyncSession = Depends(db.get_session),
):

    db_movie = await get_object_or_404(session, tables.Movie, movie_id)

    if movie:
        movie_data = movie.dict(exclude_defaults=True)
        for key, value in movie_data.items():
            setattr(db_movie, key, value)

    # adding genres to movie
    if genres is not None:
        db_genres = []
        for genre in genres:
            db_genres.append(await get_or_create(session, tables.Genre, name=genre))
        db_movie.genres = db_genres

    # best attempt at not updating the movie if no data is actually passed in
    if movie or genres is not None:
        session.add(db_movie)
        await commit(session)
        await session.refresh(db_movie)

        logger.info(f"Updated movie: {db_movie.dict()}")
    return db_movie


@router.delete("/movie/{movie_id}")
async def delete_movie(movie_id: int, session: AsyncSession = Depends(db.get_session)):
    movie = await get_object_or_404(session, tables.Movie, movie_id)
    await session.delete(movie)
    await commit(session)

    logger.info(f"Deleted movie: {movie.dict()}")
    return {"ok": True}
