# app/src/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field


class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "Smart Financial Coach"
    DEBUG: bool = True

    # Database Config (Loads from ENV vars like POSTGRES_USER)
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432

    # LLM Config
    LLM_API_KEY: str

    @computed_field
    def database_url(self) -> str:
        # Returns a SQLAlchemy compatible connection string
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file=("../../.env", "../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Dependency Injection Root
settings = Settings()
