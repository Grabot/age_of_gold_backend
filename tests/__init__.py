"""Main file for tests"""

import sys
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).parent.parent))

# An example of how to run a specific test
if __name__ == "__main__":
    pytest.main(["tests/routes/authorization/test_login/test_login_direct.py"])
