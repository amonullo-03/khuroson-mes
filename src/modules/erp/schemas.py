from datetime import datetime
import enum
from pydantic import BaseModel, ConfigDict, Field, PositiveInt

class OrderStatusEnum(str, enum.Enum):
    CREATED = "CREATED"
    AWAITING = "AWAITING"
    IN_PRODUCTION = "IN_PRODUCTION"
    READY = "READY"
    SHIPPED = "SHIPPED"

class OrderCreate(BaseModel):
    client_name: str = Field(..., max_length=150, description="Имя заказчика или название объекта")
    product_id: int
    quantity_ordered: PositiveInt = Field(..., description="Количество заказываемых изделий")

class OrderResponse(OrderCreate):
    id: int
    status: OrderStatusEnum
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

