from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.api.v1.endpoints import production, materials


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="Backend центр для MES-системы цеха в Хуросоне"
)

# Настройка CORS (чтобы в будущем планшеты и веб-панели могли спокойно слать запросы)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Для MVP разрешаем доступ отовсюду
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "message": "Привет из Хуросона! Бэкенд работает исправно."
    }


# <-- ДОБАВИЛИ РЕГИСТРАЦИЮ РОУТЕРА -->
app.include_router(production.router, prefix="/api/v1/production", tags=["Производство"])
app.include_router(materials.router, prefix="/api/v1/materials", tags=["Материалы - Склад"])
