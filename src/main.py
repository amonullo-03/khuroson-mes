from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
# Импортируем наш единый новый роутер, который объединяет все 3 модуля
from src.api.v1.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",  # Поднимаем версию до модульной архитектуры!
    description="Backend центр для модульной ERP/MES/WMS экосистемы T-Link"
)

# Ваша проверенная настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Системные"])
async def root():
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "message": "Привет из Хуросона! Бэкенд экосистемы T-Link работает исправно."
    }

# Регистрируем единый роутер, в котором уже упакованы /production, /materials и /orders
app.include_router(api_router, prefix="/api/v1")

