"""Custom rules loaded from a YAML/JSON config file.

Each entry in the ``rules`` list supports:

    name:        (str)  Human-readable label shown in logs.
    pattern:     (str)  Glob pattern matched against the filename only
                        (e.g. "*.pdf", "Screenshot*").
    match:       (str, optional)  Additional regex matched against the
                 filename (case-insensitive).  The rule only fires when
                 BOTH pattern and match agree.
    destination: (str)  Relative folder path (e.g. "Facturas/").

Rules are evaluated in list order; the first match wins.
"""
from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path

from nest.rules.base import Rule


@dataclass
class RuleSpec:
    name: str
    pattern: str
    destination: str
    match: str | None = None

    # Compiled regex (populated lazily)
    _regex: re.Pattern | None = None

    def __post_init__(self) -> None:
        if self.match:
            self._regex = re.compile(self.match, re.IGNORECASE)


class CustomRule(Rule):
    """Applies a list of user-defined :class:`RuleSpec` entries in order."""

    def __init__(self, specs: list[RuleSpec]) -> None:
        self._specs = specs

    @classmethod
    def from_dict(cls, data: dict) -> "CustomRule":
        """Build from the parsed contents of a rules YAML file."""
        specs = []
        for entry in data.get("rules", []):
            specs.append(
                RuleSpec(
                    name=entry.get("name", ""),
                    pattern=entry["pattern"],
                    destination=entry["destination"].rstrip("/"),
                    match=entry.get("match"),
                )
            )
        return cls(specs)

    def resolve(self, file: Path) -> Path | None:
        name = file.name
        for spec in self._specs:
            if not fnmatch.fnmatch(name, spec.pattern):
                continue
            if spec._regex and not spec._regex.search(name):
                continue
            return Path(spec.destination) / name
        return None
