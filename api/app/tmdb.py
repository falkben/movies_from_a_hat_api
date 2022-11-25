import asyncio
from datetime import date

import httpx
from pydantic import BaseModel, Field


class TMDBSearchResult(BaseModel):
    id: int | None
    title: str | None
    overview: str | None
    release_date: date | str | None
    poster_path: str | None
    genre_ids: list[int]


class TMDBMovieResult(BaseModel):
    """This is a reflection of the TMDB movie result
    but with some fields ommitted and others aliased to how we store them"""

    tmdb_id: int = Field(..., alias="id")
    title: str
    release_date: date
    runtime: int
    imdb_id: str
    poster: str = Field(..., alias="poster_path")
    adult: bool


class ReleaseDate(BaseModel):
    certification: str
    iso_639_1: str | None
    note: str | None = None
    release_date: str
    type: int


class Result(BaseModel):
    iso_3166_1: str
    release_dates: list[ReleaseDate]


class ReleaseDates(BaseModel):
    results: list[Result]


# use a semaphore to avoid overloading the tmdb api
# https://rednafi.github.io/reflections/limit-concurrency-with-semaphore-in-python-asyncio.html
# https://anyio.readthedocs.io/en/stable/synchronization.html
sem = asyncio.Semaphore(3)


async def get_movie_data(tmdb_id: int, tmdb_api_url: str, tmdb_api_key: str):
    async with sem:
        async with httpx.AsyncClient() as client:
            return await client.get(
                f"{tmdb_api_url}/movie/{tmdb_id}?api_key={tmdb_api_key}&append_to_response=release_dates"
            )


def get_rating_from_release_dates(release_dates: ReleaseDates) -> str | None:
    # get the rating from the nested release dates

    for result in release_dates.results:
        if result.iso_3166_1 != "US":
            continue

        # most likely the last release has the rating so iterate over list backwards
        for release in result.release_dates[::-1]:
            if release.certification:
                return release.certification
