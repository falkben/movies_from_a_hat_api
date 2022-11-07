from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func
from sqlmodel import Field, Relationship, SQLModel

# todo User
# todo: Watched (date) is a M2M with Users and Movies


class GenreMovieLink(SQLModel, table=True):
    genre_id: int | None = Field(default=None, foreign_key="genre.id", primary_key=True)
    movie_id: int | None = Field(default=None, foreign_key="movie.id", primary_key=True)


class Genre(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    movies: list["Movie"] = Relationship(
        back_populates="genres", link_model=GenreMovieLink
    )


class MovieBase(SQLModel):
    title: str = Field(default=..., index=True)
    # todo: add "gt" constraint on database
    year: int = Field(default=..., index=True, gt=1878)
    runtime: int = Field(default=..., index=True)
    url: str | None = Field(default=None, description="imdb url")
    img: str | None = Field(default=None, description="url to image")
    rating: str | None = Field(default=None, description="MPAA rating")
    nsfw: bool = False


class Movie(MovieBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )
    # todo: cascade on delete (sa_relationship_kwargs)
    genres: list[Genre] = Relationship(
        back_populates="movies", link_model=GenreMovieLink
    )
    # todo: created_by (user)


class MovieCreate(MovieBase):
    genres: list[str] = []


class MovieRead(MovieBase):
    id: int
    created_at: datetime
    updated_at: datetime | None
    genres: list[Genre] = []


class MovieUpdate(MovieBase):
    title: str | None = None
    year: int | None = Field(default=None, gt=1878)
    runtime: int | None = None
    nsfw: bool | None = None
    genres: list[str] | None = None
