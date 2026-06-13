#!/bin/bash

# Адрес вашего локального сервера
BASE_URL="http://127.0.0.1:8000"

echo "=== Шаг 1: Создание материала ==="
curl -X POST "$BASE_URL/api/v1/materials/" \
     -H "Content-Type: application/json" \
     -d '{"name": "Цемент М500", "unit": "кг"}'
echo -e "\n\n"

echo "=== Шаг 2: Поставка сырья на склад (500 кг) ==="
curl -X POST "$BASE_URL/api/v1/materials/transaction" \
     -H "Content-Type: application/json" \
     -d '{"material_id": 1, "transaction_type": "INFLOW", "quantity": 2500}'
echo -e "\n\n"

echo "=== Шаг 3: Создание рецепта (2.5 кг на 1 шт) ==="
curl -X POST "$BASE_URL/api/v1/production/recipes" \
     -H "Content-Type: application/json" \
     -d '{"product_id": 1, "material_id": 1, "quantity_per_unit": 2.5}'
echo -e "\n\n"

echo "=== Шаг 4: Успешное производство (100 шт -> спишет 250 кг) ==="
curl -X POST "$BASE_URL/api/v1/production/log" \
     -H "Content-Type: application/json" \
     -d '{"product_id": 1, "quantity_produced": 100}'
echo -e "\n\n"

echo "=== Шаг 5: Проверка ошибки 400 (Попытка произвести 300 шт -> нужно 750 кг, осталось 250) ==="
curl -X POST "$BASE_URL/api/v1/production/log" \
     -H "Content-Type: application/json" \
     -d '{"product_id": 1, "quantity_produced": 300}'
echo -e "\n"

