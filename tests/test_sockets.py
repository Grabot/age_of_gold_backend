"""Testing file for sockets."""

from typing import Dict, Optional, Union
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from pytest import CaptureFixture

from src.models.user import User
from src.sockets.sockets import (
    handle_connect,
    handle_disconnect,
    handle_join,
    handle_join_group,
    handle_leave,
    handle_leave_group,
    handle_message_event,
)
from tests.conftest import ASYNC_TESTING_SESSION_LOCAL


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
        await handle_join("test_sid_1", data)

        mock_sio.enter_room.assert_called_once_with("test_sid_1", "room_1")
        mock_sio.emit.assert_called_once_with(
            "message_event",
            "User has entered room room_1",
            room="room_1",
        )

        data_not_real: Dict[str, Union[int, str]] = {"user_id": 2}
        await handle_join("test_sid_2", data_not_real)

        mock_sio.enter_room.assert_any_call("test_sid_1", "room_1")
        mock_sio.enter_room.assert_any_call("test_sid_2", "room_2")
        mock_sio.emit.assert_any_call(
            "message_event",
            "User has entered room room_2",
            room="room_2",
        )
        mock_sio.emit.assert_any_call(
            "message_event",
            "User has entered room room_1",
            room="room_1",
        )

        async with ASYNC_TESTING_SESSION_LOCAL() as db:
            retrieved_user: Optional[User] = await db.get(User, 1)
            assert retrieved_user is not None
            assert retrieved_user.id == user.id
            assert retrieved_user.username == user.username


@pytest.mark.asyncio
async def test_handle_join_group() -> None:
    """Test the handle_join_group function."""
    with patch("src.sockets.sockets.sio") as mock_sio:
        mock_sio.enter_room = AsyncMock()
        mock_sio.emit = AsyncMock()

        data: Dict[str, Union[int, str]] = {"chat_id": 1}
        await handle_join_group("test_sid", data)

        mock_sio.enter_room.assert_called_once_with("test_sid", "group_1")
        mock_sio.emit.assert_called_once_with(
            "message_event",
            "User has entered group room group_1",
            room="group_1",
        )


@pytest.mark.asyncio
async def test_handle_leave_group() -> None:
    """Test the handle_leave_group function."""
    with patch("src.sockets.sockets.sio") as mock_sio:
        mock_sio.leave_room = AsyncMock()
        mock_sio.emit = AsyncMock()

        data: Dict[str, Union[int, str]] = {"chat_id": 1}
        await handle_leave_group("test_sid", data)

        mock_sio.leave_room.assert_called_once_with("test_sid", "group_1")
        mock_sio.emit.assert_called_once_with(
            "message_event",
            "User has left group room group_1",
            room="test_sid",
        )
