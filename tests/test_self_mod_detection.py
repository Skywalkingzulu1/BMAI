import os
import tempfile
from pathlib import Path

import pytest

from app.self_mod_detection import (
    get_file_hash,
    write_hash_file,
    is_hash_modified,
    is_marker_modified,
)


@pytest.fixture
def temp_file():
    """Create a temporary file with known content."""
    with tempfile.TemporaryDirectory() as td:
        file_path = Path(td) / "sample.txt"
        file_path.write_text("initial content", encoding="utf-8")
        yield file_path


def test_hash_computation_consistency(temp_