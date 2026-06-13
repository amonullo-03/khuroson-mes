from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.database import get_db
from src.models.materials import Material, MaterialTransaction
from src.schemas.materials import (
    MaterialCreate, 
    MaterialResponse, 
    MaterialBalance,
    MaterialTransactionCreate, 
    MaterialTransactionResponse
)
# Переключаемся на ваш новый целевой сервис склада
from src.services.warehouse import get_all_material_balances

router = APIRouter()

@router.post("/", response_model=MaterialResponse)
async def create_material(
    material_in: MaterialCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Создать новый вид сырья (с защитой от дубликатов по имени)
    """
    # Проверяем, нет ли уже сырья с таким именем
    stmt = select(Material).where(Material.name == material_in.name)
    result = await db.execute(stmt)
    existing_mat = result.scalar_one_or_none()
    
    if existing_mat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Материал с названием '{material_in.name}' уже существует."
        )

    new_mat = Material(name=material_in.name, unit=material_in.unit)
    db.add(new_mat)
    await db.commit()
    await db.refresh(new_mat)
    return new_mat


@router.post("/transaction", response_model=MaterialTransactionResponse)
async def create_transaction(
    trans_in: MaterialTransactionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Добавить приход или расход материала (INFLOW / OUTFLOW)
    с проверкой остатка, чтобы склад не уходил в минус
    """
    # Если это списание, проверяем реальный остаток на складе
    if trans_in.transaction_type == "OUTFLOW":
        balances = await get_all_material_balances(db)
        current_balance = next((b.balance for b in balances if b.material_id == trans_in.material_id), 0.0)
        
        if current_balance < trans_in.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недостаточно сырья на складе. Доступно: {current_balance}, требуется: {trans_in.quantity}"
            )

    new_trans = MaterialTransaction(**trans_in.model_dump())
    db.add(new_trans)
    await db.commit()
    await db.refresh(new_trans)
    return new_trans


@router.get("/balances", response_model=list[MaterialBalance])
async def get_all_balances(db: AsyncSession = Depends(get_db)):
    """
    Получить текущие остатки сырья на складе (вызов сервисного слоя)
    """
    return await get_all_material_balances(db)

