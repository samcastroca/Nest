"""Configuration loading for Prometeus."""
from __future__ import annotations

from pathlib import Path

import yaml

from prometeus.rules.custom import CustomRule


def load_custom_rules(config_path: Path) -> CustomRule:
    """Parse a YAML config file and return a :class:`CustomRule` instance."""
    with config_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return CustomRule.from_dict(data)


EXAMPLE_CONFIG = """\
# Prometeus custom rules
# Rules are evaluated in order; the first match wins.
#
# Fields:
#   name:        Human-readable label (shown in logs)
#   pattern:     Glob matched against the filename  (e.g. "*.pdf")
#   match:       Optional regex matched against the filename (case-insensitive)
#   destination: Target subdirectory  (relative to the source folder)

rules:
  - name: "Facturas"
    pattern: "*.pdf"
    match: "factura|invoice"
    destination: "Facturas/"

  - name: "Screenshots"
    pattern: "Screenshot*.png"
    destination: "Capturas/Screenshots"

  - name: "Datasets CSV"
    pattern: "*.csv"
    destination: "Datasets/"
"""
