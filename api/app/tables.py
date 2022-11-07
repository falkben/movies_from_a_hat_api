from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func
from sqlmodel import Field, SQLModel

# todo: Watched (date) is a M2M with Users and Movies


class MovieBase(SQLModel):
    title: str = Field(default=..., index=True)
    year: int = Field(default=..., index=True, gt=1878)
    runtime: int = Field(default=..., index=True)
    url: str | None = Field(default=None, description="imdb url")
    img: str | None = Field(default=None, description="url to image")
    rating: str | None = Field(default=None, description="MPAA rating")
    nsfw: bool = False

    # todo: created by user
    # todo: M2M column for Genres


class Movie(MovieBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )


class MovieCreate(MovieBase):
    pass


class MovieRead(MovieBase):
    id: int
    created_at: datetime
    updated_at: datetime | None


class MovieUpdate(SQLModel):
    title: str | None = None
    year: int | None = Field(default=None, gt=1878)
    runtime: int | None = None
    nsfw: bool | None = None
