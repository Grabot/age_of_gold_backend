"""Test for avatar creation endpoint via direct function call."""

# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from src.api.api_v1.authorization import register  # pylint: disable=C0413


@pytest.mark.asyncio
@patch("src.api.api_v1.authorization.register.sio")
@patch("src.api.api_v1.authorization.register.asyncio.sleep")
async def test_avatar_created_success(
    mock_sleep: MagicMock, mock_sio: MagicMock
) -> None:
    """Test successful avatar creation."""
    mock_sleep.return_value = None

    async def mock_emit(*args: Any, **kwargs: Any) -> None:
        """Mock emit function."""

    mock_sio.emit = MagicMock(side_effect=mock_emit)

    avatar_created_request = register.AvatarCreatedRequest(user_id=1)
    response = await register.avatar_created(avatar_created_request)

    mock_sleep.assert_called_once_with(1)
    mock_sio.emit.assert_called_once_with(
        "message_event",
        "Avatar creation done!",
        room="room_1",
    )

    assert response["result"] is True
    assert response["message"] == "Avatar creation done!"


if __name__ == "__main__":
    pytest.main([__file__])
