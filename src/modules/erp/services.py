from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.modules.erp.models import Order, OrderStatus, FinishedGoodsInventory, Waybill
from src.modules.erp.schemas import OrderCreate, WaybillCreate
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


async def ship_order_part(waybill_in: WaybillCreate, db: AsyncSession):
    """
    Проведение отгрузки: проверка остатков шлакоблоков на складе ГП,
    создание ТТН и автоматическое обновление статуса заказа.
    """
    # 1. Ищем заказ
    order = await db.scalar(select(Order).where(Order.id == waybill_in.order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    # 2. Проверяем склад готовой продукции
    inventory = await db.scalar(
        select(FinishedGoodsInventory).where(FinishedGoodsInventory.product_id == order.product_id)
    )
    if not inventory or inventory.quantity_available < waybill_in.quantity_shipped:
        available = inventory.quantity_available if inventory else 0
        raise HTTPException(
            status_code=400,
            detail=f"Недостаточно готовой продукции на складе ГП. Доступно: {available}, требуется: {waybill_in.quantity_shipped}"
        )

    # 3. Считаем, сколько БЫЛО отгружено по этому заказу ДО текущей машины
    previous_shipped_result = await db.execute(
        select(func.coalesce(func.sum(Waybill.quantity_shipped), 0)).where(Waybill.order_id == order.id)
    )
    previously_shipped = previous_shipped_result.scalar() or 0

    # 4. Списываем блоки со склада ГП
    inventory.quantity_available -= waybill_in.quantity_shipped

    # 5. Создаем ТТН
    new_waybill = Waybill(**waybill_in.model_dump())
    db.add(new_waybill)

    # 6. Обновляем статус заказа: прибавляем к старым отгрузкам текущую
    if (previously_shipped + waybill_in.quantity_shipped) >= order.quantity_ordered:
        order.status = OrderStatus.SHIPPED

    await db.commit()
    await db.refresh(new_waybill)
    return new_waybill



async def add_finished_goods_to_inventory(product_id: int, quantity: int, db: AsyncSession):
    """
    Изолированный сервис: оприходование готовой продукции на склад ГП.
    """
    stmt = select(FinishedGoodsInventory).where(FinishedGoodsInventory.product_id == product_id)
    inv = await db.scalar(stmt)
    
    if not inv:
        inv = FinishedGoodsInventory(product_id=product_id, quantity_available=quantity)
        db.add(inv)
    else:
        inv.quantity_available += quantity
    
    # Мы НЕ делаем здесь db.commit(), так как эта функция — часть большой транзакции цеха!

