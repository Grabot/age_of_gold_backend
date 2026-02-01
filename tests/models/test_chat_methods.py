"""Test for Chat model methods."""

import pytest
from botocore.exceptions import ClientError

from src.models.chat import Chat


@pytest.fixture
def test_chat() -> Chat:
    """Create a test chat instance."""
    return Chat(
        id=1,
        user_ids=[1, 2, 3],
        user_admin_ids=[1],
        private=True,
        group_name="Test Group",
        group_description="Test Description",
        group_colour="#FF5733",
        default_avatar=True,
        current_message_id=1,
        last_message_read_id_chat=1,
        message_version=1,
        avatar_version=1,
    )


def test_chat_add_user(test_chat: Chat) -> None:  # pylint: disable=redefined-outer-name
    """Test adding a user to chat."""
    initial_users = test_chat.user_ids.copy()
    test_chat.add_user(4)
    assert test_chat.user_ids == sorted(initial_users + [4])


def test_chat_add_user_duplicate(test_chat: Chat) -> None:  # pylint: disable=redefined-outer-name
    """Test adding a duplicate user to chat."""
    initial_users = test_chat.user_ids.copy()
    test_chat.add_user(2)  # User 2 already exists
    assert test_chat.user_ids == sorted(initial_users + [2])


def test_chat_add_user_empty_list() -> None:
    """Test adding a user to empty chat."""
    empty_chat = Chat(
        id=1,
        user_ids=[],
        user_admin_ids=[],
        private=True,
        group_name="Empty Group",
        group_description="Empty Description",
        group_colour="#FFFFFF",
        default_avatar=True,
        current_message_id=1,
        last_message_read_id_chat=1,
        message_version=1,
        avatar_version=1,
    )
    empty_chat.add_user(1)
    assert empty_chat.user_ids == [1]


def test_chat_remove_user(test_chat: Chat) -> None:  # pylint: disable=redefined-outer-name
    """Test removing a user from chat."""
    test_chat.remove_user(2)
    assert 2 not in test_chat.user_ids
    assert 1 in test_chat.user_ids
    assert 3 in test_chat.user_ids


def test_chat_remove_user_not_found(test_chat: Chat) -> None:  # pylint: disable=redefined-outer-name
    """Test removing a non-existent user from chat."""
    initial_users = test_chat.user_ids.copy()
    test_chat.remove_user(999)  # User 999 doesn't exist
    assert test_chat.user_ids == initial_users


def test_chat_remove_user_empty_list() -> None:
    """Test removing a user from empty chat."""
    empty_chat = Chat(
        id=1,
        user_ids=[],
        user_admin_ids=[],
        private=True,
        group_name="Empty Group",
        group_description="Empty Description",
        group_colour="#FFFFFF",
        default_avatar=True,
        current_message_id=1,
        last_message_read_id_chat=1,
        message_version=1,
        avatar_version=1,
    )
    empty_chat.remove_user(1)
    assert empty_chat.user_ids == []


def test_chat_add_admin(test_chat: Chat) -> None:  # pylint: disable=redefined-outer-name
    """Test adding an admin to chat."""
    initial_admins = test_chat.user_admin_ids.copy()
    test_chat.add_admin(2)
    assert test_chat.user_admin_ids == sorted(initial_admins + [2])


def test_chat_add_admin_duplicate(test_chat: Chat) -> None:  # pylint: disable=redefined-outer-name
    """Test adding a duplicate admin to chat."""
    initial_admins = test_chat.user_admin_ids.copy()
    test_chat.add_admin(1)  # Admin 1 already exists
    assert test_chat.user_admin_ids == sorted(initial_admins + [1])


def test_chat_add_admin_empty_list() -> None:
    """Test adding an admin to empty chat."""
    empty_chat = Chat(
        id=1,
        user_ids=[],
        user_admin_ids=[],
        private=True,
        group_name="Empty Group",
        group_description="Empty Description",
        group_colour="#FFFFFF",
        default_avatar=True,
        current_message_id=1,
        last_message_read_id_chat=1,
        message_version=1,
        avatar_version=1,
    )
    empty_chat.add_admin(1)
    assert empty_chat.user_admin_ids == [1]


def test_chat_remove_admin(test_chat: Chat) -> None:  # pylint: disable=redefined-outer-name
    """Test removing an admin from chat."""
    test_chat.remove_admin(1)
    assert 1 not in test_chat.user_admin_ids
    assert test_chat.user_admin_ids == []


def test_chat_remove_admin_not_found(test_chat: Chat) -> None:  # pylint: disable=redefined-outer-name
    """Test removing a non-existent admin from chat."""
    initial_admins = test_chat.user_admin_ids.copy()
    test_chat.remove_admin(999)  # Admin 999 doesn't exist
    assert test_chat.user_admin_ids == initial_admins


def test_chat_remove_admin_empty_list() -> None:
    """Test removing an admin from empty chat."""
    empty_chat = Chat(
        id=1,
        user_ids=[],
        user_admin_ids=[],
        private=True,
        group_name="Empty Group",
        group_description="Empty Description",
        group_colour="#FFFFFF",
        default_avatar=True,
        current_message_id=1,
        last_message_read_id_chat=1,
        message_version=1,
        avatar_version=1,
    )
    empty_chat.remove_admin(1)
    assert empty_chat.user_admin_ids == []


def test_chat_group_avatar_filename(test_chat: Chat) -> None:  # pylint: disable=redefined-outer-name
    """Test group avatar filename generation."""
    filename = test_chat.group_avatar_filename()
    assert len(filename) == 32  # MD5 hash length
    assert isinstance(filename, str)


def test_chat_group_avatar_filename_default(test_chat: Chat) -> None:  # pylint: disable=redefined-outer-name
    """Test group avatar default filename generation."""
    filename = test_chat.group_avatar_filename_default()
    assert len(filename) == 40  # MD5 hash length (32) + "_default" (8)
    assert filename.endswith("_default")


def test_chat_group_avatar_s3_key(test_chat: Chat) -> None:  # pylint: disable=redefined-outer-name
    """Test group avatar S3 key generation."""
    s3_key = test_chat.group_avatar_s3_key("test_filename")
    expected_key = "age_of_gold/avatars/group/test_filename.png"
    assert s3_key == expected_key


def test_chat_remove_group_avatar_error_handling(test_chat: Chat, mocker) -> None:  # pylint: disable=redefined-outer-name
    """Test error handling in remove_group_avatar method."""
    # Mock s3_client and ClientError
    mock_s3_client = mocker.MagicMock()
    mock_error = ClientError(
        error_response={"Error": {"Code": "SomeError", "Message": "Test error"}},
        operation_name="delete_object",
    )
    mock_s3_client.delete_object.side_effect = mock_error

    # This should not raise an exception, just log the error
    test_chat.remove_group_avatar(mock_s3_client)

    # Verify the delete_object was called
    mock_s3_client.delete_object.assert_called_once()


def test_chat_remove_group_avatar_default_error_handling(
    test_chat: Chat,  # pylint: disable=redefined-outer-name
    mocker,
) -> None:
    """Test error handling in remove_group_avatar_default method."""
    # Mock s3_client and ClientError
    mock_s3_client = mocker.MagicMock()
    mock_error = ClientError(
        error_response={"Error": {"Code": "SomeError", "Message": "Test error"}},
        operation_name="delete_object",
    )
    mock_s3_client.delete_object.side_effect = mock_error

    # This should not raise an exception, just log the error
    test_chat.remove_group_avatar_default(mock_s3_client)

    # Verify the delete_object was called
    mock_s3_client.delete_object.assert_called_once()
