"""Pytest fixtures для интеграционного тестирования.

Фикстура clean_database запускается автоматически перед и после каждого теста,
очищая БД для гарантированной изоляции.

Тесты подключаются через sync URL (psycopg2) так как fixtures
не могут быть асинхронными на уровне setup/teardown.
"""
import pytest
import pytest_asyncio
import psycopg2
from dotenv import load_dotenv

from src.core.config import settings

# Загружаем .env файл явно (на случай если pytest запускается не из корня проекта)
load_dotenv(".env")


@pytest_asyncio.fixture(autouse=True, scope="function")
async def clean_database():
    """
    Автоматическая очистка СУБД перед каждым тестом и после него.
    
    SETUP фаза:
    - Подключается к БД через sync URL (psycopg2)
    - Очищает все таблицы (TRUNCATE RESTART IDENTITY CASCADE)
    - Создает дефолтную локацию (Цех Хуросон) с ID=1
    
    TEAR DOWN фаза:
    - Очищает все таблицы после теста
    
    Это гарантирует, что каждый тест начинает с чистого листа.
    """
    try:
        # ========== SETUP: Очищаем БД перед тестом ==========
        conn = psycopg2.connect(settings.database_url_sync)
        cursor = conn.cursor()

        # Получаем список всех пользовательских таблиц (исключая Alembic)
        cursor.execute(
            """
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' AND tablename NOT LIKE 'alembic%'
        """
        )
        tables = [row[0] for row in cursor.fetchall()]

        if tables:
            # Очищаем все таблицы и сбрасываем их sequense'ы в 1
            # CASCADE гарантирует удаление даже если есть FK constraints
            tables_str = ", ".join(tables)
            cursor.execute(f"TRUNCATE {tables_str} RESTART IDENTITY CASCADE;")

        # Создаем дефолтную фабричную локацию (ID всегда будет равен 1)
        # Это нужно для всех ��стальных тестов, так как они expect location_id=1
        cursor.execute(
            "INSERT INTO wms_locations (name, type) VALUES ('Цех Хуросон', 'FACTORY');"
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"⚠️  Ошибка очистки БД перед тестом: {e}")
        raise  # Пробросим ошибку дальше, так как setup failed

    # ========== YIELD: Здесь выполняются сами тесты ==========
    yield

    # ========== TEAR DOWN: Подчищаем БД после теста ==========
    try:
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
        print(f"⚠️  Ошибка очистки БД после теста: {e}")
        # Не пробрасываем ошибку в tear down, так как тест уже прошел
