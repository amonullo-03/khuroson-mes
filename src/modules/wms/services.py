from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from src.modules.wms.models import Material, MaterialTransaction, TransactionType
from src.modules.wms.schemas import MaterialBalance
from typing import List

async def get_material_balances_by_location(db: AsyncSession, location_id: int) -> List[MaterialBalance]:
    """
    Оптимизированный расчет остатков сырья на конкретном складе (1 SQL запрос)
    """
    stmt = (
        select(
            Material.id,
            Material.name,
            Material.unit,
            func.coalesce(
                func.sum(
                    case(
                        (MaterialTransaction.transaction_type == TransactionType.INFLOW, MaterialTransaction.quantity),
                        else_=0.0
                    )
                ) - func.sum(
                    case(
                        (MaterialTransaction.transaction_type == TransactionType.OUTFLOW, MaterialTransaction.quantity),
                        else_=0.0
                    )
                ), 
                0.0
            ).label("balance")
        )
        .join(MaterialTransaction, Material.id == MaterialTransaction.material_id, isouter=True)
        .where(MaterialTransaction.location_id == location_id) # Фильтр по конкретному складу
        .group_by(Material.id, Material.name, Material.unit)
    )
    
    result = await db.execute(stmt)
    balances = []
    for row in result.all():
        balances.append(MaterialBalance(
            material_id=row.id,
            name=row.name,
            unit=row.unit,
            balance=float(row.balance)
        ))
    return balances

