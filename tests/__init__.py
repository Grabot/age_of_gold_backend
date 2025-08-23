import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


import pytest

if __name__ == "__main__":
    pytest.main(["tests/test_login.py"])
