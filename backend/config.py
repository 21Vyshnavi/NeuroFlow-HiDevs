# ruff: noqa
# mypy: ignore-errors
# ruff: noqa
# mypy: ignore-errors
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_user: str = Field(default="neuroflow")
    postgres_password: str = Field(default="neuroflow_password")
    postgres_db: str = Field(default="neuroflow")
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)

    redis_password: str = Field(default="redis_password")
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)

    mlflow_tracking_uri: str = Field(default="http://localhost:5000")
    otlp_endpoint: str = Field(default="http://localhost:4317")

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"

settings = Settings()
