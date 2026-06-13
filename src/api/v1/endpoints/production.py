from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.database import get_db
from src.models.production import Product
from src.schemas.production import (
    ProductCreate, ProductResponse, 
    ProductionLogCreate, ProductionLogResponse,
    RecipeCreate, RecipeResponse
)
# Импортируем наши новые сервисы
from src.services.manufacturing import process_production_release, create_new_recipe

router = APIRouter()

@router.post("/products", response_model=ProductResponse)
async def create_product(product_in: ProductCreate, db: AsyncSession = Depends(get_db)):
    new_product = Product(name=product_in.name, unit=product_in.unit)
    db.add(new_product)
    try:
        await db.commit()
        await db.refresh(new_product)
        return new_product
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Продукт с таким названием уже существует!"
        )

@router.post("/recipes", response_model=RecipeResponse)
async def create_recipe(recipe_in: RecipeCreate, db: AsyncSession = Depends(get_db)):
    """Вызов сервиса создания рецептур"""
    return await create_new_recipe(recipe_in, db)

@router.post("/log", response_model=ProductionLogResponse)
async def create_production_log(log_in: ProductionLogCreate, db: AsyncSession = Depends(get_db)):
    """Вызов сервиса проведения смены/выпуска"""
    return await process_production_release(log_in, db)

