"""Alembic environment configuration for async migrations."""
import asyncio
import sys
from os.path import realpath, dirname
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 1. Добавляем корень проекта в пути поиска Python
sys.path.insert(0, dirname(dirname(realpath(__file__))))

# Теперь спокойно импортируем наши конфиги и модели
from src.core.config import settings
from src.models import Base

# Это стандартная настройка логов Alembic
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Передаем метаданные наших моделей
target_metadata = Base.metadata


def do_run_migrations(connection):
    """Выполнить миграции с уже готовым подключением."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Асинхронный режим миграций (для production с asyncpg).
    
    Подменяем конфигурацию Alembic на асинхронный URL из settings.
    Используем NullPool чтобы каждая миграция была в отдельном соединении.
    """
    configuration = config.get_section(config.config_ini_section) or {}

    # ✅ ВАЖНО: Используем ASYNC URL для asyncpg
    configuration["sqlalchemy.url"] = settings.database_url_async

    # ✅ Правильная конфигурация для asyncpg в Alembic
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Отключаем пул для миграций (каждая миграция в новом соединении)
        connect_args={
            "server_settings": {
                "application_name": f"{settings.PROJECT_NAME}-alembic",
            },
            "timeout": 30,  # Миграции могут быть долгими
        },
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_offline() -> None:
    """
    Режим оффлайн (генерация SQL скриптов без подключения к БД).
    
    Используем SYNC URL для корректной генерации SQL для PostgreSQL.
    Это нужно когда вы хотите просто сгенерировать SQL файл без реального применения.
    """
    # ✅ Используем SYNC URL для offline режима (psycopg2)
    url = settings.database_url_sync
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,  # Bind параметры прямо в SQL (вместо placeholders)
        dialect_opts={"paramstyle": "named"},  # Используем named параметры
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Главная точка входа, которая определяет режим и запускает нужную функцию.
    
    - Если Alembic в offline режиме: генерирует SQL скрипты
    - Если онлайн: запускает асинхронные миграции через asyncpg
    """
    if context.is_offline_mode():
        # Offline режим: просто генерируем SQL
        run_migrations_offline()
    else:
        # Online режим: запускаем асинхронный цикл для миграций
        asyncio.run(run_async_migrations())


# === ТОЧКА ВХОДА ===
# Этот блок ОБЯЗАТЕЛЬНО должен быть в самом конце файла
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
