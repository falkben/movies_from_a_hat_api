import asyncio

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.future import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app import db, tables
from app.config import Settings, get_settings
from app.db_helpers import commit, get_object_or_404, get_or_create
from app.tmdb_models import ReleaseDates, TMDBMovieResult, TMDBSearchResult

router = APIRouter()


def get_rating_from_release_dates(release_dates: ReleaseDates) -> str | None:
    # get the rating from the nested release dates

    for result in release_dates.results:
        if result.iso_3166_1 != "US":
            continue

        # most likely the last release has the rating so iterate over list backwards
        for release in result.release_dates[::-1]:
            if release.certification:
                return release.certification


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


@router.post("/movie_from_tmdb/", response_model=list[tables.MovieRead])
async def create_movie_tmdb_id(
    tmdb_ids: list[int] = Query([], description="List of tmdb movie ids to create"),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(db.get_session),
):

    # todo: get movies that have matching tmdb id's from our database
    stmt = select(tables.Movie).filter(tables.Movie.tmdb_id.in_(tmdb_ids))
    existing_movies = (await session.scalars(stmt)).unique().all()

    # todo: use a semaphore to avoid overloading the tmdb api
    # https://rednafi.github.io/reflections/limit-concurrency-with-semaphore-in-python-asyncio.html
    # https://anyio.readthedocs.io/en/stable/synchronization.html

    # todo: exclude tmdbs which we have data for

    # remaining tmdb id's we need to fetch their data from tmdb
    async with httpx.AsyncClient() as client:
        tasks = [
            client.get(
                f"{settings.tmdb_api_url}/movie/{tmdb_id}?api_key={settings.tmdb_api_key}&append_to_response=release_dates"
            )
            for tmdb_id in tmdb_ids
        ]
        # todo: handle exceptions with a task group or anyio
        results = await asyncio.gather(*tasks)

    # add the missing movies to our database
    db_movies = []
    for result in results:
        result_data = result.json()
        movie_data = TMDBMovieResult(**result_data)

        release_dates = ReleaseDates(**result_data.get("release_dates"))
        rating = get_rating_from_release_dates(release_dates)

        # get the keys from data that we need
        db_movie = tables.Movie(rating=rating, **movie_data.dict())

        # adding genres to movie
        db_genres = []
        genres = [g["name"] for g in result_data["genres"]]
        for genre in genres:
            # todo: can we do this in a single operation or with task group?
            db_genres.append(await get_or_create(session, tables.Genre, name=genre))
        db_movie.genres = db_genres

        # todo: instead of serially, can we add in a single operation or with a task group
        session.add(db_movie)
        await commit(session)
        await session.refresh(db_movie)

        logger.info(f"Created movie: {db_movie.dict()}")

        # add to list of db_movies
        db_movies.append(db_movie)

    requested_movies = existing_movies + db_movies

    requested_movies.sort(key=lambda m: tmdb_ids.index(m.tmdb_id))
    return requested_movies


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
