import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import pytest
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi import Response
from app.api.api_v1.authorization.login import LoginRequest, login_user
from fastapi.testclient import TestClient
from main import app

DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)

@pytest.fixture(scope="module", autouse=True)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

@pytest.fixture(scope="function")
async def session():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
        await session.rollback()

@pytest.fixture(scope="function")
def client():
    with TestClient(app) as c:
        yield c

@pytest.mark.asyncio
async def test_successful_login_with_email_direct_call():
    # Mock the response
    mock_response = MagicMock(spec=Response)

    # Mock the user and its methods
    mock_user = MagicMock()
    mock_user.origin = 0
    mock_user.verify_password.return_value = True
    mock_user.serialize = {"id": 1, "username": "testuser"}

    # Mock the result of the database query
    mock_result = AsyncMock()
    mock_result.first.return_value = MagicMock(User=mock_user)

    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute.return_value = mock_result

    # Mock the get_db dependency to return your mock_session
    with patch("app.api.api_v1.authorization.login.get_db", return_value=mock_session):
        login_request = LoginRequest(
            user_name="testuser",
            password="testpassword"
        )
        result = await login_user(
            login_request=login_request,
            response=mock_response,
            db=mock_session
        )
        assert result["result"] is True
        mock_session.execute.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])