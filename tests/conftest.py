"""Pytest fixtures для интеграционного тестирования."""
import pytest
import pytest_asyncio
import psycopg2
from dotenv import load_dotenv

from src.core.config import settings

# Загружаем .env файл явно
load_dotenv(".env")


@pytest_asyncio.fixture(autouse=True, scope="function")
async def clean_database():
    """
    Автоматическая очистка СУБД перед каждым тестом и после него.
    Сбрасывает все ID в 1 для гарантированной изоляции каждого теста.

    Использует settings.database_url_sync (синхронный URL через psycopg2).
    """
    try:
        # SETUP: Очищаем базу перед запуском теста
        conn = psycopg2.connect(settings.database_url_sync)
        cursor = conn.cursor()

        # Получаем список всех пользовательских таблиц (исключаем Alembic)
        cursor.execute(
            """
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' AND tablename NOT LIKE 'alembic%'
        """
        )
        tables = [row[0] for row in cursor.fetchall()]

        if tables:
            tables_str = ", ".join(tables)
            cursor.execute(f"TRUNCATE {tables_str} RESTART IDENTITY CASCADE;")

        # Создаем дефолтную фабричную локацию (ID всегда будет равен 1)
        cursor.execute(
            "INSERT INTO wms_locations (name, type) VALUES ('Цех Хуросон', 'FACTORY');"
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Ошибка очистки БД перед тестом: {e}")

    yield  # Здесь выполняются сами тесты

    try:
        # TEARDOWN: Подчищаем базу за собой после теста
        conn = psycopg2.connect(settings.database_url_sync)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' AND tablename NOT LIKE 'alembic%'
        """
        )
        tables = [row[0] for row in cursor.fetchall()]

        if tables:
            tables_str = ", ".join(tables)
            cursor.execute(f"TRUNCATE {tables_str} RESTART IDENTITY CASCADE;")

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Ошибка очистки БД после теста: {e}")
