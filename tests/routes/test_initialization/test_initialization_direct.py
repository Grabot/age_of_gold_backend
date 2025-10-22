"""Test for initialization endpoint via direct function call."""

# ruff: noqa: E402
import sys
from pathlib import Path

import stat
from unittest.mock import MagicMock, patch

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.api.api_v1.initialization import initialize_folders  # pylint: disable=C0413
from src.config.config import settings  # pylint: disable=C0413


@pytest.mark.asyncio
async def test_successful_initialization_direct_avatar() -> None:
    """Test successful initialization of avatar folder."""

    def mock_exists(path: str) -> bool:
        if path == settings.UPLOAD_FOLDER_AVATARS:
            return False
        if path == settings.UPLOAD_FOLDER_CRESTS:
            return True

        return False

    with (
        patch("os.path.exists", side_effect=mock_exists) as mock_exists,
        patch("os.makedirs") as mock_makedirs,
        patch("os.chmod") as mock_chmod,
        patch("src.api.api_v1.initialization.task_initialize") as mock_task_initialize,
    ):
        mock_exists.return_value = False
        mock_task_initialize.delay.return_value = MagicMock()

        response = await initialize_folders()

        assert response["result"] is True
        mock_makedirs.assert_called_with(settings.UPLOAD_FOLDER_AVATARS)
        mock_chmod.assert_called_with(
            settings.UPLOAD_FOLDER_AVATARS, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
        )
        mock_task_initialize.delay.assert_called_once()


@pytest.mark.asyncio
async def test_successful_initialization_direct_crest() -> None:
    """Test successful initialization of crest folder."""

    def mock_exists(path: str) -> bool:
        if path == settings.UPLOAD_FOLDER_AVATARS:
            return True
        if path == settings.UPLOAD_FOLDER_CRESTS:
            return False

        return False

    with (
        patch("os.path.exists", side_effect=mock_exists) as mock_exists,
        patch("os.makedirs") as mock_makedirs,
        patch("os.chmod") as mock_chmod,
        patch("src.api.api_v1.initialization.task_initialize") as mock_task_initialize,
    ):
        mock_exists.return_value = False
        mock_task_initialize.delay.return_value = MagicMock()

        response = await initialize_folders()

        assert response["result"] is True
        mock_makedirs.assert_called_with(settings.UPLOAD_FOLDER_CRESTS)
        mock_chmod.assert_called_with(
            settings.UPLOAD_FOLDER_CRESTS, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
        )
        mock_task_initialize.delay.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
