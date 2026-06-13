from datetime import datetime
import enum
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base

class TransactionType(str, enum.Enum):
    INFLOW = "INFLOW"
    OUTFLOW = "OUTFLOW"

class Location(Base):
    """Справочник физических локаций (Цех Хуросон, Склад №1, Объект)"""
    __tablename__ = "wms_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    type: Mapped[str] = mapped_column(String(50)) # "FACTORY", "WAREHOUSE", "CLIENT_SITE"

class Material(Base):
    """Справочник сырья и материалов (универсальный для SaaS)"""
    __tablename__ = "wms_materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)

class MaterialTransaction(Base):
    """Движение сырья с привязкой к конкретному складу/цеху"""
    __tablename__ = "wms_material_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("wms_materials.id"), nullable=False)
    location_id: Mapped[int] = mapped_column(ForeignKey("wms_locations.id"), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(SQLEnum(TransactionType), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    comment: Mapped[str] = mapped_column(String(255), nullable=True)

