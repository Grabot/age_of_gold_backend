# ruff: noqa: E402
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from typing import Any, Dict, Generator, Optional, Union
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest import CaptureFixture

from app.sockets.sockets import (
    handle_connect,
    handle_disconnect,
    handle_join,
    handle_leave,
    handle_message_event,
)
from tests.conftest import AsyncTestingSessionLocal, test_setup

@pytest.mark.asyncio
async def test_handle_connect(capfd: CaptureFixture[str]) -> None:
    await handle_connect("test_sid")
    captured = capfd.readouterr()
    assert "Received connect: test_sid" in captured.out

@pytest.mark.asyncio
async def test_handle_disconnect(capfd: CaptureFixture[str]) -> None:
    await handle_disconnect("test_sid")
    captured = capfd.readouterr()
    assert "Received disconnect: test_sid" in captured.out

@pytest.mark.asyncio
async def test_handle_message_event(capfd: CaptureFixture[str]) -> None:
    await handle_message_event("test_sid")
    captured = capfd.readouterr()
    assert "Received message_event: test_sid" in captured.out

@pytest.mark.asyncio
async def test_handle_join(test_setup: Generator[Any, Any, Any]) -> None:
    with patch("app.sockets.sockets.sio") as mock_sio, \
         patch("app.sockets.sockets.async_session", new=AsyncTestingSessionLocal):
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
    with patch("app.sockets.sockets.sio") as mock_sio:
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
async def test_handle_join_with_db(test_setup: Generator[Any, Any, Any]) -> None:
    from app.models.user import User
    from app.database import async_session

    async with AsyncTestingSessionLocal() as db:
        user: Optional[User] = await db.get(User, 1)
        assert user is not None

    with patch("app.sockets.sockets.sio") as mock_sio, \
         patch("app.sockets.sockets.async_session", new=AsyncTestingSessionLocal):

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

        async with AsyncTestingSessionLocal() as db:
            retrieved_user: Optional[User] = await db.get(User, 1)
            assert retrieved_user is not None
            assert retrieved_user.id == user.id
            assert retrieved_user.username == user.username

if __name__ == "__main__":
    pytest.main([__file__])

