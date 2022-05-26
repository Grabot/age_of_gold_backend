from models import User
from schema import SchemaUser
from app import app


@app.post("/user/")
async def create_user(user: SchemaUser):
    user_id = await User.create(**user.dict())
    return {"user_id": user_id}


@app.get("/user/{id}", response_model=SchemaUser)
async def get_user(id: int):
    user = await User.get(id)
    return SchemaUser(**user).dict()

