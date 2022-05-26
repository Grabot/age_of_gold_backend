import uvicorn
from app import app
from init import add_settings
import routes


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.on_event("startup")
async def startup_event():
    # On startup we want to initialize the project
    await add_settings()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

