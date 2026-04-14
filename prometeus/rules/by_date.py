from datetime import datetime
from pathlib import Path

from prometeus.rules.base import Rule


class ByDateRule(Rule):
    """Organizes files into date-based subdirectories.

    Args:
        fmt:    strftime format for the subdirectory name.
                Defaults to ``"%Y/%m"`` → ``2024/03/``.
        use:    Which timestamp to use: ``"mtime"`` (last modification,
                default) or ``"ctime"`` (creation / metadata change).
    """

    def __init__(self, fmt: str = "%Y/%m", use: str = "mtime") -> None:
        if use not in ("mtime", "ctime"):
            raise ValueError(f"use must be 'mtime' or 'ctime', got {use!r}")
        self._fmt = fmt
        self._use = use

    def resolve(self, file: Path) -> Path | None:
        stat = file.stat()
        ts = stat.st_mtime if self._use == "mtime" else stat.st_ctime
        folder = datetime.fromtimestamp(ts).strftime(self._fmt)
        return Path(folder) / file.name
