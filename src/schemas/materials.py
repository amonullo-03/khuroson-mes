# src/schemas/materials.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, PositiveFloat
from src.models.materials import TransactionType

# --- СХЕМЫ ДЛЯ МАТЕРИАЛА ---
class MaterialBase(BaseModel):
    name: str = Field(..., max_length=100, description="Название сырья", examples=["Цемент М500"])
    unit: str = Field(..., max_length=20, description="Единица измерения", examples=["кг"])

class MaterialCreate(MaterialBase):
    pass  # Используется при создании нового материала (вход)

class MaterialResponse(MaterialBase):
    id: int

    # В Pydantic v2 вместо orm_mode = True используется ConfigDict
    model_config = ConfigDict(from_attributes=True)

class MaterialBalance(BaseModel):
    material_id: int
    name: str
    unit: str
    balance: float

# --- СХЕМЫ ДЛЯ ТРАНЗАКЦИЙ СЫРЬЯ ---
class MaterialTransactionBase(BaseModel):
    material_id: int
    transaction_type: TransactionType
    quantity: PositiveFloat = Field(..., description="Количество сырья (строго больше 0)")
    comment: Optional[str] = Field(None, max_length=255)

class MaterialTransactionCreate(MaterialTransactionBase):
    pass  # Используется при фиксации прихода/расхода (вход)

class MaterialTransactionResponse(MaterialTransactionBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
