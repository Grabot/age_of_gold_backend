"""Test file for tasks."""

from unittest.mock import MagicMock, patch

from age_of_gold_worker.age_of_gold_worker.tasks import (
    task_generate_avatar,
    task_initialize,
    task_send_email_delete_account,
    task_send_email_forgot_password,
)


def test_task_initialize() -> None:
    """Test the task_initialize function."""
    with patch("age_of_gold_worker.age_of_gold_worker.tasks.logger") as mock_logger:
        result = task_initialize()
        assert result == {"success": True}
        mock_logger.info.assert_called_once_with("initialize task")


@patch("age_of_gold_worker.age_of_gold_worker.tasks.avatar.generate_avatar")
@patch("age_of_gold_worker.age_of_gold_worker.tasks.worker_settings")
def test_task_generate_avatar(
    mock_worker_settings: MagicMock, mock_generate_avatar: MagicMock
) -> None:
    """Test the task_generate_avatar function."""
    mock_worker_settings.BASE_URL = "http://example.com"
    mock_worker_settings.API_V1_STR = "/api/v1"
    mock_worker_settings.UPLOAD_FOLDER_AVATARS = "/path/to/avatars"

    mock_response = MagicMock()
    mock_response.status_code = 200

    result = task_generate_avatar("avatar.png", 1)

    mock_generate_avatar.assert_called_once_with("avatar.png", "/path/to/avatars")
    assert result == {"success": True}


@patch("age_of_gold_worker.age_of_gold_worker.tasks.avatar.generate_avatar")
def test_task_generate_avatar_no_user_id(mock_generate_avatar: MagicMock) -> None:
    """Test the task_generate_avatar function."""
    result = task_generate_avatar("avatar.png", None)

    mock_generate_avatar.assert_not_called()
    assert result == {"success": False}


@patch("age_of_gold_worker.age_of_gold_worker.tasks.send_reset_email")
def test_task_send_email_forgot_password(mock_send_reset_email: MagicMock) -> None:
    """Test the task_send_email_forgot_password function."""
    result = task_send_email_forgot_password("test@test.test", "test", "test_token")

    mock_send_reset_email.assert_called_once_with(
        "test@test.test", "test", "test_token"
    )
    assert result == {"success": True}


@patch("age_of_gold_worker.age_of_gold_worker.tasks.send_delete_account")
def test_task_send_email_delete_account(mock_send_delete_account: MagicMock) -> None:
    """Test the task_send_email_delete_account function."""
    result = task_send_email_delete_account("test@test.test", "test", "test_token")

    mock_send_delete_account.assert_called_once_with(
        "test@test.test", "test", "test_token"
    )
    assert result == {"success": True}
