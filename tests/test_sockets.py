"""Testing file for sockets."""

# ruff: noqa: E402
import sys
from pathlib import Path
from typing import Dict, Optional, Union
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from pytest import CaptureFixture

sys.path.append(str(Path(__file__).parent.parent))

from src.models.user import User  # pylint: disable=C0413
from src.sockets.sockets import (  # pylint: disable=C0413
    handle_connect,
    handle_disconnect,
    handle_join,
    handle_leave,
    handle_message_event,
)
from tests.conftest import ASYNC_TESTING_SESSION_LOCAL  # pylint: disable=C0413


@pytest.mark.asyncio
async def test_handle_connect(capfd: CaptureFixture[str]) -> None:
    """Test the handle_connect function."""
    await handle_connect("test_sid")
    captured = capfd.readouterr()
    assert "Received connect: test_sid" in captured.out


@pytest.mark.asyncio
async def test_handle_disconnect(capfd: CaptureFixture[str]) -> None:
    """Test the handle_disconnect function."""
    await handle_disconnect("test_sid")
    captured = capfd.readouterr()
    assert "Received disconnect: test_sid" in captured.out


@pytest.mark.asyncio
async def test_handle_message_event(capfd: CaptureFixture[str]) -> None:
    """Test the handle_message_event function."""
    await handle_message_event("test_sid")
    captured = capfd.readouterr()
    assert "Received message_event: test_sid" in captured.out


@pytest.mark.asyncio
async def test_handle_join(test_setup: TestClient) -> None:
    """Test the handle_join function."""
    with (
        patch("src.sockets.sockets.sio") as mock_sio,
        patch("src.sockets.sockets.async_session", new=ASYNC_TESTING_SESSION_LOCAL),
    ):
        mock_sio.enter_room = AsyncMock()
        mock_sio.emit = AsyncMock()

        data: Dict[str, Union[int, str]] = {"user_id": 1}
        await handle_join("test_sid", data)

        mock_sio.enter_room.assert_called_once_with("test_sid", "room_1")
        mock_sio.emit.assert_called_once_with(
            "message_event",
            "User has entered room room_1",
            room="room_1",
        )


@pytest.mark.asyncio
async def test_handle_leave() -> None:
    """Test the handle_leave function."""
    with patch("src.sockets.sockets.sio") as mock_sio:
        mock_sio.leave_room = AsyncMock()
        mock_sio.emit = AsyncMock()

        data: Dict[str, Union[int, str]] = {"user_id": 1}
        await handle_leave("test_sid", data)

        mock_sio.leave_room.assert_called_once_with("test_sid", "room_1")
        mock_sio.emit.assert_called_once_with(
            "message_event",
            "User has left room room_1",
            room="test_sid",
        )


@pytest.mark.asyncio
async def test_handle_join_with_db(test_setup: TestClient) -> None:
    """Test the handle_join function with database interaction."""

    async with ASYNC_TESTING_SESSION_LOCAL() as db:
        user: Optional[User] = await db.get(User, 1)
        assert user is not None

    with (
        patch("src.sockets.sockets.sio") as mock_sio,
        patch("src.sockets.sockets.async_session", new=ASYNC_TESTING_SESSION_LOCAL),
    ):
        mock_sio.enter_room = AsyncMock()
        mock_sio.emit = AsyncMock()

        data: Dict[str, Union[int, str]] = {"user_id": 1}
        await handle_join("test_sid", data)

        mock_sio.enter_room.assert_called_once_with("test_sid", "room_1")
        mock_sio.emit.assert_called_once_with(
            "message_event",
            "User has entered room room_1",
            room="room_1",
        )

        async with ASYNC_TESTING_SESSION_LOCAL() as db:
            retrieved_user: Optional[User] = await db.get(User, 1)
            assert retrieved_user is not None
            assert retrieved_user.id == user.id
            assert retrieved_user.username == user.username


if __name__ == "__main__":
    pytest.main([__file__])
