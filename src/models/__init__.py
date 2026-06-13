# Импортируем сам Base
from src.core.database import Base

# Импортируем все классы моделей, чтобы SQLAlchemy «увидела» их метаданные
from src.models.materials import Material, MaterialTransaction
from src.models.production import Product, ProductionLog, ProductRecipe

# Экспортируем их для удобного внешнего доступа (опционально)
__all__ = [
    "Base",
    "Material",
    "MaterialTransaction",
    "Product",
    "ProductionLog",
    "ProductRecipe",
]


