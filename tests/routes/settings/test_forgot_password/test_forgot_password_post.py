"""Test for forgot password endpoint via direct get call."""

from typing import Any
from unittest.mock import patch
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.config.config import settings
from src.models.user_token import UserToken
from tests.conftest import add_user


@pytest.mark.asyncio
async def test_successful_forgot_password(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful forgot password with valid token."""
    test_user = await add_user("mail_user", 0, test_db, "test.test")

    with patch(
        "src.api.api_v1.settings.forgot_password.task_send_email_forgot_password.delay"
    ) as mock_mail_task:
        email = "mail_user@test.test"
        response = test_setup.post(
            f"{settings.API_V1_STR}/password/forgot",
            json={
                "email": email,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["success"] is True

        mock_mail_task.assert_called_once()
        _, kwargs = mock_mail_task.call_args
        assert kwargs["to_email"] == email
        assert kwargs["subject"] == "Reset your password - Age of Gold"
        assert "access_token" in kwargs

        result = await test_db.execute(
            select(UserToken).where(UserToken.user_id == test_user.id)
        )
        user_token: Any = result.scalars().first()
        assert isinstance(user_token, UserToken)
        assert user_token is not None
        assert user_token.token_expiration is not None
