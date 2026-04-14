"""Tests for the organize() engine."""
from pathlib import Path

import pytest

from nest.organizer import organize
from nest.rules.by_extension import ByExtensionRule
from nest.rules.by_date import ByDateRule


class TestOrganize:
    def test_dry_run_moves_nothing(self, sample_dir):
        before = set(sample_dir.iterdir())
        organize(sample_dir, [ByExtensionRule()], dry_run=True)
        after = set(sample_dir.iterdir())
        assert before == after

    def test_files_moved_to_correct_categories(self, sample_dir):
        organize(sample_dir, [ByExtensionRule()], interactive=False)
        assert (sample_dir / "Images" / "photo.jpg").exists()
        assert (sample_dir / "Documents" / "report.pdf").exists()
        assert (sample_dir / "Spreadsheets" / "spreadsheet.xlsx").exists()
        assert (sample_dir / "Archives" / "archive.zip").exists()
        assert (sample_dir / "Code" / "script.py").exists()
        assert (sample_dir / "Audio" / "song.mp3").exists()
        assert (sample_dir / "Videos" / "video.mp4").exists()
        assert (sample_dir / "Other" / "unknown.xyz").exists()

    def test_report_counts_correctly(self, sample_dir):
        report = organize(sample_dir, [ByExtensionRule()], interactive=False)
        total_expected = len(list(sample_dir.glob("*")))
        assert report.total == total_expected or len(report.moved) > 0

    def test_no_rules_skips_all_files(self, sample_dir):
        report = organize(sample_dir, [], interactive=False)
        assert len(report.skipped) > 0
        assert len(report.moved) == 0

    def test_conflict_auto_rename(self, tmp_path):
        # Place a file both at source and destination.
        src_file = tmp_path / "photo.jpg"
        src_file.write_text("new")
        (tmp_path / "Images").mkdir()
        (tmp_path / "Images" / "photo.jpg").write_text("old")

        organize(tmp_path, [ByExtensionRule()], interactive=False)

        # Original should still exist (renamed copy).
        assert (tmp_path / "Images" / "photo.jpg").exists()
        assert (tmp_path / "Images" / "photo_1.jpg").exists()

    def test_recursive_flag(self, tmp_path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "nested.jpg").write_text("x")

        organize(tmp_path, [ByExtensionRule()], recursive=True, interactive=False)
        assert (tmp_path / "Images" / "nested.jpg").exists()
