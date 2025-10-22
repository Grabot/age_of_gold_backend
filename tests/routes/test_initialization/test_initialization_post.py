"""Test for initialization endpoint via direct get call."""

# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from main import app  # pylint: disable=C0413


@pytest.mark.asyncio
@patch("os.path.exists", return_value=True)
@patch("src.celery_worker.tasks.task_initialize.delay")
async def test_successful_initialization_get(
    mock_task_initialize_delay: MagicMock,
    mock_exists: MagicMock,
    test_setup: Generator[Any, Any, Any],
) -> None:
    """Test successful intialization via GET request."""
    with TestClient(app) as client:
        headers = {"Authorization": "Bearer valid_access_token"}
        response = client.get(
            "/api/v1.0/initialize",
            headers=headers,
        )
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["result"] is True


if __name__ == "__main__":
    pytest.main([__file__])
