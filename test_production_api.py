import pytest
from httpx import AsyncClient

# URL вашего запущенного локально FastAPI сервера
BASE_URL = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_mes_production_workflow():
    async with AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        print("\n Запуск интеграционного теста MES системы...")

        # 1. СОЗДАЕМ МАТЕРИАЛ (Цемент М500)
        mat_res = await client.post("/api/v1/materials/", json={
            "name": "Цемент М500",
            "unit": "кг"
        })
        assert mat_res.status_code == 200, f"Не удалось создать материал: {mat_res.text}"
        material_id = mat_res.json()["id"]
        print(f" -> [OK] Материал создан с ID: {material_id}")

        # 2. ПОПОЛНЯЕМ СКЛАД (INFLOW) — Завезем 2000 кг цемента
        trans_res = await client.post("/api/v1/materials/transaction", json={
            "material_id": material_id,
            "transaction_type": "INFLOW",
            "quantity": 2000.0,
            "comment": "Поставка цемента на склад"
        })
        assert trans_res.status_code == 200
        print(" -> [OK] На склад успешно оприходовано 2000 кг цемента.")

        # 3. СОЗДАЕМ ПРОДУКТ (Шлакоблок)
        prod_res = await client.post("/api/v1/production/products", json={
            "name": "Шлакоблок 19х19х39",
            "unit": "шт"
        })
        assert prod_res.status_code == 200, f"Не удалось создать продукт: {prod_res.text}"
        product_id = prod_res.json()["id"]
        print(f" -> [OK] Продукт создан с ID: {product_id}")

        # 4. СОЗДАЕМ РЕЦЕПТ (2.5 кг цемента на 1 шлакоблок)
        recipe_res = await client.post("/api/v1/production/recipes", json={
            "product_id": product_id,
            "material_id": material_id,
            "quantity_per_unit": 2.5
        })
        assert recipe_res.status_code == 200
        print(" -> [OK] Рецепт успешно добавлен в систему (2.5 кг/ед).")

        # 5. ТЕСТ ЗАЩИТЫ ОТ ДУБЛИКАТОВ: Пробуем создать ТОЧНО ТАКОЙ ЖЕ рецепт еще раз
        dup_recipe_res = await client.post("/api/v1/production/recipes", json={
            "product_id": product_id,
            "material_id": material_id,
            "quantity_per_unit": 2.5
        })
        # Система должна выдать 400 Bad Request, защищая базу данных
        assert dup_recipe_res.status_code == 400
        print(" -> [ЗАЩИТА СРАБОТАЛА] Повторное создание рецепта заблокировано API (400 Bad Request)!")

        # 6. ФИКСИРУЕМ ВЫПУСК ПРОДУКЦИИ (Выпустим 100 шлакоблоков)
        # Ожидаемый расход сырья: 100 * 2.5 = 250 кг цемента
        log_res = await client.post("/api/v1/production/log", json={
            "product_id": product_id,
            "quantity_produced": 100,
            "quantity_defective": 0,
            "operator_name": "Тестовый оператор"
        })
        assert log_res.status_code == 200, f"Ошибка фиксации выпуска: {log_res.text}"
        print(" -> [OK] Зафиксирован выпуск 100 единиц шлакоблока.")

        # 7. ПРОВЕРЯЕМ ОСТАТКИ НА СКЛАДЕ ПОСЛЕ ВЫПУСКА через /balances
        # Было 2000 кг, списалось 250 кг, должно остаться строго 1750 кг
        balance_res = await client.get("/api/v1/materials/balances")
        assert balance_res.status_code == 200
        
        balances = balance_res.json()
        cement_balance = next((b for b in balances if b["material_id"] == material_id), None)
        
        assert cement_balance is not None, "Баланс для цемента не найден в ответе"
        assert cement_balance["balance"] == 1750.0, f"Неверное списание! Остаток: {cement_balance['balance']}, а ожидали 1750.0"
        
        print(f" -> [ФИНАЛЬНЫЙ ТЕСТ ПРОЙДЕН] Баланс склада сошелся идеально! Реальный остаток: {cement_balance['balance']} кг.")
        print("\n Все защитные механизмы MES-системы работают бездефектно!")

