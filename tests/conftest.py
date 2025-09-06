

import os
from pathlib import Path
import pytest

@pytest.fixture(autouse=True)
def _reset_cwd():
    """Run each test from the repo root so relative paths resolve.

    Some tests rely on paths like 'tests/fixtures/...' or 'seeds/...'.
    Other tests may chdir into a tmp directory. This fixture standardizes
    the working directory for every test and restores it afterwards.
    """
    repo_root = Path(__file__).resolve().parent.parent
    old_cwd = Path.cwd()
    os.chdir(repo_root)
    try:
        yield
    finally:
        os.chdir(old_cwd)