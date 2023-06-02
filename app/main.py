import uvicorn
from config import settings
from fastapi import APIRouter, Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session

from app.api import api_v1
from app.database import engine, get_db
from app.models import Friend, User

app = FastAPI()
api_router = APIRouter()
api_router.include_router(api_v1.api_router_v1, tags=["api_v1"])


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.post("/create/user", response_model=User)
async def create_user(user: User):
    with Session(engine) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


@app.post("/new/user")
async def user_new(user: User, db: AsyncSession = Depends(get_db)) -> dict:
    db.add(user)
    await db.commit()
    return {"quick": "test", "user": user}


@app.post("/create/friend", response_model=Friend)
async def create_friend(friend: Friend):
    with Session(engine) as session:
        session.add(friend)
        session.commit()
        session.refresh(friend)
        return friend


app.include_router(api_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    uvicorn.run("main:app", port=5000, host="0.0.0.0", reload=True)
