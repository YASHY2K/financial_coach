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

    # Read-Only Database Config (Defaults if not set, but good to have explicit)
    POSTGRES_READONLY_USER: str = "financial_coach_readonly"
    POSTGRES_READONLY_PASSWORD: str = "readonly_password"

    # LLM Config
    LLM_API_KEY: str

    @computed_field
    def database_url(self) -> str:
        # Returns a SQLAlchemy compatible connection string
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @computed_field
    def readonly_database_url(self) -> str:
        # Returns a SQLAlchemy compatible connection string for the read-only user.
        # Note: Agents use synchronous drivers (psycopg2)
        return f"postgresql+psycopg2://{self.POSTGRES_READONLY_USER}:{self.POSTGRES_READONLY_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file=("../../.env", "../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Dependency Injection Root
settings = Settings()
