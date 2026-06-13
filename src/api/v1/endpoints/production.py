from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.database import get_db
from src.modules.mes.models import Product
from src.modules.mes.schemas import ProductCreate, ProductResponse
from src.modules.mes.schemas import (
    RecipeCreate, RecipeResponse,
    ProductionBatchCreate, ProductionBatchResponse,
    BatchCloseRequest
)
from src.modules.mes.models import ProductRecipe
from src.modules.mes.services import start_production_batch, move_batch_to_curing, close_production_batch

router = APIRouter()

@router.post("/products", response_model=ProductResponse)
async def create_product(product_in: ProductCreate, db: AsyncSession = Depends(get_db)):
    """Создать вид готовой продукции"""
    new_product = Product(name=product_in.name, unit=product_in.unit)
    db.add(new_product)
    try:
        await db.commit()
        await db.refresh(new_product)
        return new_product
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Продукт с таким названием уже существует!")

@router.post("/recipes", response_model=RecipeResponse)
async def create_recipe(recipe_in: RecipeCreate, db: AsyncSession = Depends(get_db)):
    """Создать уникальный рецепт"""
    stmt = select(ProductRecipe).where(
        ProductRecipe.product_id == recipe_in.product_id,
        ProductRecipe.material_id == recipe_in.material_id
    )
    existing = await db.scalar(stmt)
    if existing:
        raise HTTPException(status_code=400, detail="Рецепт для этой пары уже задан!")
        
    new_recipe = ProductRecipe(**recipe_in.model_dump())
    db.add(new_recipe)
    await db.commit()
    await db.refresh(new_recipe)
    return new_recipe

@router.post("/batches", response_model=ProductionBatchResponse)
async def create_batch(batch_in: ProductionBatchCreate, db: AsyncSession = Depends(get_db)):
    """Запуск формовки производственной партии со списанием сырья"""
    return await start_production_batch(batch_in, db)

@router.put("/batches/{batch_id}/curing", response_model=ProductionBatchResponse)
async def send_to_curing(batch_id: int, db: AsyncSession = Depends(get_db)):
    """Отправить партию в камеру сушки"""
    return await move_batch_to_curing(batch_id, db)

@router.put("/batches/{batch_id}/close", response_model=ProductionBatchResponse)
async def close_batch(batch_id: int, req: BatchCloseRequest, db: AsyncSession = Depends(get_db)):
    """Приемка из сушки: фиксация годных блоков и объема брака"""
    return await close_production_batch(batch_id, req, db)

