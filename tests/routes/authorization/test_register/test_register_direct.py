"""Test for register endpoint via direct function call."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.authorization import register
from src.util.util import SuccessfulLoginResponse
from tests.helpers import (
    assert_exception_error_response,
    assert_integrity_error_response,
    assert_sqalchemy_error_response,
    assert_successful_login_dict,
)


@pytest.mark.asyncio
@patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay")
async def test_successful_register_direct(
    mock_task_generate_avatar: MagicMock,
    mock_tokens: tuple[str, str, MagicMock, MagicMock],
    test_setup: MagicMock,
    test_db: AsyncSession,
) -> None:
    """Test successful user registration via direct function call."""
    expected_access_token, expected_refresh_token, _, _ = mock_tokens
    login_request = register.RegisterRequest(
        email="new_test1@test.test",
        username="new_test1",
        password="new_test1password",
    )

    response_dict: SuccessfulLoginResponse = await register.register_user(
        login_request, test_db
    )

    assert_successful_login_dict(
        response_dict, expected_access_token, expected_refresh_token
    )
    mock_task_generate_avatar.assert_called_once()


@pytest.mark.asyncio
async def test_register_missing_fields_email(
    test_setup: MagicMock,
    test_db: AsyncSession,
) -> None:
    """Test user registration with missing email field."""
    register_request_email = register.RegisterRequest(
        email="", username="new_test2", password="new_test2password"
    )
    with pytest.raises(HTTPException) as exc_info:
        await register.register_user(register_request_email, test_db)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Invalid request"


@pytest.mark.asyncio
async def test_register_missing_fields_username(
    test_setup: MagicMock,
    test_db: AsyncSession,
) -> None:
    """Test user registration with missing username field."""
    register_request_username = register.RegisterRequest(
        email="new_test3@test.test", username="", password="new_test3password"
    )
    with pytest.raises(HTTPException) as exc_info:
        await register.register_user(register_request_username, test_db)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Invalid request"


@pytest.mark.asyncio
async def test_register_missing_fields_password(
    test_setup: MagicMock,
    test_db: AsyncSession,
) -> None:
    """Test user registration with missing password field."""
    register_request_password = register.RegisterRequest(
        email="new_test4@test.test", username="new_test4", password=""
    )
    with pytest.raises(HTTPException) as exc_info:
        await register.register_user(register_request_password, test_db)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Invalid request"


@pytest.mark.asyncio
@patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay")
async def test_register_username_already_taken(
    mock_task_generate_avatar: MagicMock,
    mock_tokens: tuple[str, str, MagicMock, MagicMock],
    test_setup: MagicMock,
    test_db: AsyncSession,
) -> None:
    """Test user registration with a username that is already taken."""
    expected_access_token, expected_refresh_token, _, _ = mock_tokens
    register_request = register.RegisterRequest(
        email="new_test5@test.test",
        username="new_test5",
        password="new_test5password",
    )
    response_dict: SuccessfulLoginResponse = await register.register_user(
        register_request, test_db
    )

    assert_successful_login_dict(
        response_dict, expected_access_token, expected_refresh_token
    )

    register_request = register.RegisterRequest(
        email="new_test5_2@test.test",
        username="new_test5",
        password="new_test5password",
    )
    with pytest.raises(HTTPException) as exc_info:
        await register.register_user(register_request, test_db)

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert exc_info.value.detail == "Username already taken"
    mock_task_generate_avatar.assert_called_once()


@pytest.mark.asyncio
@patch("age_of_gold_worker.age_of_gold_worker.tasks.task_generate_avatar.delay")
async def test_register_email_already_used(
    mock_task_generate_avatar: MagicMock,
    mock_tokens: tuple[str, str, MagicMock, MagicMock],
    test_setup: MagicMock,
    test_db: AsyncSession,
) -> None:
    """Test user registration with an email that is already used."""
    expected_access_token, expected_refresh_token, _, _ = mock_tokens
    register_request = register.RegisterRequest(
        email="new_test6@test.test",
        username="new_test6",
        password="new_test6password",
    )
    response_dict: SuccessfulLoginResponse = await register.register_user(
        register_request, test_db
    )

    assert_successful_login_dict(
        response_dict, expected_access_token, expected_refresh_token
    )

    register_request = register.RegisterRequest(
        email="new_test6@test.test",
        username="new_test6_2",
        password="new_test6password",
    )
    with pytest.raises(HTTPException) as exc_info:
        await register.register_user(register_request, test_db)
    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert exc_info.value.detail == "Email already used"


@pytest.mark.asyncio
@patch("src.util.gold_logging.logger.error")
async def test_register_database_integrity_error(
    mock_logger_error: MagicMock,
    test_setup: MagicMock,
    test_db: AsyncSession,
) -> None:
    """Test user registration with a database integrity error."""
    with (
        patch.object(
            test_db,
            "commit",
            side_effect=IntegrityError("IntegrityError", "params", "orig"),
        ),
        patch.object(test_db, "rollback", return_value=None) as mock_rollback,
    ):
        register_request = register.RegisterRequest(
            email="new_test7@test.test",
            username="new_test7",
            password="new_test7password",
        )
        with pytest.raises(HTTPException) as exc_info:
            await register.register_user(register_request, test_db)

        mock_rollback.assert_called_once()

        assert_integrity_error_response(
            exc_info.value,
            mock_logger_error,
        )


@pytest.mark.asyncio
@patch("src.util.gold_logging.logger.error")
async def test_register_database_error(
    mock_logger_error: MagicMock,
    test_setup: MagicMock,
    test_db: AsyncSession,
) -> None:
    """Test user registration with a database error."""
    with (
        patch.object(test_db, "commit", side_effect=SQLAlchemyError("SQLAlchemyError")),
        patch.object(test_db, "rollback", return_value=None) as mock_rollback,
    ):
        register_request = register.RegisterRequest(
            email="new_test8@test.test",
            username="new_test8",
            password="new_test8password",
        )
        with pytest.raises(HTTPException) as exc_info:
            await register.register_user(register_request, test_db)

        mock_rollback.assert_called_once()

        assert_sqalchemy_error_response(
            exc_info.value,
            mock_logger_error,
            "Registration failed",
        )


@pytest.mark.asyncio
@patch("src.util.gold_logging.logger.error")
async def test_register_unexpected_error(
    mock_logger_error: MagicMock,
    test_setup: MagicMock,
    test_db: AsyncSession,
) -> None:
    """Test user registration with an unexpected error."""
    with (
        patch.object(test_db, "commit", side_effect=Exception("Unexpected error")),
        patch.object(test_db, "rollback", return_value=None) as mock_rollback,
    ):
        register_request = register.RegisterRequest(
            email="new_test9@test.test",
            username="new_test9",
            password="new_test9password",
        )
        with pytest.raises(HTTPException) as exc_info:
            await register.register_user(register_request, test_db)

        mock_rollback.assert_called_once()

        assert_exception_error_response(
            exc_info.value,
            mock_logger_error,
            "Registration failed",
        )
