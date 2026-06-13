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
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Здесь мы перехватываем управление и подсовываем URL из .env"""
    configuration = config.get_section(config.config_ini_section) or {}
    
    # ИМЕННО ТУТ подменяем URL на наш асинхронный sqlite из .env
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_offline() -> None:
    """Режим оффлайн (генерация SQL скриптов без подключения к БД)"""
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Главная точка входа, которая запускает асинхронный цикл"""
    asyncio.run(run_async_migrations())

# ВОТ ЭТОТ БЛОК ОБЯЗАТЕЛЬНО ДОЛЖЕН БЫТЬ В САМОМ КОНЦЕ ФАЙЛА:
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
