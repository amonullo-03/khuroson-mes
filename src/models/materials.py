# src/models/materials.py
from datetime import datetime
from enum import Enum
from typing import List, Optional
from sqlalchemy import ForeignKey, String, Integer, Float, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base

class TransactionType(str, Enum):
    INFLOW = "INFLOW"    # Приход сырья на склад
    OUTFLOW = "OUTFLOW"  # Расход сырья (ушло в бетономешалку / брак)

class Material(Base):
    """Справочник сырья и материалов"""
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)  # Например: "Цемент М500 (Душанбе)"
    unit: Mapped[str] = mapped_column(String(20), nullable=False)      # Например: "кг", "тонна"
    
    # Связь с транзакциями. cascade указывает, что если мы удалим материал, 
    # из базы также удалятся все его исторические транзакции.
    transactions: Mapped[List["MaterialTransaction"]] = relationship(
        back_populates="material", 
        cascade="all, delete-orphan"
    )

class MaterialTransaction(Base):
    """Журнал движения сырья (Приход / Расход)"""
    __tablename__ = "material_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(SQLEnum(TransactionType), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # "Поставка от поставщика Х"

    # Отношение к материалу (используем строку "Material" во избежание циклических импортов)
    material: Mapped["Material"] = relationship(back_populates="transactions")
