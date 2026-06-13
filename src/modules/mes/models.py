from datetime import datetime
import enum
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base

class BatchStatus(str, enum.Enum):
    MOLDING = "MOLDING"      # Формовка на станке
    CURING = "CURING"        # Сушка в камере пропарки
    MATURING = "MATURING"    # Вылеживание на складе (набор прочности)
    DONE = "DONE"            # Проверено ОТК, принято на склад готовой продукции

class Product(Base):
    """Справочник выпускаемой продукции цеха"""
    __tablename__ = "mes_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    unit: Mapped[str] = mapped_column(String(20), default="шт")

class ProductRecipe(Base):
    """Спецификация расхода сырья"""
    __tablename__ = "mes_product_recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("mes_products.id", ondelete="CASCADE"), nullable=False)
    material_id: Mapped[int] = mapped_column(ForeignKey("wms_materials.id", ondelete="CASCADE"), nullable=False)
    quantity_per_unit: Mapped[float] = mapped_column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint('product_id', 'material_id', name='uq_product_material_mes'),
    )

class ProductionBatch(Base):
    """Учет партий производства и стадий сушки"""
    __tablename__ = "mes_production_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("mes_products.id"), nullable=False)
    location_id: Mapped[int] = mapped_column(ForeignKey("wms_locations.id"), nullable=False) # Где сейчас партия
    order_id: Mapped[int] = mapped_column(Integer, nullable=True) # Привязка к заказу ERP (если есть)
    
    quantity_molded: Mapped[int] = mapped_column(Integer, nullable=False)   # Сколько отформовали
    quantity_good: Mapped[int] = mapped_column(Integer, default=0)         # Сдано на склад ГП
    quantity_defective: Mapped[int] = mapped_column(Integer, default=0)    # Выявленный брак
    
    status: Mapped[BatchStatus] = mapped_column(SQLEnum(BatchStatus), default=BatchStatus.MOLDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    operator_name: Mapped[str] = mapped_column(String(100), nullable=True)

