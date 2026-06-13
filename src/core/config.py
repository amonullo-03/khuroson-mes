from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    """
    Главная конфигурация проекта Khuroson MES.
    Все параметры читаются из файла .env в корне проекта.
    """

    # === PROJECT ===
    PROJECT_NAME: str = "Khuroson MES"
    VERSION: str = "2.0.0"
    DEBUG: bool = False

    # === DATABASE (component parts для гибкости) ===
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str

    # === DATABASE POOL (production-важно!) ===
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False  # SQLAlchemy echo для логирования SQL в разработке

    # === LOGGING ===
    LOG_LEVEL: str = "INFO"

    # === CORS ===
    CORS_ORIGINS: List[str] = ["*"]

    # === API ===
    API_V1_PREFIX: str = "/api/v1"

    # === SECURITY ===
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # === COMPUTED PROPERTIES ===
    @property
    def database_url_async(self) -> str:
        """
        URL для асинхронного engine (FastAPI + asyncpg).
        Используется в src/core/database.py для create_async_engine().
        """
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def database_url_sync(self) -> str:
        """
        URL для синхронного подключения (Alembic миграции, тесты).
        Используется в alembic/env.py и tests/conftest.py для psycopg2.
        """
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
