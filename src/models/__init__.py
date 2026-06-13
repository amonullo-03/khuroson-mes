from src.core.database import Base
from src.modules.wms.models import Location, Material, MaterialTransaction
from src.modules.mes.models import Product, ProductRecipe, ProductionBatch
from src.modules.erp.models import Order

# Экспортируем Base для Alembic
__all__ = ["Base"]


