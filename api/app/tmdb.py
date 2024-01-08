import asyncio
import re
import sys
from datetime import date

import httpx
from fastapi import HTTPException
from loguru import logger
from loguru._defaults import LOGURU_FORMAT
from pydantic import BaseModel, Field, ValidationError


def obfuscate_message(message: str):
    """Obfuscate sensitive information."""
    result = re.sub(r"api_key=[a-zA-Z0-9]*", "api_key=xxxxxx", message)
    return result


def formatter(record):
    record["extra"]["obfuscated_message"] = obfuscate_message(record["message"])

    new_format = LOGURU_FORMAT.replace("message", "extra[obfuscated_message]")

    # when using a callable it seems we need to add a terminator to the message
    return new_format + "\n"


# replace the default handler with one that obfuscates the api key
logger.remove(0)
logger.add(sys.stderr, colorize=True, format=formatter)


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
    imdb_id: str | None = None
    poster: str | None = Field(None, alias="poster_path")
    adult: bool = False


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


def resp_error_handling(resp: httpx.Response):
    """Generalized error handler for tmdb responses"""

    # todo: remove sensitive info (api key) from logged data
    # in the query argument of resp.request URL

    if 400 <= resp.status_code < 500:
        # error in user submission
        logger.error(
            "Error from TMDB. Request: {}, Response: {}",
            resp.request,
            resp,
        )
        raise HTTPException(resp.status_code, "Bad search params")

    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error(
            "Error from TMDB. Request: {}, Response: {}",
            resp.request,
            e.response,
        )
        raise HTTPException(504)


async def tmdb_search(params, api_url) -> TMDBSearchResult:
    async with sem:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{api_url}/search/movie", params=params)

    resp_error_handling(resp)

    return resp.json()["results"]


def get_rating_from_release_dates(release_dates: ReleaseDates) -> str | None:
    # get the rating from the nested release dates

    for result in release_dates.results:
        if result.iso_3166_1 != "US":
            continue

        # most likely the last release has the rating so iterate over list backwards
        for release in result.release_dates[::-1]:
            if release.certification:
                return release.certification


async def get_movie_data(
    tmdb_id: int, tmdb_api_url: str, tmdb_api_key: str
) -> tuple[TMDBMovieResult, str | None, list[str]]:
    async with sem:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{tmdb_api_url}/movie/{tmdb_id}?api_key={tmdb_api_key}&append_to_response=release_dates"
            )

            resp_error_handling(resp)

            tmdb_data = resp.json()
            try:
                movie_data = TMDBMovieResult(**tmdb_data)
            except ValidationError:
                logger.error("Error parsing tmdb movie data response for {}", tmdb_data)
                raise HTTPException(500)
            try:
                release_dates = ReleaseDates(**tmdb_data.get("release_dates"))
            except ValidationError:
                logger.error(
                    "Error parsing tmdb release dates for {}",
                    tmdb_data.get("release_dates"),
                )
                raise HTTPException(500)
            rating = get_rating_from_release_dates(release_dates)

            genres_data = tmdb_data.get("genres")
            genres = [g["name"] for g in genres_data]

            return movie_data, rating, genres
