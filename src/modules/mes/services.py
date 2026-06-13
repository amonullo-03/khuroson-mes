from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.modules.mes.models import Product, ProductRecipe, ProductionBatch, BatchStatus
from src.modules.wms.models import MaterialTransaction, TransactionType
from src.modules.mes.schemas import ProductionBatchCreate, BatchCloseRequest
from src.modules.wms.services import get_material_balances_by_location

async def start_production_batch(batch_in: ProductionBatchCreate, db: AsyncSession):
    """
    Запуск формовки партии: проверка рецепта, контроль остатков на складе сырья
    и автоматическое точечное списание компонентов.
    """
    # 1. Проверяем продукт
    product = await db.scalar(select(Product).where(Product.id == batch_in.product_id))
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден")

    # 2. Получаем уникальные рецепты для продукта
    recipes_result = await db.scalars(select(ProductRecipe).where(ProductRecipe.product_id == batch_in.product_id))
    recipes = recipes_result.all()
    if not recipes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Для данного продукта не задана рецептура. Выпуск невозможен."
        )

    # 3. Контролируем остатки на конкретном складе сырья
    balances = await get_material_balances_by_location(db, location_id=batch_in.location_id)
    balance_dict = {b.material_id: b.balance for b in balances}

    for recipe in recipes:
        total_needed = recipe.quantity_per_unit * batch_in.quantity_molded
        current_stock = balance_dict.get(recipe.material_id, 0.0)
        
        if current_stock < total_needed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недостаточно сырья (ID: {recipe.material_id}) на складе {batch_in.location_id}. Надо: {total_needed}, есть: {current_stock}"
            )

    # 4. Проводим транзакции списания сырья в модуле WMS
    for recipe in recipes:
        total_needed = recipe.quantity_per_unit * batch_in.quantity_molded
        deduction = MaterialTransaction(
            material_id=recipe.material_id,
            location_id=batch_in.location_id,
            transaction_type=TransactionType.OUTFLOW,
            quantity=total_needed,
            comment=f"Списание на замес партии (Продукт ID: {product.id}, Отформовано: {batch_in.quantity_molded})"
        )
        db.add(deduction)

    # 5. Создаем новую производственную партию со статусом MOLDING (Формовка)
    new_batch = ProductionBatch(
        product_id=batch_in.product_id,
        location_id=batch_in.location_id,
        order_id=batch_in.order_id,
        quantity_molded=batch_in.quantity_molded,
        status=BatchStatus.MOLDING,
        operator_name=batch_in.operator_name
    )
    db.add(new_batch)
    
    await db.commit()
    await db.refresh(new_batch)
    return new_batch


async def move_batch_to_curing(batch_id: int, db: AsyncSession):
    """Перевод партии в камеру сушки (пропарку)"""
    batch = await db.scalar(select(ProductionBatch).where(ProductionBatch.id == batch_id))
    if not batch:
        raise HTTPException(status_code=404, detail="Партия не найдена")
    
    batch.status = BatchStatus.CURING
    await db.commit()
    await db.refresh(batch)
    return batch


async def close_production_batch(batch_id: int, req: BatchCloseRequest, db: AsyncSession):
    """
    Выход из сушки: фиксация годных блоков, объема брака 
    и перевод в финальный статус DONE.
    """
    batch = await db.scalar(select(ProductionBatch).where(ProductionBatch.id == batch_id))
    if not batch:
        raise HTTPException(status_code=404, detail="Партия не найдена")

    if batch.quantity_molded != (req.quantity_good + req.quantity_defective):
        raise HTTPException(
            status_code=400, 
            detail=f"Сумма годных ({req.quantity_good}) и бракованных ({req.quantity_defective}) изделий должна быть равна изначально отформованному количеству ({batch.quantity_molded})!"
        )

    batch.quantity_good = req.quantity_good
    batch.quantity_defective = req.quantity_defective
    batch.status = BatchStatus.DONE
    
    await db.commit()
    await db.refresh(batch)
    return batch

