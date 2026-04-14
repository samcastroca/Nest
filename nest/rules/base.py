from abc import ABC, abstractmethod
from pathlib import Path


class Rule(ABC):
    """Base class for all file organization rules.

    Each rule inspects a file path and returns a *relative* destination
    path (e.g. ``Images/photo.jpg``) or ``None`` if the rule does not
    apply to that file.
    """

    @abstractmethod
    def resolve(self, file: Path) -> Path | None:
        """Return the relative destination path for *file*, or None."""
