"""Nest CLI — entry point."""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

app = typer.Typer(
    name="nest",
    help="Organize files by extension, date, name, or custom rules.",
    add_completion=True,
)
config_app = typer.Typer(help="Manage Nest configuration.")
app.add_typer(config_app, name="config")

console = Console()


class SortBy(str, Enum):
    extension = "extension"
    date = "date"


class DateUse(str, Enum):
    mtime = "mtime"
    ctime = "ctime"


# ---------------------------------------------------------------------------
# sort
# ---------------------------------------------------------------------------

@app.command()
def sort(
    path: Annotated[Path, typer.Argument(
        help="Directory to organize.",
        exists=True, file_okay=False, resolve_path=True,
    )],
    by: Annotated[Optional[SortBy], typer.Option(
        "--by", help="Primary sort strategy.",
    )] = None,
    config: Annotated[Optional[Path], typer.Option(
        "--config", "-c",
        help="YAML config file with custom rules (applied before --by).",
        exists=True, dir_okay=False, resolve_path=True,
    )] = None,
    date_format: Annotated[str, typer.Option(
        "--format", help="strftime format for --by date folders.",
    )] = "%Y/%m",
    date_use: Annotated[DateUse, typer.Option(
        "--use", help="Timestamp to use for --by date.",
    )] = DateUse.mtime,
    dry_run: Annotated[bool, typer.Option(
        "--dry-run", help="Preview moves without touching files.",
    )] = False,
    recursive: Annotated[bool, typer.Option(
        "--recursive", "-r", help="Descend into subdirectories.",
    )] = False,
    no_interactive: Annotated[bool, typer.Option(
        "--no-interactive", help="Auto-rename on conflict without prompting.",
    )] = False,
) -> None:
    """Organize files in PATH according to the chosen strategy."""
    from nest.rules.base import Rule
    from nest.rules.by_extension import ByExtensionRule
    from nest.rules.by_date import ByDateRule
    from nest.config import load_custom_rules
    from nest.organizer import organize

    rules: list[Rule] = []

    # Custom rules always take priority (applied first).
    if config:
        rules.append(load_custom_rules(config))
        console.print(f"[dim]Loaded custom rules from {config}[/dim]")

    if by == SortBy.extension:
        rules.append(ByExtensionRule())
    elif by == SortBy.date:
        rules.append(ByDateRule(fmt=date_format, use=date_use.value))
    elif by is None and not config:
        # No strategy given — default to extension-based sorting.
        console.print("[dim]No --by specified; defaulting to --by extension[/dim]")
        rules.append(ByExtensionRule())

    if not rules:
        typer.echo("No rules to apply. Use --by or --config.", err=True)
        raise typer.Exit(1)

    organize(
        path,
        rules,
        dry_run=dry_run,
        recursive=recursive,
        interactive=not no_interactive,
    )


# ---------------------------------------------------------------------------
# watch
# ---------------------------------------------------------------------------

@app.command()
def watch(
    path: Annotated[Path, typer.Argument(
        help="Directory to monitor.",
        exists=True, file_okay=False, resolve_path=True,
    )],
    by: Annotated[Optional[SortBy], typer.Option(
        "--by", help="Sort strategy for incoming files.",
    )] = SortBy.extension,
    config: Annotated[Optional[Path], typer.Option(
        "--config", "-c",
        help="YAML config file with custom rules.",
        exists=True, dir_okay=False, resolve_path=True,
    )] = None,
    date_format: Annotated[str, typer.Option(
        "--format", help="strftime format for --by date folders.",
    )] = "%Y/%m",
    date_use: Annotated[DateUse, typer.Option(
        "--use", help="Timestamp to use for --by date.",
    )] = DateUse.mtime,
) -> None:
    """Watch PATH and organize new files automatically. Press Ctrl+C to stop."""
    from nest.rules.base import Rule
    from nest.rules.by_extension import ByExtensionRule
    from nest.rules.by_date import ByDateRule
    from nest.config import load_custom_rules
    from nest.watcher import start_watcher

    rules: list[Rule] = []

    if config:
        rules.append(load_custom_rules(config))
        console.print(f"[dim]Loaded custom rules from {config}[/dim]")

    if by == SortBy.extension:
        rules.append(ByExtensionRule())
    elif by == SortBy.date:
        rules.append(ByDateRule(fmt=date_format, use=date_use.value))

    if not rules:
        rules.append(ByExtensionRule())

    console.print(f"[bold green]Watching[/bold green] {path}  (Ctrl+C to stop)")
    start_watcher(path, rules)


# ---------------------------------------------------------------------------
# undo
# ---------------------------------------------------------------------------

@app.command()
def undo(
    path: Annotated[Path, typer.Argument(
        help="Directory that was previously organized.",
        exists=True, file_okay=False, resolve_path=True,
    )],
    session: Annotated[Optional[str], typer.Option(
        "--session", "-s",
        help="Session ID to undo (defaults to the most recent session).",
    )] = None,
    list_sessions: Annotated[bool, typer.Option(
        "--list", "-l",
        help="List all available sessions without undoing anything.",
    )] = False,
    dry_run: Annotated[bool, typer.Option(
        "--dry-run", help="Preview what would be restored without moving files.",
    )] = False,
) -> None:
    """Restore files to their original locations using the session log."""
    import shutil
    from rich.table import Table
    from nest.log import list_sessions as get_sessions, get_session, remove_session, LOG_FILENAME

    sessions = get_sessions(path)

    if list_sessions:
        if not sessions:
            console.print("[yellow]No sessions recorded for this directory.[/yellow]")
            raise typer.Exit()
        table = Table(title=f"Sessions — {path}", show_lines=False)
        table.add_column("ID", style="cyan")
        table.add_column("Timestamp")
        table.add_column("Files moved", justify="right")
        for s in sessions:
            table.add_row(s["id"], s["timestamp"], str(len(s["moves"])))
        console.print(table)
        return

    if not sessions:
        console.print("[yellow]No sessions recorded for this directory.[/yellow]")
        raise typer.Exit(1)

    target_id = session or sessions[0]["id"]
    target = get_session(path, target_id)
    if target is None:
        console.print(f"[red]Session {target_id!r} not found.[/red]")
        raise typer.Exit(1)

    console.print(f"Undoing session [cyan]{target_id}[/cyan] ({target['timestamp']}) — "
                  f"{len(target['moves'])} file(s)")

    errors = 0
    restored = 0
    for entry in reversed(target["moves"]):
        src = path / entry["to"]    # where the file is now
        dst = path / entry["from"]  # where it should go back

        if not src.exists():
            console.print(f"  [yellow]missing[/yellow] {entry['to']} — skipped")
            continue

        if dry_run:
            console.print(f"  [dim]would restore[/dim] {entry['to']} → {entry['from']}")
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(src), str(dst))
            console.print(f"  [green]restored[/green] {entry['to']} → {entry['from']}")
            restored += 1
        except OSError as exc:
            console.print(f"  [red]error[/red]    {entry['to']}: {exc}")
            errors += 1

    if not dry_run:
        if errors == 0:
            remove_session(path, target_id)
        console.print(
            f"\n[bold]Done.[/bold] "
            f"Restored: [green]{restored}[/green]  Errors: [red]{errors}[/red]"
        )


# ---------------------------------------------------------------------------
# config init
# ---------------------------------------------------------------------------

@config_app.command("init")
def config_init(
    output: Annotated[Path, typer.Option(
        "--output", "-o",
        help="Where to write the example config file.",
    )] = Path("rules.yaml"),
) -> None:
    """Generate an example rules.yaml config file."""
    from nest.config import EXAMPLE_CONFIG

    if output.exists():
        overwrite = typer.confirm(f"{output} already exists. Overwrite?", default=False)
        if not overwrite:
            raise typer.Exit()

    output.write_text(EXAMPLE_CONFIG, encoding="utf-8")
    console.print(f"[green]Created[/green] {output}")
    console.print("[dim]Edit the file and use it with: nest sort <path> --config rules.yaml[/dim]")
