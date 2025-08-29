# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.mark.asyncio
@patch("app.api.api_v1.authorization.register.sio")
@patch("app.api.api_v1.authorization.register.asyncio.sleep")
async def test_avatar_created_success_post(
    mock_sleep: MagicMock, mock_sio: MagicMock
) -> None:
    mock_sleep.return_value = None

    async def mock_emit(*args: Any, **kwargs: Any) -> None:
        pass

    mock_sio.emit = MagicMock(side_effect=mock_emit)

    with TestClient(app) as client:
        response = client.post(
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
