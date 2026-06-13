# src/schemas/production.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt

# --- СХЕМЫ ДЛЯ ПРОДУКТА ---
class ProductBase(BaseModel):
    name: str = Field(..., max_length=150, description="Название готового изделия", examples=["Шлакоблок 19х19х39"])
    unit: str = Field("шт", max_length=20)

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# --- СХЕМЫ ДЛЯ ЛОГОВ ВЫПУСКА ---
class ProductionLogBase(BaseModel):
    product_id: int
    quantity_produced: NonNegativeInt = Field(..., description="Количество качественной продукции")
    quantity_defective: NonNegativeInt = Field(0, description="Количество брака")
    operator_name: Optional[str] = Field(None, max_length=100, description="Имя мастера смены")

class ProductionLogCreate(ProductionLogBase):
    pass  

class ProductionLogResponse(ProductionLogBase):
    id: int
    timestamp: datetime  

    model_config = ConfigDict(from_attributes=True)


class RecipeCreate(BaseModel):
    product_id: int
    material_id: int
    quantity_per_unit: float = Field(..., gt=0, description="Расход сырья на 1 ед. продукта")

class RecipeResponse(RecipeCreate):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

