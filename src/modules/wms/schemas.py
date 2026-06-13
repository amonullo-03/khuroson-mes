from datetime import datetime
from typing import Optional
import enum
from pydantic import BaseModel, ConfigDict, Field, PositiveFloat

# Нам нужен enum для валидации типа транзакции в схемах
class TransactionTypeEnum(str, enum.Enum):
    INFLOW = "INFLOW"
    OUTFLOW = "OUTFLOW"

# --- СХЕМЫ ДЛЯ ЛОКАЦИЙ (СКЛАДОВ) ---
class LocationBase(BaseModel):
    name: str = Field(..., max_length=100, description="Название склада/цеха")
    type: str = Field("FACTORY", max_length=50, description="Тип точки: FACTORY, WAREHOUSE, CLIENT_SITE")

class LocationCreate(LocationBase):
    pass

class LocationResponse(LocationBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- СХЕМЫ ДЛЯ МАТЕРИАЛА ---
class MaterialBase(BaseModel):
    name: str = Field(..., max_length=100, description="Название сырья")
    unit: str = Field(..., max_length=20, description="Единица измерения")

class MaterialCreate(MaterialBase):
    pass

class MaterialResponse(MaterialBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class MaterialBalance(BaseModel):
    material_id: int
    name: str
    unit: str
    balance: float

# --- СХЕМЫ ДЛЯ ТРАНЗАКЦИЙ СЫРЬЯ ---
class MaterialTransactionBase(BaseModel):
    material_id: int
    location_id: int  # Добавили обязательный ID склада
    transaction_type: TransactionTypeEnum
    quantity: PositiveFloat = Field(..., description="Количество сырья (строго положительное)")
    comment: Optional[str] = Field(None, max_length=255)

class MaterialTransactionCreate(MaterialTransactionBase):
    pass

class MaterialTransactionResponse(MaterialTransactionBase):
    id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

