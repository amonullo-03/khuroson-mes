"""Database configuration and session management for async operations."""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import DeclarativeBase

from src.core.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


# === ASYNC ENGINE ДЛЯ FASTAPI ===
# asyncpg требует специальной конфигурации через connect_args
engine = create_async_engine(
    settings.database_url_async,
    echo=settings.DB_ECHO,
    future=True,
    # ✅ ПРАВИЛЬНАЯ конфигурация для asyncpg
    connect_args={
        "server_settings": {
            "application_name": settings.PROJECT_NAME,
            "jit": "off",  # Отключаем JIT компиляцию для стабильности
        },
        "timeout": 10,  # Timeout подключения
        "command_timeout": 10,  # Timeout команд
    },
    # Пул соединений
    pool_pre_ping=True,  # Проверяем соединение перед использованием (важно для долгоживущих соединений)
    pool_recycle=3600,  # Переиспользуем соединения каждый час (для избежания timeout'ов БД)
)

# === ASYNC SESSION FACTORY ===
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения БД сессии в эндпоинтах FastAPI.

    Пример использования в роутере:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
