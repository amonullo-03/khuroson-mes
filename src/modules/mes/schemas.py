from datetime import datetime
from typing import Optional
import enum
from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt, PositiveFloat

class BatchStatusEnum(str, enum.Enum):
    MOLDING = "MOLDING"
    CURING = "CURING"
    MATURING = "MATURING"
    DONE = "DONE"

# --- СХЕМЫ ДЛЯ ПРОДУКТА ---
class ProductBase(BaseModel):
    name: str = Field(..., max_length=150, description="Название готового изделия")
    unit: str = Field("шт", max_length=20)

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- СХЕМЫ ДЛЯ РЕЦЕПТОВ ---
class RecipeCreate(BaseModel):
    product_id: int
    material_id: int
    quantity_per_unit: PositiveFloat = Field(..., description="Расход сырья на 1 единицу готовой продукции")

class RecipeResponse(RecipeCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- СХЕМЫ ДЛЯ ПРОИЗВОДСТВЕННЫХ ПАРТИЙ (ВМЕСТО СТАРЫХ ЛОГОВ) ---
class ProductionBatchCreate(BaseModel):
    product_id: int
    location_id: int  # На каком складе/цеху запускаем замес
    order_id: Optional[int] = Field(None, description="ID заказа из ERP, если делаем под заказ")
    quantity_molded: NonNegativeInt = Field(..., description="Сколько штук отформовано изначально")
    operator_name: Optional[str] = Field(None, max_length=100)

class ProductionBatchResponse(ProductionBatchCreate):
    id: int
    quantity_good: int
    quantity_defective: int
    status: BatchStatusEnum
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Схема для фиксации итогов сушки и брака (перевод в статус DONE)
class BatchCloseRequest(BaseModel):
    quantity_good: NonNegativeInt = Field(..., description="Сколько блоков успешно вышло из сушки")
    quantity_defective: NonNegativeInt = Field(..., description="Сколько блоков ушло в брак")

