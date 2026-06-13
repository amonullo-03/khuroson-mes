import pytest
import pytest_asyncio
import psycopg2

DB_CONN_STR = "dbname=khuroson_mes user=mes_user password=your_password host=localhost port=5432"

@pytest_asyncio.fixture(autouse=True, scope="function")
async def clean_database():
    """
    Автоматическая очистка СУБД перед каждым тестом и после него.
    Сбрасывает все ID в 1 для гарантированной изоляции.
    """
    # SETUP: Очищаем базу перед запуском теста
    conn = psycopg2.connect(DB_CONN_STR)
    cursor = conn.cursor()
    cursor.execute("""
        TRUNCATE wms_materials, mes_products, mes_production_batches, 
                 erp_orders, wms_material_transactions, wms_locations, mes_product_recipes
        RESTART IDENTITY CASCADE;
    """)
    # Создаем дефолтную фабричную локацию (ID всегда будет равен 1)
    cursor.execute("INSERT INTO wms_locations (name, type) VALUES ('Цех Хуросон', 'FACTORY');")
    conn.commit()
    cursor.close()
    conn.close()

    yield # Здесь выполняются сами тесты

    # TEARDOWN: Подчищаем базу за собой после теста
    conn = psycopg2.connect(DB_CONN_STR)
    cursor = conn.cursor()
    cursor.execute("""
        TRUNCATE wms_materials, mes_products, mes_production_batches, 
                 erp_orders, wms_material_transactions, wms_locations, mes_product_recipes
        RESTART IDENTITY CASCADE;
    """)
    conn.commit()
    cursor.close()
    conn.close()

