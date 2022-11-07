"""Main entrypoint"""

from typing import List

from app import tables
from fastapi import FastAPI, HTTPException
from sqlmodel import Session, SQLModel, create_engine, select

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/movie/", response_model=tables.MovieRead)
def create_movie(movie: tables.MovieCreate):
    with Session(engine) as session:
        db_movie = tables.Movie.from_orm(movie)
        session.add(db_movie)
        session.commit()
        session.refresh(db_movie)
        return db_movie


@app.get("/movies/", response_model=List[tables.MovieRead])
def list_movies():
    with Session(engine) as session:
        movies = session.exec(select(tables.Movie)).all()
        return movies


@app.get("/movie/{movie_id}", response_model=tables.MovieRead)
def read_movie(movie_id: int):
    with Session(engine) as session:
        movie = session.get(tables.Movie, movie_id)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        return movie


@app.patch("/movie/{movie_id}", response_model=tables.MovieRead)
def update_movie(movie_id: int, movie: tables.MovieUpdate):
    with Session(engine) as session:
        db_movie = session.get(tables.Movie, movie_id)
        if not db_movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        movie_data = movie.dict(exclude_unset=True)
        for key, value in movie_data.items():
            setattr(db_movie, key, value)
        session.add(db_movie)
        session.commit()
        session.refresh(db_movie)
        return db_movie
