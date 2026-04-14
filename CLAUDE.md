# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**Nest** is a Python CLI tool that organizes files by extension, date, or user-defined rules. It supports one-shot sorting and real-time folder watching.

## Setup & Commands

```bash
# Install in editable mode (includes dev dependencies)
pip install -e ".[dev]"

# Run the CLI
nest --help
nest sort ~/Downloads --by extension --dry-run
nest sort ~/Downloads --by date --format "%Y/%m"
nest sort ~/Downloads --config rules.yaml --by extension
nest watch ~/Downloads --by extension
nest config init --output rules.yaml

# Run all tests
pytest tests/ -v

# Run a single test file
pytest tests/test_rules.py -v

# Run a single test
pytest tests/test_organizer.py::TestOrganize::test_dry_run_moves_nothing -v
```

## Architecture

```
nest/
├── cli.py          # Typer entry point — commands: sort, watch, config init
├── organizer.py    # organize() engine: iterates files, applies rules, moves files
├── conflict.py     # Interactive conflict resolution (skip/overwrite/rename/all)
├── config.py       # load_custom_rules() + EXAMPLE_CONFIG template string
└── rules/
    ├── base.py         # Abstract Rule: resolve(file) -> Path | None
    ├── by_extension.py # Groups by category (Images, Documents, …) via DEFAULT_CATEGORIES
    ├── by_date.py      # Subcategories YYYY/MM from mtime or ctime
    └── custom.py       # User-defined glob+regex rules loaded from YAML
```

### Rule pipeline

`organize()` calls `rules` in list order; the **first non-None result wins**.  
In `cli.py`, custom rules (from `--config`) are prepended, so they always have priority over `--by extension|date`.

### Conflict resolution

`conflict.resolve_raw()` handles the interactive prompt.  
A module-level `_global_resolution` variable holds the session choice (`A` = all-rename, `S` = all-skip) so the user only needs to answer once.  
Pass `interactive=False` for watch mode and tests.

### Watch mode

`watcher.py` uses `watchdog.Observer`. The handler only processes **direct children** of the watched directory (files already inside organized subdirectories are ignored to avoid re-processing).

## Key conventions

- Rules always return **relative** paths (e.g. `Path("Images/photo.jpg")`). `organizer.py` prepends the source directory.
- `organize()` accepts `dry_run=True` to print a Rich table without touching the filesystem.
- `conflict.reset_global()` must be called at the start of each `organize()` call (already done inside the function).
