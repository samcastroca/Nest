"""Tests for individual rule implementations."""
import time
from pathlib import Path

import pytest

from prometeus.rules.by_extension import ByExtensionRule
from prometeus.rules.by_date import ByDateRule
from prometeus.rules.custom import CustomRule, RuleSpec


# ---------------------------------------------------------------------------
# ByExtensionRule
# ---------------------------------------------------------------------------

class TestByExtensionRule:
    def test_known_extension_returns_correct_category(self, tmp_path):
        (tmp_path / "photo.jpg").write_text("x")
        result = ByExtensionRule().resolve(tmp_path / "photo.jpg")
        assert result == Path("Images/photo.jpg")

    def test_pdf_goes_to_documents(self, tmp_path):
        (tmp_path / "doc.pdf").write_text("x")
        result = ByExtensionRule().resolve(tmp_path / "doc.pdf")
        assert result == Path("Documents/doc.pdf")

    def test_unknown_extension_goes_to_other(self, tmp_path):
        (tmp_path / "file.xyz").write_text("x")
        result = ByExtensionRule().resolve(tmp_path / "file.xyz")
        assert result == Path("Other/file.xyz")

    def test_custom_categories_override_default(self, tmp_path):
        (tmp_path / "file.jpg").write_text("x")
        rule = ByExtensionRule(categories={"Fotos": ["jpg"]})
        result = rule.resolve(tmp_path / "file.jpg")
        assert result == Path("Fotos/file.jpg")

    def test_case_insensitive_extension(self, tmp_path):
        (tmp_path / "IMAGE.PNG").write_text("x")
        result = ByExtensionRule().resolve(tmp_path / "IMAGE.PNG")
        assert result == Path("Images/IMAGE.PNG")


# ---------------------------------------------------------------------------
# ByDateRule
# ---------------------------------------------------------------------------

class TestByDateRule:
    def test_default_format_produces_year_month(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("x")
        rule = ByDateRule(fmt="%Y/%m", use="mtime")
        result = rule.resolve(f)
        # Should be e.g. Path("2024/03/file.txt")
        assert result is not None
        parts = result.parts
        assert len(parts) == 3  # year / month / filename
        assert parts[2] == "file.txt"

    def test_custom_format(self, tmp_path):
        f = tmp_path / "doc.pdf"
        f.write_text("x")
        rule = ByDateRule(fmt="%Y", use="mtime")
        result = rule.resolve(f)
        assert result is not None
        assert result.parts[1] == "doc.pdf"

    def test_invalid_use_raises(self):
        with pytest.raises(ValueError):
            ByDateRule(use="birthtime")


# ---------------------------------------------------------------------------
# CustomRule
# ---------------------------------------------------------------------------

class TestCustomRule:
    def _make_file(self, tmp_path, name):
        f = tmp_path / name
        f.write_text("x")
        return f

    def test_glob_pattern_match(self, tmp_path):
        rule = CustomRule([RuleSpec(name="PDFs", pattern="*.pdf", destination="Docs")])
        f = self._make_file(tmp_path, "report.pdf")
        assert rule.resolve(f) == Path("Docs/report.pdf")

    def test_glob_no_match_returns_none(self, tmp_path):
        rule = CustomRule([RuleSpec(name="PDFs", pattern="*.pdf", destination="Docs")])
        f = self._make_file(tmp_path, "photo.jpg")
        assert rule.resolve(f) is None

    def test_regex_match_filter(self, tmp_path):
        rule = CustomRule([
            RuleSpec(name="Invoices", pattern="*.pdf", match="invoice|factura", destination="Invoices")
        ])
        assert rule.resolve(self._make_file(tmp_path, "invoice_2024.pdf")) == Path("Invoices/invoice_2024.pdf")
        assert rule.resolve(self._make_file(tmp_path, "report.pdf")) is None

    def test_from_dict(self, tmp_path):
        data = {
            "rules": [
                {"name": "Imgs", "pattern": "*.jpg", "destination": "Images/"}
            ]
        }
        rule = CustomRule.from_dict(data)
        f = self._make_file(tmp_path, "cat.jpg")
        assert rule.resolve(f) == Path("Images/cat.jpg")

    def test_first_matching_rule_wins(self, tmp_path):
        rule = CustomRule([
            RuleSpec(name="A", pattern="*.pdf", destination="A"),
            RuleSpec(name="B", pattern="*.pdf", destination="B"),
        ])
        f = self._make_file(tmp_path, "file.pdf")
        assert rule.resolve(f) == Path("A/file.pdf")
