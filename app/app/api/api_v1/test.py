from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.database import get_db
from app.models import User


@api_router_v1.get("/test", status_code=200)
async def get_test(db: AsyncSession = Depends(get_db)) -> dict:
    """
    api v1 GET
    """
    statement = select(User)
    results = await db.execute(statement)
    finals = []
    for result in results:
        finals.append(str(result))
    return {"results": finals}
