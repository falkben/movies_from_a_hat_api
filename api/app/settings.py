from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    database_connection_str = "sqlite+aiosqlite:///database.sqlite"

    tmdb_api_key: str = Field(..., env="TMDB_API_TOKEN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
