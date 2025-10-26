"""Test for avatar creation endpoint via direct post call."""

# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))


@pytest.mark.asyncio
@patch("src.api.api_v1.authorization.register.sio")
@patch("src.api.api_v1.authorization.register.asyncio.sleep")
async def test_avatar_created_success_post(
    mock_sleep: MagicMock, mock_sio: MagicMock, test_setup: TestClient
) -> None:
    """Test successful avatar creation via direct post call."""
    mock_sleep.return_value = None

    async def mock_emit(*args: Any, **kwargs: Any) -> None:
        """Mock emit function for socket.io."""

    mock_sio.emit = MagicMock(side_effect=mock_emit)

    response = test_setup.post(
        "/api/v1.0/avatar/created",
        json={"user_id": 1},
    )

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["result"] is True
    assert response_json["message"] == "Avatar creation done!"

    mock_sleep.assert_any_call(1)
    mock_sio.emit.assert_called_once_with(
        "message_event",
        "Avatar creation done!",
        room="room_1",
    )


if __name__ == "__main__":
    pytest.main([__file__])
