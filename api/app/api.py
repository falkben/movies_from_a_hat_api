"""Main entrypoint"""

from typing import List

from fastapi import Depends, FastAPI, HTTPException
from loguru import logger
from sqlmodel import Session, SQLModel, create_engine, select

from app import tables
from app.db_helpers import commit, get_or_create

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


@app.post("/movie/", response_model=tables.MovieRead)
def create_movie(movie: tables.MovieCreate, session: Session = Depends(get_session)):

    genres = movie.genres
    db_movie = tables.Movie.from_orm(movie)

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


@app.get("/movies/", response_model=List[tables.MovieRead])
def list_movies(session: Session = Depends(get_session)):
    movies = session.exec(select(tables.Movie)).all()
    return movies


@app.get("/movie/{movie_id}", response_model=tables.MovieRead)
def read_movie(movie_id: int, session: Session = Depends(get_session)):
    movie = session.get(tables.Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@app.patch("/movie/{movie_id}", response_model=tables.MovieRead)
def update_movie(
    movie_id: int, movie: tables.MovieUpdate, session: Session = Depends(get_session)
):

    db_movie = session.get(tables.Movie, movie_id)
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    movie_data = movie.dict(exclude_unset=True)
    genres = movie_data.pop("genres", None)
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
