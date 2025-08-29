# ruff: noqa: E402, F401, F811
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

import time
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.api_v1.authorization.logout import logout_user
from app.models.user import User
from app.models.user_token import UserToken
from main import app
from tests.conftest import AsyncTestingSessionLocal, test_setup

if __name__ == "__main__":
    pytest.main([__file__])
