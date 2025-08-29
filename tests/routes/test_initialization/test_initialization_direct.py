# ruff: noqa: E402
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

import stat
from unittest.mock import MagicMock, patch

import pytest

from app.api.api_v1.initialization import initialize_folders
from app.config.config import settings


@pytest.mark.asyncio
async def test_successful_initialization_direct_avatar() -> None:
    def mock_exists(path: str) -> bool:
        if path == settings.UPLOAD_FOLDER_AVATARS:
            return False
        elif path == settings.UPLOAD_FOLDER_CRESTS:
            return True
        else:
            return False

    with (
        patch("os.path.exists", side_effect=mock_exists) as mock_exists,
        patch("os.makedirs") as mock_makedirs,
        patch("os.chmod") as mock_chmod,
        patch("app.api.api_v1.initialization.task_initialize") as mock_task_initialize,
    ):
        mock_exists.return_value = False
        mock_task_initialize.delay.return_value = MagicMock()

        response = await initialize_folders()

        assert response["results"] == "true"
        mock_makedirs.assert_called_with(settings.UPLOAD_FOLDER_AVATARS)
        mock_chmod.assert_called_with(
            settings.UPLOAD_FOLDER_AVATARS, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
        )
        mock_task_initialize.delay.assert_called_once()


@pytest.mark.asyncio
async def test_successful_initialization_direct_crest() -> None:
    def mock_exists(path: str) -> bool:
        if path == settings.UPLOAD_FOLDER_AVATARS:
            return True
        elif path == settings.UPLOAD_FOLDER_CRESTS:
            return False
        else:
            return False

    with (
        patch("os.path.exists", side_effect=mock_exists) as mock_exists,
        patch("os.makedirs") as mock_makedirs,
        patch("os.chmod") as mock_chmod,
        patch("app.api.api_v1.initialization.task_initialize") as mock_task_initialize,
    ):
        mock_exists.return_value = False
        mock_task_initialize.delay.return_value = MagicMock()

        response = await initialize_folders()

        assert response["results"] == "true"
        mock_makedirs.assert_called_with(settings.UPLOAD_FOLDER_CRESTS)
        mock_chmod.assert_called_with(
            settings.UPLOAD_FOLDER_CRESTS, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
        )
        mock_task_initialize.delay.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
