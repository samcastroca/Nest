"""Tests for conflict resolution helpers."""
from pathlib import Path

import pytest

import nest.conflict as conflict_mod
from nest.conflict import resolve_raw, _auto_rename


class TestAutoRename:
    def test_always_returns_renamed_path(self, tmp_path):
        # _auto_rename is only called when dest already exists;
        # it always returns a renamed candidate, never the original.
        dest = tmp_path / "file.txt"
        dest.write_text("x")
        assert _auto_rename(dest) == tmp_path / "file_1.txt"

    def test_adds_suffix_when_exists(self, tmp_path):
        dest = tmp_path / "file.txt"
        dest.write_text("x")
        renamed = _auto_rename(dest)
        assert renamed == tmp_path / "file_1.txt"

    def test_increments_suffix(self, tmp_path):
        dest = tmp_path / "file.txt"
        dest.write_text("x")
        (tmp_path / "file_1.txt").write_text("x")
        renamed = _auto_rename(dest)
        assert renamed == tmp_path / "file_2.txt"


class TestResolveRaw:
    def setup_method(self):
        conflict_mod.reset_global()

    def test_no_conflict_returns_dest(self, tmp_path):
        src = tmp_path / "src.txt"
        dest = tmp_path / "dest.txt"
        src.write_text("x")
        result = resolve_raw(src, dest, interactive=False)
        assert result == dest

    def test_non_interactive_auto_renames(self, tmp_path):
        src = tmp_path / "file.txt"
        src.write_text("new")
        dest = tmp_path / "file.txt"
        dest.write_text("old")
        result = resolve_raw(src, dest, interactive=False)
        assert result == tmp_path / "file_1.txt"
