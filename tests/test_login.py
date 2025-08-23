import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from app.models import User
from fastapi import APIRouter, FastAPI, Response

from app.api import api_v1
from main import app
from app.api.api_v1.authorization.login import LoginRequest, login_user
from app.config.config import settings
import asyncio

DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)

@pytest.fixture(scope="module")
def client():
    async def init_db():
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    asyncio.run(init_db())

    with TestClient(app) as c:
        yield c

@pytest.mark.asyncio
async def test_successful_login_with_email(client):
    response = client.post("/api/v1.0/login", json={"user_name": "testuser", "password": "testpassword"})
    assert response.status_code == 200
    assert response.json()["result"] is True

if __name__ == "__main__":
    pytest.main([__file__])
