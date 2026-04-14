"""Shared fixtures for Nest tests."""
from pathlib import Path

import pytest


@pytest.fixture()
def sample_dir(tmp_path: Path) -> Path:
    """A temporary directory with a handful of test files."""
    files = [
        "photo.jpg",
        "report.pdf",
        "spreadsheet.xlsx",
        "archive.zip",
        "script.py",
        "data.csv",
        "video.mp4",
        "song.mp3",
        "unknown.xyz",
    ]
    for name in files:
        (tmp_path / name).write_text(f"content of {name}")
    return tmp_path
