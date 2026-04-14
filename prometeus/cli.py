"""Prometeus CLI — entry point."""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

app = typer.Typer(
    name="prometeus",
    help="Organize files by extension, date, name, or custom rules.",
    add_completion=True,
)
config_app = typer.Typer(help="Manage Prometeus configuration.")
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
    from prometeus.rules.base import Rule
    from prometeus.rules.by_extension import ByExtensionRule
    from prometeus.rules.by_date import ByDateRule
    from prometeus.config import load_custom_rules
    from prometeus.organizer import organize

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
    from prometeus.rules.base import Rule
    from prometeus.rules.by_extension import ByExtensionRule
    from prometeus.rules.by_date import ByDateRule
    from prometeus.config import load_custom_rules
    from prometeus.watcher import start_watcher

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
    from prometeus.config import EXAMPLE_CONFIG

    if output.exists():
        overwrite = typer.confirm(f"{output} already exists. Overwrite?", default=False)
        if not overwrite:
            raise typer.Exit()

    output.write_text(EXAMPLE_CONFIG, encoding="utf-8")
    console.print(f"[green]Created[/green] {output}")
    console.print("[dim]Edit the file and use it with: prometeus sort <path> --config rules.yaml[/dim]")
