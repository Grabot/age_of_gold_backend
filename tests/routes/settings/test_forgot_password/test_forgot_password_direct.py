"""Test for forgot password endpoint via direct function call."""

from fastapi import HTTPException, status
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch

from sqlmodel import select
from src.api.api_v1.settings import forgot_password
from src.models.user_token import UserToken
from tests.conftest import add_user


@pytest.mark.asyncio
async def test_successful_forgot_password_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful forgot password via direct function call."""
    test_user = await add_user("mail_user", 0, test_db, "test.test")

    with patch(
        "src.api.api_v1.settings.forgot_password.task_send_email_forgot_password.delay"
    ) as mock_mail_task:
        email = "mail_user@test.test"
        password_forgot_request = forgot_password.PasswordForgotRequest(email=email)

        response_json = await forgot_password.forgot_password(
            password_forgot_request, test_db
        )

        assert response_json["success"] is True

        mock_mail_task.assert_called_once()
        _, kwargs = mock_mail_task.call_args
        assert kwargs["to_email"] == email
        assert kwargs["subject"] == "Reset your password - Age of Gold"
        assert "access_token" in kwargs

        result = await test_db.execute(
            select(UserToken).where(UserToken.user_id == test_user.id)
        )
        user_token: UserToken = result.scalars().first()
        assert user_token is not None
        assert user_token.token_expiration is not None


@pytest.mark.asyncio
async def test_forgot_password_no_user_found(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test forgot password with an email that doesn't exist in the database."""
    email = "nonexistent@test.test"
    password_forgot_request = forgot_password.PasswordForgotRequest(email=email)

    with pytest.raises(HTTPException) as exc_info:
        await forgot_password.forgot_password(password_forgot_request, test_db)

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc_info.value.detail == "no account found using this email"
