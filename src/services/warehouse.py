# src/services/warehouse.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from src.models.materials import Material, MaterialTransaction, TransactionType
from src.schemas.materials import MaterialBalance
from typing import List

async def get_all_material_balances(db: AsyncSession) -> List[MaterialBalance]:
    """
    Оптимизированный сервис расчета остатков.
    Делает всего 1 запрос к базе данных вместо N+1!
    """
    # Считаем сумму приходов и расходов, группируя по материалам
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

