import pytest
from httpx import AsyncClient

BASE_URL = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_mes_batch_stages():
    async with AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # Подготовка данных на чистой базе
        mat = (await client.post("/api/v1/materials/", json={"name": "Цемент М500", "unit": "кг"})).json()
        await client.post("/api/v1/materials/transaction", json={"material_id": mat["id"], "location_id": 1, "transaction_type": "INFLOW", "quantity": 1000.0})
        prod = (await client.post("/api/v1/production/products", json={"name": "Шлакоблок", "unit": "шт"})).json()
        await client.post("/api/v1/production/recipes", json={"product_id": prod["id"], "material_id": mat["id"], "quantity_per_unit": 2.0})

        # 1. Запуск формовки партии (MOLDING) на 100 штук (спишет 200 кг цемента)
        batch = await client.post("/api/v1/production/batches", json={"product_id": prod["id"], "location_id": 1, "quantity_molded": 100, "operator_name": "Али"})
        assert batch.json()["status"] == "MOLDING"
        batch_id = batch.json()["id"]

        # 2. Перевод в сушильную камеру (CURING)
        curing = await client.put(f"/api/v1/production/batches/{batch_id}/curing")
        assert curing.json()["status"] == "CURING"

        # 3. Закрытие партии (DONE): Из 100 штук вышло 95 целых и 5 бракованных
        close = await client.put(f"/api/v1/production/batches/{batch_id}/close", json={"quantity_good": 95, "quantity_defective": 5})
        assert close.json()["status"] == "DONE"
        assert close.json()["quantity_good"] == 95

