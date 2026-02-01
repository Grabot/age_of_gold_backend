"""Test for change colour endpoint via direct function call."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

from src.api.api_v1.settings.change_colour import ChangeColourRequest, change_colour
from src.models.user import User


@pytest.mark.asyncio
async def test_successful_change_colour_direct(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    """Test successful change colour via direct function call."""
    from tests.conftest import add_token

    test_user, user_token = await add_token(1000, 1000, test_db)
    test_user_id = test_user.id
    original_colour = test_user.colour
    original_profile_version = test_user.profile_version

    auth = (test_user, user_token)
    new_colour = "#FF5733"
    change_colour_request = ChangeColourRequest(new_colour=new_colour)

    result = await change_colour(change_colour_request, auth, test_db)

    assert result["success"] is True

    # Verify the user's colour was updated in the database
    test_user_result = await test_db.get(User, test_user_id)
    assert test_user_result is not None
    assert test_user_result.colour != original_colour
    assert test_user_result.colour == new_colour
    assert test_user_result.profile_version == original_profile_version + 1
