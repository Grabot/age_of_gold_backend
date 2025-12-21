"""Test for delete account endpoint via direct function call."""

from typing import Any, Tuple
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.settings import delete_account
from sqlmodel import select
from src.models.user import User, hash_email
from src.models.user_token import UserToken
from tests.conftest import add_token, add_user


@pytest.mark.asyncio
async def test_successful_delete_account_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful delete account via direct function call."""
    test_user_1 = await add_user(
        "testuser1", 1, test_db, "example.com", "testuser1@example.com"
    )
    await test_db.refresh(test_user_1)
    _, test_user_token_1 = await add_token(1000, 1000, test_db, test_user_1.id)
    test_user_id = test_user_1.id
    await test_db.refresh(test_user_token_1)
    auth: Tuple[User, UserToken] = (test_user_1, test_user_token_1)
    response_json: dict[str, Any] = await delete_account.delete_account(auth, test_db)

    assert response_json["success"]
    test_user_result = await test_db.get(User, test_user_id)
    assert test_user_result is None
    tokens_result = await test_db.execute(
        select(UserToken).where(UserToken.user_id == test_user_id)
    )
    assert tokens_result.scalars().all() == []


@pytest.mark.asyncio
async def test_successful_delete_account_all_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful delete account all via direct function call."""
    test_user_0 = await add_user(
        "testuser0", 1, test_db, "example.com", "testuserdelete@example.com"
    )
    await test_db.refresh(test_user_0)
    _, test_user_token_0 = await add_token(1000, 1000, test_db, test_user_0.id)
    test_user_id = test_user_0.id
    await test_db.refresh(test_user_token_0)
    test_user_1 = await add_user(
        "testuser1", 1, test_db, "example.com", "testuserdelete@example.com"
    )
    test_user_2 = await add_user(
        "testuser2", 2, test_db, "example.com", "testuserdelete@example.com"
    )
    test_user_3 = await add_user(
        "testuser3", 3, test_db, "example.com", "testuserdelete@example.com"
    )
    test_user_4 = await add_user(
        "testuser4", 4, test_db, "example.com", "testuserdelete@example.com"
    )
    await test_db.refresh(test_user_1)
    await test_db.refresh(test_user_2)
    await test_db.refresh(test_user_3)
    await test_db.refresh(test_user_4)
    test_user_id = test_user_0.id
    auth: Tuple[User, UserToken] = (test_user_0, test_user_token_0)
    response_json: dict[str, Any] = await delete_account.delete_account_all(
        auth, test_db
    )

    assert response_json["success"]
    test_user_result = await test_db.get(User, test_user_id)
    assert test_user_result is None
    users_result = await test_db.execute(
        select(User).where(User.email_hash == hash_email("testuserdelete@example.com"))
    )
    assert users_result.scalars().all() == []


@pytest.mark.asyncio
@patch(
    "age_of_gold_worker.age_of_gold_worker.tasks.task_send_email_delete_account.delay"
)
async def test_successful_delete_account_request_direct(
    mock_task_send_email_delete_account: MagicMock,
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful delete account request via direct function call."""
    test_user_request = await add_user(
        "testuserrequest", 1, test_db, "example.com", "testuserrequest@example.com"
    )
    await test_db.refresh(test_user_request)
    delete_account_request: delete_account.DeleteAccountRequest = (
        delete_account.DeleteAccountRequest(email="testuserrequest@example.com")
    )
    response_json: dict[str, Any] = await delete_account.delete_account_request_call(
        delete_account_request, test_db
    )

    mock_task_send_email_delete_account.assert_called_once()
    assert response_json["success"]


@pytest.mark.asyncio
async def test_delete_account_request_no_account(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test delete account request no account via direct function call."""
    delete_account_request: delete_account.DeleteAccountRequest = (
        delete_account.DeleteAccountRequest(email="testuserdelete@example.com")
    )
    with pytest.raises(HTTPException) as exc_info:
        await delete_account.delete_account_request_call(
            delete_account_request, test_db
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "No account found with this email"
