from datetime import date

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
    iso_639_1: str
    note: str | None = None
    release_date: str
    type: int


class Result(BaseModel):
    iso_3166_1: str
    release_dates: list[ReleaseDate]


class ReleaseDates(BaseModel):
    results: list[Result]
