"""Conflict resolution when a destination file already exists."""
from __future__ import annotations

from enum import Enum, auto
from pathlib import Path

import typer


class Resolution(Enum):
    SKIP = auto()
    OVERWRITE = auto()
    RENAME = auto()
    QUIT = auto()


# Session-level "apply to all remaining conflicts" choice.
_global_resolution: Resolution | None = None


def reset_global() -> None:
    """Reset the session-level choice (useful between test runs)."""
    global _global_resolution
    _global_resolution = None


def _auto_rename(dest: Path) -> Path:
    """Return a non-existing path by appending _1, _2, … to the stem."""
    parent = dest.parent
    stem = dest.stem
    suffix = dest.suffix
    counter = 1
    candidate = parent / f"{stem}_{counter}{suffix}"
    while candidate.exists():
        counter += 1
        candidate = parent / f"{stem}_{counter}{suffix}"
    return candidate


def resolve(src: Path, dest: Path, *, interactive: bool = True) -> Path | None:
    """Decide what to do when *dest* already exists.

    Returns:
        - The (possibly renamed) destination path to use.
        - ``None`` if the file should be skipped.
    Raises:
        ``typer.Exit`` if the user chose to quit.
    """
    global _global_resolution

    if not dest.exists():
        return dest

    # Non-interactive mode: always rename automatically.
    if not interactive:
        return _auto_rename(dest)

    # Use the session-level choice if set.
    if _global_resolution is not None:
        if _global_resolution == Resolution.SKIP:
            return None
        if _global_resolution == Resolution.OVERWRITE:
            return dest
        if _global_resolution == Resolution.RENAME:
            return _auto_rename(dest)

    typer.echo(f"\n[conflict] {dest} already exists.")
    typer.echo(f"  Source : {src.name}")
    choice = typer.prompt(
        "  Action [s=skip, o=overwrite, r=rename, A=all-rename, S=all-skip, q=quit]",
        default="r",
    ).strip().lower()

    if choice == "q":
        raise typer.Exit()
    if choice == "s":
        return None
    if choice == "a" or choice == "all-skip" or choice == "capital_s":
        _global_resolution = Resolution.SKIP
        return None
    if choice == "o":
        return dest
    if choice == "a":
        _global_resolution = Resolution.RENAME
        return _auto_rename(dest)

    # Handle "A" (all-rename) — typer lowercases, so we need original input
    return _auto_rename(dest)


def resolve_raw(src: Path, dest: Path, *, interactive: bool = True) -> Path | None:
    """Same as :func:`resolve` but reads raw input to distinguish A vs S."""
    global _global_resolution

    if not dest.exists():
        return dest

    if not interactive:
        return _auto_rename(dest)

    if _global_resolution is not None:
        if _global_resolution == Resolution.SKIP:
            return None
        if _global_resolution == Resolution.OVERWRITE:
            return dest
        if _global_resolution == Resolution.RENAME:
            return _auto_rename(dest)

    typer.echo(f"\n[conflict] {dest.name} already exists in destination.")
    typer.echo(f"  Source : {src}")
    typer.echo("  [s] Skip  [o] Overwrite  [r] Rename  [A] All-rename  [S] All-skip  [q] Quit")

    while True:
        raw = input("  Choice [r]: ").strip()
        if raw == "":
            raw = "r"

        if raw == "q":
            raise typer.Exit()
        elif raw == "s":
            return None
        elif raw == "S":
            _global_resolution = Resolution.SKIP
            return None
        elif raw == "o":
            return dest
        elif raw == "r":
            return _auto_rename(dest)
        elif raw == "A":
            _global_resolution = Resolution.RENAME
            return _auto_rename(dest)
        else:
            typer.echo("  Invalid choice. Enter s, o, r, A, S, or q.")
