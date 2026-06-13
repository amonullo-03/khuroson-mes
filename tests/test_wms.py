import pytest
from httpx import AsyncClient

BASE_URL = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_wms_material_lifecycle():
    async with AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Создание материала
        res = await client.post("/api/v1/materials/", json={"name": "Цемент М500", "unit": "кг"})
        assert res.status_code == 200
        mat_id = res.json()["id"]

        # 2. Проверка защиты от дубликатов
        dup_res = await client.post("/api/v1/materials/", json={"name": "Цемент М500", "unit": "кг"})
        assert dup_res.status_code == 400

        # 3. Оприходование сырья (INFLOW) на локацию 1
        trans = await client.post("/api/v1/materials/transaction", json={
            "material_id": mat_id, "location_id": 1, "transaction_type": "INFLOW", "quantity": 1000.0, "comment": "Тест"
        })
        assert trans.status_code == 200

        # 4. Проверка остатка
        bal = await client.get("/api/v1/materials/balances/1")
        assert bal.json()[0]["balance"] == 1000.0

