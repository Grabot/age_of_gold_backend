# ruff: noqa: E402
import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.append(str(current_dir.parent.parent))

import filecmp
import os

import pytest

from app.util.avatar import generate_avatar


def test_generate_avatar() -> None:
    test_path = os.path.join(current_dir.parent, "data")

    generate_avatar(file_name="test", file_path=str(test_path))

    generated_avatar_path = os.path.join(test_path, "test_default.png")
    default_avatar_path = os.path.join(test_path, "test_default_copy.png")

    assert filecmp.cmp(
        str(generated_avatar_path), str(default_avatar_path), shallow=False
    ), "The generated avatar does not match the default avatar"

    os.remove(str(generated_avatar_path))


if __name__ == "__main__":
    pytest.main([__file__])
