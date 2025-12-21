"""Test for initialization endpoint via direct get call."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from main import app
from src.config.config import settings


@pytest.mark.asyncio
@patch("os.path.exists", return_value=True)
@patch("age_of_gold_worker.age_of_gold_worker.tasks.task_initialize.delay")
async def test_successful_initialization_get(
    mock_task_initialize_delay: MagicMock,
    mock_exists: MagicMock,
    test_setup: TestClient,
) -> None:
    """Test successful intialization via GET request."""
    with TestClient(app) as client:
        headers = {"Authorization": "Bearer valid_access_token"}
        response = client.get(
            f"{settings.API_V1_STR}/initialize",
            headers=headers,
        )
        assert response.status_code == status.HTTP_200_OK
        response_dict = response.json()
        assert "success" in response_dict
        assert response_dict["success"]
