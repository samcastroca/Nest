"""Core file organization engine."""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from rich.console import Console
from rich.table import Table

from nest.rules.base import Rule
import nest.conflict as conflict_mod
import nest.log as log_mod

console = Console()


@dataclass
class MoveResult:
    """Outcome for a single file."""
    source: Path
    destination: Path | None  # None means skipped
    skipped: bool = False
    conflict: bool = False
    error: str | None = None


@dataclass
class OrganizeReport:
    moved: list[MoveResult] = field(default_factory=list)
    skipped: list[MoveResult] = field(default_factory=list)
    errors: list[MoveResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.moved) + len(self.skipped) + len(self.errors)


def organize(
    source_dir: Path,
    rules: Sequence[Rule],
    *,
    dry_run: bool = False,
    recursive: bool = False,
    interactive: bool = True,
) -> OrganizeReport:
    """Organize files in *source_dir* applying *rules* in order.

    Args:
        source_dir:   Directory to scan.
        rules:        Ordered list of :class:`~nest.rules.base.Rule`.
                      First match wins.
        dry_run:      If ``True``, print planned moves without touching disk.
        recursive:    Descend into subdirectories.
        interactive:  Prompt the user on conflicts (pass ``False`` for
                      non-interactive / watch-mode use).
    """
    conflict_mod.reset_global()
    report = OrganizeReport()

    pattern = "**/*" if recursive else "*"
    files = [f for f in source_dir.glob(pattern) if f.is_file()
             if f.name != log_mod.LOG_FILENAME]

    if dry_run:
        _print_dry_run(source_dir, files, rules)
        return report

    session_id = log_mod.new_session_id()
    completed_moves: list[tuple[Path, Path]] = []

    for file in files:
        dest_rel = _first_match(file, rules)
        if dest_rel is None:
            result = MoveResult(source=file, destination=None, skipped=True)
            report.skipped.append(result)
            continue

        dest_abs = source_dir / dest_rel
        dest_abs.parent.mkdir(parents=True, exist_ok=True)

        try:
            final_dest = conflict_mod.resolve_raw(file, dest_abs, interactive=interactive)
        except SystemExit:
            break

        if final_dest is None:
            result = MoveResult(source=file, destination=None, skipped=True, conflict=True)
            report.skipped.append(result)
            console.print(f"  [yellow]skipped[/yellow] {file.name}")
            continue

        try:
            shutil.move(str(file), str(final_dest))
            result = MoveResult(source=file, destination=final_dest, conflict=(final_dest != dest_abs))
            report.moved.append(result)
            completed_moves.append((file, final_dest))
            console.print(f"  [green]moved[/green]   {file.name} → {final_dest.relative_to(source_dir)}")
        except OSError as exc:
            result = MoveResult(source=file, destination=None, error=str(exc))
            report.errors.append(result)
            console.print(f"  [red]error[/red]   {file.name}: {exc}")

    if completed_moves:
        log_mod.record_session(source_dir, session_id, completed_moves)
        console.print(f"[dim]Session logged as {session_id}[/dim]")

    _print_summary(report)
    return report


def _first_match(file: Path, rules: Sequence[Rule]) -> Path | None:
    for rule in rules:
        dest = rule.resolve(file)
        if dest is not None:
            return dest
    return None


def _print_dry_run(source_dir: Path, files: list[Path], rules: Sequence[Rule]) -> None:
    table = Table(title=f"Dry run — {source_dir}", show_lines=False)
    table.add_column("File", style="cyan", no_wrap=True)
    table.add_column("→ Destination", style="green")

    for file in files:
        dest = _first_match(file, rules)
        dest_str = str(dest) if dest else "[dim]no rule matched — skip[/dim]"
        table.add_row(file.name, dest_str)

    console.print(table)
    console.print(f"[dim]{len(files)} file(s) listed (no changes made)[/dim]")


def _print_summary(report: OrganizeReport) -> None:
    console.print(
        f"\n[bold]Done.[/bold] "
        f"Moved: [green]{len(report.moved)}[/green]  "
        f"Skipped: [yellow]{len(report.skipped)}[/yellow]  "
        f"Errors: [red]{len(report.errors)}[/red]"
    )
