import pytest
from httpx import AsyncClient

BASE_URL = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_erp_order_dependencies():
    async with AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # Подготовка: создаем продукт и цемент
        mat = (await client.post("/api/v1/materials/", json={"name": "Цемент М500", "unit": "кг"})).json()
        prod = (await client.post("/api/v1/production/products", json={"name": "Шлакоблок", "unit": "шт"})).json()
        
        # Создаем рецепт (2.5 кг на 1 шт)
        await client.post("/api/v1/production/recipes", json={"product_id": prod["id"], "material_id": mat["id"], "quantity_per_unit": 2.5})

        # Тест №1: Создаем заказ БЕЗ сырья на складе. Статус должен стать AWAITING (Ожидание)
        order1 = await client.post("/api/v1/orders/", json={"client_name": "Тест Клиент", "product_id": prod["id"], "quantity_ordered": 100})
        assert order1.json()["status"] == "AWAITING"

        # Тест №2: Завозим сырье с запасом
        await client.post("/api/v1/materials/transaction", json={"material_id": mat["id"], "location_id": 1, "transaction_type": "INFLOW", "quantity": 5000.0})

        # Тест №3: Создаем новый заказ С сырьем. Статус должен автоматически стать IN_PRODUCTION
        order2 = await client.post("/api/v1/orders/", json={"client_name": "Тест Клиент 2", "product_id": prod["id"], "quantity_ordered": 100})
        assert order2.json()["status"] == "IN_PRODUCTION"

