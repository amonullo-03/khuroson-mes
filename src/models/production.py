# src/models/production.py
from datetime import datetime
from typing import List, Optional
from sqlalchemy import ForeignKey, String, Integer, Float, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base

class Product(Base):
    """Справочник готовой продукции цеха"""
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)  # "Шлакоблок Усиленный 19х19х39"
    unit: Mapped[str] = mapped_column(String(20), default="шт")                  # Единица измерения
    
    # Связь с логами выпуска продукции
    production_logs: Mapped[List["ProductionLog"]] = relationship(
        back_populates="product", 
        cascade="all, delete-orphan"
    )


class ProductionLog(Base):
    """Журнал выпуска готовой продукции смены"""
    __tablename__ = "production_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity_produced: Mapped[int] = mapped_column(Integer, nullable=False)   # Сколько сделали хорошего товара
    quantity_defective: Mapped[int] = mapped_column(Integer, default=0, nullable=False) # Сколько ушло в брак
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    operator_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Кто зафиксировал (Ахмед, Баха)

    # Отношение к продукту
    product: Mapped["Product"] = relationship(back_populates="production_logs")



class ProductRecipe(Base):
    """Спецификация: сколько какого сырья нужно на 1 единицу продукта"""
    __tablename__ = "product_recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id", ondelete="CASCADE"), nullable=False)
    quantity_per_unit: Mapped[float] = mapped_column(Float, nullable=False)

    # ЭТА СТРОКА ЗАБЛОКИРУЕТ БАГИ НА УРОВНЕ СУБД:
    __table_args__ = (
        UniqueConstraint('product_id', 'material_id', name='uq_product_material'),
    )

