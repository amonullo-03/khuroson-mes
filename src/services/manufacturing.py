# src/services/manufacturing.py
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.production import Product, ProductionLog, ProductRecipe
from src.models.materials import MaterialTransaction, TransactionType
from src.schemas.production import ProductionLogCreate, RecipeCreate
from src.services.warehouse import get_all_material_balances

async def create_new_recipe(recipe_in: RecipeCreate, db: AsyncSession):
    """Бизнес-логика проверки и создания рецепта"""
    stmt = select(ProductRecipe).where(
        ProductRecipe.product_id == recipe_in.product_id,
        ProductRecipe.material_id == recipe_in.material_id
    )
    existing = await db.scalar(stmt)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Рецепт для этой пары продукт-материал уже существует!"
        )
    
    new_recipe = ProductRecipe(**recipe_in.model_dump())
    db.add(new_recipe)
    await db.commit()
    await db.refresh(new_recipe)
    return new_recipe


async def process_production_release(log_in: ProductionLogCreate, db: AsyncSession):
    """
    Главная бизнес-логика: проверка существования, контроль остатков 
    и атомарное проведение выпуска со списанием сырья.
    """
    # 1. Проверяем продукт
    product = await db.scalar(select(Product).where(Product.id == log_in.product_id))
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден")

    # 2. Получаем рецепты
    recipes_result = await db.scalars(select(ProductRecipe).where(ProductRecipe.product_id == log_in.product_id))
    recipes = recipes_result.all()
    if not recipes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Для данного продукта не задана рецептура. Выпуск невозможен."
        )

    # 3. Контроль остатков склада
    balances = await get_all_material_balances(db)
    balance_dict = {b.material_id: b.balance for b in balances}

    for recipe in recipes:
        total_needed = recipe.quantity_per_unit * log_in.quantity_produced
        current_stock = balance_dict.get(recipe.material_id, 0.0)
        
        if current_stock < total_needed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недостаточно сырья (ID: {recipe.material_id}) на складе. Надо: {total_needed}, есть: {current_stock}"
            )

    # 4. Проведение транзакций списания сырья
    for recipe in recipes:
        total_needed = recipe.quantity_per_unit * log_in.quantity_produced
        deduction = MaterialTransaction(
            material_id=recipe.material_id,
            transaction_type=TransactionType.OUTFLOW,
            quantity=total_needed,
            comment=f"Списание на производство (Продукт ID: {product.id}, Выпущено: {log_in.quantity_produced})"
        )
        db.add(deduction)

    # 5. Логирование самого выпуска готовой продукции
    new_log = ProductionLog(
        product_id=log_in.product_id,
        quantity_produced=log_in.quantity_produced,
        quantity_defective=log_in.quantity_defective,
        operator_name=log_in.operator_name
    )
    db.add(new_log)

    # Атомарный коммит: спишется либо всё вместе, либо ничего!
    await db.commit()
    await db.refresh(new_log)
    return new_log

