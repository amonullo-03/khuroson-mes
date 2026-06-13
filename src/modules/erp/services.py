from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.modules.erp.models import Order, OrderStatus
from src.modules.erp.schemas import OrderCreate
from src.modules.mes.models import Product, ProductRecipe
from src.modules.wms.services import get_material_balances_by_location

async def create_client_order(order_in: OrderCreate, db: AsyncSession):
    """
    Прием заказа клиента с автоматической проверкой сырья 
    и резервированием статуса производства.
    """
    # 1. Проверяем, существует ли заказываемый продукт
    product = await db.scalar(select(Product).where(Product.id == order_in.product_id))
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден")

    # 2. Ищем рецепт для этого продукта
    recipes_result = await db.scalars(select(ProductRecipe).where(ProductRecipe.product_id == order_in.product_id))
    recipes = recipes_result.all()
    
    # По умолчанию считаем, что сырья хватит
    initial_status = OrderStatus.IN_PRODUCTION

    if recipes:
        # 3. Допустим, производство идет на главной локации ID: 1 (Цех Хуросон)
        MAIN_LOCATION_ID = 1
        balances = await get_material_balances_by_location(db, location_id=MAIN_LOCATION_ID)
        balance_dict = {b.material_id: b.balance for b in balances}

        # Проверяем, нет ли дефицита хотя бы по одному компоненту
        for recipe in recipes:
            total_needed = recipe.quantity_per_unit * order_in.quantity_ordered
            current_stock = balance_dict.get(recipe.material_id, 0.0)
            
            if current_stock < total_needed:
                # Если сырья не хватает — заказ падает в ожидание закупки сырья
                initial_status = OrderStatus.AWAITING_MATERIALS
                break

    # 4. Создаем заказ в базе данных ERP
    new_order = Order(
        client_name=order_in.client_name,
        product_id=order_in.product_id,
        quantity_ordered=order_in.quantity_ordered,
        status=initial_status
    )
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)
    return new_order

