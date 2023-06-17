from celery_worker.tasks import task_add
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.database import get_db
from app.models import Hexagon


@api_router_v1.get("/test", status_code=200)
async def get_test(db: AsyncSession = Depends(get_db)) -> dict:
    print("1")
    statement = (
        select(Hexagon)
        .where(Hexagon.q == 0 and Hexagon.r == 0)
        .options(selectinload(Hexagon.tiles))
    )
    results = await db.execute(statement)
    hexagon = results.first()
    print(f"hexagon: {hexagon}")
    print(f"hexagon: {hexagon.Hexagon}")
    print(f"hexagon: {hexagon.Hexagon.tiles}")
    return {"results": "true"}


@api_router_v1.post("/users/{count}/{delay}", status_code=201)
def add_user(count: int, delay: int):
    """
    Get random user data from randomuser.me/api and
    add database using Celery. Uses Redis as Broker
    and Postgres as Backend.
    """
    task = task_add.delay(count, delay)
    return {"task_id": task.id}
