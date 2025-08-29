# ruff: noqa: E402
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from unittest.mock import MagicMock, patch

import pytest

from app.celery_worker.tasks import task_generate_avatar, task_initialize


def test_task_initialize() -> None:
    with patch("app.celery_worker.tasks.logger") as mock_logger:
        result = task_initialize()
        assert result == {"success": True}
        mock_logger.info.assert_called_once_with("initialize task")


@patch("app.celery_worker.tasks.generate_avatar")
@patch("app.celery_worker.tasks.requests.post")
@patch("app.celery_worker.tasks.settings")
def test_task_generate_avatar(
    mock_settings: MagicMock, mock_post: MagicMock, mock_generate_avatar: MagicMock
) -> None:
    mock_settings.BASE_URL = "http://example.com"
    mock_settings.API_V1_STR = "/api/v1"
    mock_settings.UPLOAD_FOLDER_AVATARS = "/path/to/avatars"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    result = task_generate_avatar("avatar.png", 1)

    mock_generate_avatar.assert_called_once_with("avatar.png", "/path/to/avatars")
    mock_post.assert_called_once_with(
        "http://example.com/api/v1/avatar/created",
        json={"user_id": 1},
    )
    assert result == {"success": True}


if __name__ == "__main__":
    pytest.main([__file__])
