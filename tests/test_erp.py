import pytest
from httpx import AsyncClient

BASE_URL = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_erp_order_and_shipment_lifecycle():
    async with AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # --- ПОДГОТОВКА СУЩНОСТЕЙ ---
        mat = (await client.post("/api/v1/materials/", json={"name": "Цемент М500", "unit": "кг"})).json()
        await client.post("/api/v1/materials/transaction", json={
            "material_id": mat["id"], "location_id": 1, "transaction_type": "INFLOW", "quantity": 5000.0
        })
        prod = (await client.post("/api/v1/production/products", json={"name": "Шлакоблок 19х19х39", "unit": "шт"})).json()
        await client.post("/api/v1/production/recipes", json={
            "product_id": prod["id"], "material_id": mat["id"], "quantity_per_unit": 2.5
        })

        # 1. Принимаем заказ от клиента на 500 штук
        order = (await client.post("/api/v1/orders/", json={
            "client_name": "ООО Душанбе-Сити", "product_id": prod["id"], "quantity_ordered": 500
        })).json()
        assert order["status"] == "IN_PRODUCTION"
        order_id = order["id"]

        # 2. MES формует партию под этот заказ
        batch = (await client.post("/api/v1/production/batches", json={
            "product_id": prod["id"], "location_id": 1, "order_id": order_id, "quantity_molded": 500, "operator_name": "Даврон"
        })).json()
        batch_id = batch["id"]

        # 3. Переводим в сушку и закрываем (ОТК принимает 480 блоков, 20 в брак)
        await client.put(f"/api/v1/production/batches/{batch_id}/curing")
        await client.put(f"/api/v1/production/batches/{batch_id}/close", json={
            "quantity_good": 480, "quantity_defective": 20
        })

        # 4. ТЕСТ ОТГРУЗКИ ПО ТТН (Менеджер грузит манипулятор на объект клиента)
        # Отгрузим первую партию из 300 штук
        shipment = await client.post("/api/v1/orders/shipments", json={
            "order_id": order_id,
            "driver_name": "Хуршед",
            "truck_number": "01TJ777",
            "quantity_shipped": 300
        })
        assert shipment.status_code == 200
        print(" -> [ТТН] Первая машина на 300 штук успешно оформлена!")

        # 5. ТЕСТ ЗАЩИТЫ СКЛАДА ГП: Пробуем отгрузить больше, чем есть на остатке
        # На складе ГП осталось: 480 - 300 = 180 штук. Пробуем увести склад в минус, погрузив 200 штук.
        over_shipment = await client.post("/api/v1/orders/shipments", json={
            "order_id": order_id,
            "driver_name": "Хуршед",
            "truck_number": "01TJ777",
            "quantity_shipped": 200
        })
        assert over_shipment.status_code == 400
        print(" -> [WMS ГП Защита] Попытка увести склад готовой продукции в минус успешно заблокирована!")

