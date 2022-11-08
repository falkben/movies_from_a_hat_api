from datetime import datetime

from sqlalchemy import CheckConstraint, Column, DateTime, UniqueConstraint
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
    year: int = Field(default=..., index=True, gt=1878)
    runtime: int = Field(default=..., index=True)
    url: str | None = Field(default=None, description="imdb url")
    img: str | None = Field(default=None, description="url to image")
    rating: str | None = Field(default=None, description="MPAA rating")
    nsfw: bool = False


class Movie(MovieBase, table=True):
    # require movies to be unique on year and title
    __table_args__ = (UniqueConstraint("year", "title", name="_year_title_uc"),)

    # note: sqlite will use the next largest available integer on inserts
    # meaning that primary keys can be re-used from previously deleted rows
    # https://sqlite.org/autoinc.html
    id: int | None = Field(default=None, primary_key=True)
    # CheckConstraint enforces this at the database level https://docs.sqlalchemy.org/en/14/core/constraints.html#check-constraint
    year: int = Field(default=..., sa_column_args=[CheckConstraint("year>1878")])
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
