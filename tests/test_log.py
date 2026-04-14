"""Tests for the session log module."""
import json
from pathlib import Path

import pytest

from prometeus.log import (
    LOG_FILENAME,
    new_session_id,
    record_session,
    list_sessions,
    get_session,
    remove_session,
)


class TestNewSessionId:
    def test_format(self):
        sid = new_session_id()
        # e.g. "20240315_103045_a1b2c3"
        parts = sid.split("_")
        assert len(parts) == 3
        assert len(parts[0]) == 8   # YYYYMMDD
        assert len(parts[1]) == 6   # HHMMSS
        assert len(parts[2]) == 6   # hex

    def test_unique(self):
        assert new_session_id() != new_session_id()


class TestRecordSession:
    def test_creates_log_file(self, tmp_path):
        src = tmp_path / "file.jpg"
        dst = tmp_path / "Images" / "file.jpg"
        src.write_text("x")
        dst.parent.mkdir()
        dst.write_text("x")

        record_session(tmp_path, "sess1", [(src, dst)])
        assert (tmp_path / LOG_FILENAME).exists()

    def test_log_content(self, tmp_path):
        src = tmp_path / "doc.pdf"
        dst = tmp_path / "Documents" / "doc.pdf"
        src.write_text("x")
        dst.parent.mkdir()
        dst.write_text("x")

        record_session(tmp_path, "sess1", [(src, dst)])
        data = json.loads((tmp_path / LOG_FILENAME).read_text())

        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["id"] == "sess1"
        assert data["sessions"][0]["moves"][0]["from"] == "doc.pdf"
        assert data["sessions"][0]["moves"][0]["to"] == str(Path("Documents/doc.pdf"))

    def test_empty_moves_does_not_write(self, tmp_path):
        record_session(tmp_path, "sess1", [])
        assert not (tmp_path / LOG_FILENAME).exists()

    def test_multiple_sessions_accumulate(self, tmp_path):
        for i, name in enumerate(["a.jpg", "b.pdf"]):
            src = tmp_path / name
            dst = tmp_path / "Cat" / name
            src.write_text("x")
            dst.parent.mkdir(exist_ok=True)
            dst.write_text("x")
            record_session(tmp_path, f"sess{i}", [(src, dst)])

        data = json.loads((tmp_path / LOG_FILENAME).read_text())
        assert len(data["sessions"]) == 2


class TestListSessions:
    def test_empty_dir_returns_empty(self, tmp_path):
        assert list_sessions(tmp_path) == []

    def test_returns_newest_first(self, tmp_path):
        for i, name in enumerate(["a.jpg", "b.pdf"]):
            src = tmp_path / name
            dst = tmp_path / "Cat" / name
            src.write_text("x")
            dst.parent.mkdir(exist_ok=True)
            dst.write_text("x")
            record_session(tmp_path, f"sess{i}", [(src, dst)])

        sessions = list_sessions(tmp_path)
        assert sessions[0]["id"] == "sess1"
        assert sessions[1]["id"] == "sess0"


class TestGetSession:
    def test_found(self, tmp_path):
        src = tmp_path / "file.jpg"
        dst = tmp_path / "Images" / "file.jpg"
        src.write_text("x")
        dst.parent.mkdir()
        dst.write_text("x")
        record_session(tmp_path, "my-session", [(src, dst)])

        session = get_session(tmp_path, "my-session")
        assert session is not None
        assert session["id"] == "my-session"

    def test_not_found_returns_none(self, tmp_path):
        assert get_session(tmp_path, "nonexistent") is None


class TestRemoveSession:
    def test_removes_correct_session(self, tmp_path):
        for i, name in enumerate(["a.jpg", "b.pdf"]):
            src = tmp_path / name
            dst = tmp_path / "Cat" / name
            src.write_text("x")
            dst.parent.mkdir(exist_ok=True)
            dst.write_text("x")
            record_session(tmp_path, f"sess{i}", [(src, dst)])

        remove_session(tmp_path, "sess0")
        data = json.loads((tmp_path / LOG_FILENAME).read_text())
        ids = [s["id"] for s in data["sessions"]]
        assert "sess0" not in ids
        assert "sess1" in ids
