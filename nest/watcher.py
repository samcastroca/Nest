"""File-system watcher powered by watchdog."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Sequence

from rich.console import Console
from watchdog.events import FileCreatedEvent, FileMovedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from nest.rules.base import Rule
from nest.organizer import _first_match
import shutil
import nest.conflict as conflict_mod

console = Console()


class _Handler(FileSystemEventHandler):
    def __init__(self, source_dir: Path, rules: Sequence[Rule]) -> None:
        super().__init__()
        self._source_dir = source_dir
        self._rules = rules

    def _handle_path(self, src_path: str) -> None:
        file = Path(src_path)

        # Ignore directories and files inside already-organized subdirectories.
        if not file.is_file():
            return
        # Skip files that are not direct children of the watched dir (already organized).
        if file.parent != self._source_dir:
            return

        dest_rel = _first_match(file, self._rules)
        if dest_rel is None:
            return

        dest_abs = self._source_dir / dest_rel
        dest_abs.parent.mkdir(parents=True, exist_ok=True)

        final_dest = conflict_mod.resolve_raw(file, dest_abs, interactive=False)
        if final_dest is None:
            console.print(f"  [yellow]skipped[/yellow] {file.name} (conflict)")
            return

        try:
            shutil.move(str(file), str(final_dest))
            console.print(
                f"  [green]moved[/green]   {file.name} → "
                f"{final_dest.relative_to(self._source_dir)}"
            )
        except OSError as exc:
            console.print(f"  [red]error[/red]   {file.name}: {exc}")

    def on_created(self, event: FileCreatedEvent) -> None:  # type: ignore[override]
        if not event.is_directory:
            # Small delay to let the file finish writing before moving it.
            time.sleep(0.5)
            self._handle_path(event.src_path)

    def on_moved(self, event: FileMovedEvent) -> None:  # type: ignore[override]
        if not event.is_directory:
            self._handle_path(event.dest_path)


def start_watcher(source_dir: Path, rules: Sequence[Rule]) -> None:
    """Block until Ctrl+C, organizing new files as they appear."""
    observer = Observer()
    handler = _Handler(source_dir, rules)
    observer.schedule(handler, str(source_dir), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
        console.print("\n[dim]Watcher stopped.[/dim]")
