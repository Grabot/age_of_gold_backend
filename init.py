from fastapi.middleware.cors import CORSMiddleware
from app import app


# Initialization of backend
async def add_settings():
    # Fix CORS stuff
    origins = [
        "http://localhost",
        "http://localhost:8080",
        "http://localhost:8082",
        "http://172.27.6.101:8080",
        "http://172.27.6.101:8082"
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

