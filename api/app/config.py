from pydantic import BaseSettings, Field


class Settings(BaseSettings):

    tmdb_api_key: str = Field(..., env="TMDB_API_TOKEN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
