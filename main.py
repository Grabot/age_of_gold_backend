import uvicorn
from models import User as ModelUser
from schema import SchemaUser
from app import app
from init import add_settings


@app.post("/user/")
async def create_user(user: SchemaUser):
    user_id = await ModelUser.create(**user.dict())
    return {"user_id": user_id}


@app.get("/user/{id}", response_model=SchemaUser)
async def get_user(id: int):
    user = await ModelUser.get(id)
    return SchemaUser(**user).dict()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.on_event("startup")
async def startup_event():
    # On startup we want to initialize the project
    await add_settings()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

