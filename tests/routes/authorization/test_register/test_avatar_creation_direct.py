# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from typing import Any, Generator, Optional
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Response
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import select

from app.api.api_v1.authorization.refresh import RefreshRequest, refresh_user
from app.api.api_v1.authorization.register import AvatarCreatedRequest, avatar_created
from app.models.user import User
from app.models.user_token import UserToken
from tests.conftest import AsyncTestingSessionLocal, test_setup


@pytest.mark.asyncio
@patch("app.api.api_v1.authorization.register.sio")
@patch("app.api.api_v1.authorization.register.asyncio.sleep")
async def test_avatar_created_success(
    mock_sleep: MagicMock, mock_sio: MagicMock
) -> None:
    mock_sleep.return_value = None

    async def mock_emit(*args: Any, **kwargs: Any) -> None:
        pass

    mock_sio.emit = MagicMock(side_effect=mock_emit)

    avatar_created_request = AvatarCreatedRequest(user_id=1)
    response = await avatar_created(avatar_created_request)

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
