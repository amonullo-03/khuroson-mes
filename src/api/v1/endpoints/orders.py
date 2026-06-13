from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.modules.erp.schemas import OrderCreate, OrderResponse
from src.modules.erp.services import create_client_order

router = APIRouter()

@router.post("/", response_model=OrderResponse)
async def place_order(order_in: OrderCreate, db: AsyncSession = Depends(get_db)):
    """
    Принять новый заказ от клиента (с автоматическим расчетом дефицита сырья)
    """
    return await create_client_order(order_in, db)

