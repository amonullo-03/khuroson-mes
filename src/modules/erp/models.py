from datetime import datetime
import enum
from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base

class OrderStatus(str, enum.Enum):
    CREATED = "CREATED"                 # Заказ принят менеджером
    AWAITING_MATERIALS = "AWAITING"     # Не хватает сырья в цеху
    IN_PRODUCTION = "IN_PRODUCTION"     # Партия формуется/сохнет в MES
    READY = "READY"                     # Готово на складе, можно забирать
    SHIPPED = "SHIPPED"                 # Отгружено клиенту на объект

class Order(Base):
    """Таблица заказов клиентов (Модуль ERP)"""
    __tablename__ = "erp_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_name: Mapped[str] = mapped_column(String(150), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("mes_products.id"), nullable=False)
    quantity_ordered: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(SQLEnum(OrderStatus), default=OrderStatus.CREATED)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

