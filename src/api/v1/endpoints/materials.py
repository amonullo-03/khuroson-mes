from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.database import get_db
from src.modules.wms.models import Material, MaterialTransaction
from src.modules.wms.schemas import (
    MaterialCreate, 
    MaterialResponse, 
    MaterialBalance,
    MaterialTransactionCreate, 
    MaterialTransactionResponse
)
from src.modules.wms.services import get_material_balances_by_location

router = APIRouter()

@router.post("/", response_model=MaterialResponse)
async def create_material(material_in: MaterialCreate, db: AsyncSession = Depends(get_db)):
    """Создать новый вид сырья (с защитой от дубликатов)"""
    stmt = select(Material).where(Material.name == material_in.name)
    existing_mat = await db.scalar(stmt)
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
async def create_transaction(trans_in: MaterialTransactionCreate, db: AsyncSession = Depends(get_db)):
    """Добавить транзакцию сырья с проверкой остатка конкретного склада"""
    if trans_in.transaction_type == "OUTFLOW":
        balances = await get_material_balances_by_location(db, location_id=trans_in.location_id)
        current_balance = next((b.balance for b in balances if b.material_id == trans_in.material_id), 0.0)
        
        if current_balance < trans_in.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недостаточно сырья на складе {trans_in.location_id}. Доступно: {current_balance}, требуется: {trans_in.quantity}"
            )

    new_trans = MaterialTransaction(**trans_in.model_dump())
    db.add(new_trans)
    await db.commit()
    await db.refresh(new_trans)
    return new_trans

@router.get("/balances/{location_id}", response_model=list[MaterialBalance])
async def get_balances(location_id: int, db: AsyncSession = Depends(get_db)):
    """Получить остатки сырья на конкретной локации/складе"""
    return await get_material_balances_by_location(db, location_id=location_id)

