"""Test for register endpoint via direct function call."""

# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

from unittest.mock import MagicMock, patch

import pytest
from fastapi import Response, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from src.api.api_v1.authorization.register import RegisterRequest, register_user  # pylint: disable=C0413
from tests.conftest import ASYNC_TESTING_SESSION_LOCAL  # pylint: disable=C0413


@pytest.mark.asyncio
@patch("src.models.User.generate_auth_token")
@patch("src.models.User.generate_refresh_token")
@patch("src.celery_worker.tasks.task_generate_avatar.delay")
async def test_successful_register_direct(
    mock_task_generate_avatar: MagicMock,
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: MagicMock,
) -> None:
    """Test successful user registration via direct function call."""
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        login_request = RegisterRequest(
            email="new_test1@test.test",
            username="new_test1",
            password="new_test1password",
        )
        response_object = Response()

        response = await register_user(login_request, response_object, db)

        assert response["result"] is True
        assert response["access_token"] == expected_access_token
        assert response["refresh_token"] == expected_refresh_token
        mock_task_generate_avatar.assert_called_once()


@pytest.mark.asyncio
async def test_register_missing_fields(test_setup: MagicMock) -> None:
    """Test user registration with missing fields."""
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        register_request_email = RegisterRequest(
            email="", username="new_test2", password="new_test2password"
        )
        response_object_email = Response()

        response_email = await register_user(
            register_request_email, response_object_email, db
        )

        assert response_email["result"] is False
        assert response_email["message"] == "Invalid request"
        assert response_object_email.status_code == status.HTTP_400_BAD_REQUEST

        register_request_username = RegisterRequest(
            email="new_test3@test.test", username="", password="new_test3password"
        )
        response_object_username = Response()

        response_username = await register_user(
            register_request_username, response_object_username, db
        )

        assert response_username["result"] is False
        assert response_username["message"] == "Invalid request"
        assert response_object_username.status_code == status.HTTP_400_BAD_REQUEST

        register_request_password = RegisterRequest(
            email="new_test4@test.test", username="new_test4", password=""
        )
        response_object_password = Response()

        response_password = await register_user(
            register_request_password, response_object_password, db
        )

        assert response_password["result"] is False
        assert response_password["message"] == "Invalid request"
        assert response_object_password.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
@patch("src.models.User.generate_auth_token")
@patch("src.models.User.generate_refresh_token")
@patch("src.celery_worker.tasks.task_generate_avatar.delay")
async def test_register_username_already_taken(
    mock_task_generate_avatar: MagicMock,
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: MagicMock,
) -> None:
    """Test user registration with a username that is already taken."""
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        register_request = RegisterRequest(
            email="new_test5@test.test",
            username="new_test5",
            password="new_test5password",
        )
        response_object = Response()

        response = await register_user(register_request, response_object, db)

        assert response["result"] is True
        assert response["access_token"] == expected_access_token
        assert response["refresh_token"] == expected_refresh_token

        register_request = RegisterRequest(
            email="new_test5_2@test.test",
            username="new_test5",
            password="new_test5password",
        )
        response_object = Response()

        response = await register_user(register_request, response_object, db)

        assert response["result"] is False
        assert response["message"] == "Username already taken"
        assert response_object.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
@patch("src.models.User.generate_auth_token")
@patch("src.models.User.generate_refresh_token")
@patch("src.celery_worker.tasks.task_generate_avatar.delay")
async def test_register_email_already_used(
    mock_task_generate_avatar: MagicMock,
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: MagicMock,
) -> None:
    """Test user registration with an email that is already used."""
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token
    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        register_request = RegisterRequest(
            email="new_test6@test.test",
            username="new_test6",
            password="new_test6password",
        )
        response_object = Response()

        response = await register_user(register_request, response_object, db)

        assert response["result"] is True
        assert response["access_token"] == expected_access_token
        assert response["refresh_token"] == expected_refresh_token

        register_request = RegisterRequest(
            email="new_test6@test.test",
            username="new_test6_2",
            password="new_test6password",
        )
        response_object = Response()

        response = await register_user(register_request, response_object, db)

        assert response["result"] is False
        assert response["message"] == "Email already used"
        assert response_object.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
@patch("src.models.User.generate_auth_token")
@patch("src.models.User.generate_refresh_token")
@patch("src.celery_worker.tasks.task_generate_avatar.delay")
@patch("src.util.gold_logging.logger.error")
async def test_register_database_integrity_error(
    mock_logger_error: MagicMock,
    mock_task_generate_avatar: MagicMock,
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: MagicMock,
) -> None:
    """Test user registration with a database integrity error."""
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token

    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        with (
            patch.object(
                db,
                "commit",
                side_effect=IntegrityError("IntegrityError", "params", "orig"),
            ),
            patch.object(db, "rollback", return_value=None) as mock_rollback,
        ):
            register_request = RegisterRequest(
                email="new_test7@test.test",
                username="new_test7",
                password="new_test7password",
            )
            response_object = Response()
            response = await register_user(register_request, response_object, db)

            assert response["result"] is False
            assert response["message"] == "Internal server error"
            assert response_object.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

            mock_rollback.assert_called_once()
            mock_logger_error.assert_called_once()
            args, _ = mock_logger_error.call_args
            assert args[0] == "Database integrity error during registration: %s"
            assert isinstance(args[1], Exception)


@pytest.mark.asyncio
@patch("src.models.User.generate_auth_token")
@patch("src.models.User.generate_refresh_token")
@patch("src.celery_worker.tasks.task_generate_avatar.delay")
@patch("src.util.gold_logging.logger.error")
async def test_register_database_error(
    mock_logger_error: MagicMock,
    mock_task_generate_avatar: MagicMock,
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: MagicMock,
) -> None:
    """Test user registration with a database error."""
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token

    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        with (
            patch.object(db, "commit", side_effect=SQLAlchemyError("SQLAlchemyError")),
            patch.object(db, "rollback", return_value=None) as mock_rollback,
        ):
            register_request = RegisterRequest(
                email="new_test8@test.test",
                username="new_test8",
                password="new_test8password",
            )
            response_object = Response()
            response = await register_user(register_request, response_object, db)

            assert response["result"] is False
            assert response["message"] == "Internal server error"
            assert response_object.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

            mock_rollback.assert_called_once()
            mock_logger_error.assert_called_once()
            args, _ = mock_logger_error.call_args
            assert args[0] == "Database error during registration: %s"
            assert isinstance(args[1], Exception)


@pytest.mark.asyncio
@patch("src.models.User.generate_auth_token")
@patch("src.models.User.generate_refresh_token")
@patch("src.celery_worker.tasks.task_generate_avatar.delay")
@patch("src.util.gold_logging.logger.error")
async def test_register_unexpected_error(
    mock_logger_error: MagicMock,
    mock_task_generate_avatar: MagicMock,
    mock_generate_refresh_token: MagicMock,
    mock_generate_auth_token: MagicMock,
    test_setup: MagicMock,
) -> None:
    """Test user registration with an unexpected error."""
    expected_access_token = "access_token_test"
    expected_refresh_token = "refresh_token_test"
    mock_generate_auth_token.return_value = expected_access_token
    mock_generate_refresh_token.return_value = expected_refresh_token

    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        with (
            patch.object(db, "commit", side_effect=Exception("Unexpected error")),
            patch.object(db, "rollback", return_value=None) as mock_rollback,
        ):
            register_request = RegisterRequest(
                email="new_test9@test.test",
                username="new_test9",
                password="new_test9password",
            )
            response_object = Response()
            response = await register_user(register_request, response_object, db)

            assert response["result"] is False
            assert response["message"] == "Internal server error"
            assert response_object.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

            mock_rollback.assert_called_once()
            mock_logger_error.assert_called_once()
            args, _ = mock_logger_error.call_args
            assert args[0] == "Unexpected error during registration: %s"
            assert isinstance(args[1], Exception)


if __name__ == "__main__":
    pytest.main([__file__])
