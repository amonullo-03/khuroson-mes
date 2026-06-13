from fastapi import APIRouter
from src.api.v1.endpoints.materials import router as materials_router
from src.api.v1.endpoints.production import router as production_router
# Импортируем роутер заказов, который создадим через минуту
from src.api.v1.endpoints.orders import router as orders_router

api_router = APIRouter()

# Объединяем ручки с красивыми тегами для Swagger docs
api_router.include_router(materials_router, prefix="/materials", tags=["WMS - Склад сырья"])
api_router.include_router(production_router, prefix="/production", tags=["MES - Производство"])
api_router.include_router(orders_router, prefix="/orders", tags=["ERP - Заказы клиентов"])

