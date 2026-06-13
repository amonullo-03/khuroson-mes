from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.erp.schemas import OrderCreate, OrderResponse, WaybillCreate, WaybillResponse
from src.modules.erp.services import create_client_order, ship_order_part

router = APIRouter()

@router.post("/", response_model=OrderResponse)
async def place_order(order_in: OrderCreate, db: AsyncSession = Depends(get_db)):
    """
    Принять новый заказ от клиента (с автоматическим расчетом дефицита сырья)
    """
    return await create_client_order(order_in, db)


@router.post("/shipments", response_model=WaybillResponse)
async def create_waybill(waybill_in: WaybillCreate, db: AsyncSession = Depends(get_db)):
    """
    Оформить товарно-транспортную накладную (ТТН) и отгрузить готовую продукцию со склада ГП
    """
    return await ship_order_part(waybill_in, db)

