"""Khuroson MES Configuration Module.

Центральный модуль конфигурации проекта.
Все параметры читаются из файла .env в корне проекта.

Пример .env файла:
    PROJECT_NAME="Khuroson MES"
    DB_USER="mes_user"
    DB_PASSWORD="secure_password"
    DB_HOST="localhost"
    DB_PORT=5432
    DB_NAME="khuroson_mes"
    DEBUG=false
    LOG_LEVEL="INFO"
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """
    Главная конфигурация проекта Khuroson MES.
    
    Все параметры читаются из файла .env в ко��не проекта.
    Используется Pydantic v2 для валидации.
    """

    # === PROJECT ===
    PROJECT_NAME: str = "Khuroson MES"
    VERSION: str = "2.0.0"
    DEBUG: bool = False

    # === DATABASE (component parts для гибкости) ===
    # Разбиваем DATABASE_URL на компоненты для лучшей конфигурируемости
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str

    # === DATABASE POOL (production-важно!) ===
    # DB_POOL_SIZE: кол-во соединений в пуле для asyncpg
    # DB_MAX_OVERFLOW: доп. соединения сверх pool_size когда нужно (НЕ используется для asyncpg)
    # DB_ECHO: логирование SQL запросов в разработке
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    # === LOGGING ===
    LOG_LEVEL: str = "INFO"

    # === CORS ===
    # Для production: CORS_ORIGINS="http://localhost:3000,https://yourfrontend.com"
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

    # === COMPUTED PROPERTIES (вычисляемые поля) ===
    @property
    def database_url_async(self) -> str:
        """
        URL для асинхронного engine (FastAPI + asyncpg).
        
        Используется в:
        - src/core/database.py для create_async_engine()
        - alembic/env.py для run_async_migrations()
        
        Формат: postgresql+asyncpg://user:password@host:port/dbname
        """
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def database_url_sync(self) -> str:
        """
        URL для синхронного подключения (Alembic offline режим, тесты через psycopg2).
        
        Используется в:
        - alembic/env.py для run_migrations_offline()
        - tests/conftest.py для psycopg2.connect()
        
        Формат: postgresql://user:password@host:port/dbname
        """
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


# === SINGLETON ===
# Создаем единственный экземпляр Settings, который используется по всему проекту
settings = Settings()
