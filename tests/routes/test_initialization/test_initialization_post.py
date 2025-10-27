"""Test for initialization endpoint via direct get call."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from tests.helpers import assert_successful_response


@pytest.mark.asyncio
@patch("os.path.exists", return_value=True)
@patch("src.celery_worker.tasks.task_initialize.delay")
async def test_successful_initialization_get(
    mock_task_initialize_delay: MagicMock,
    mock_exists: MagicMock,
    test_setup: TestClient,
) -> None:
    """Test successful intialization via GET request."""
    with TestClient(app) as client:
        headers = {"Authorization": "Bearer valid_access_token"}
        response = client.get(
            "/api/v1.0/initialize",
            headers=headers,
        )
        assert_successful_response(response)
