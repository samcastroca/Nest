# Nest

CLI tool to automatically organize files by extension, date, or custom rules.

## Installation

```bash
git clone https://github.com/samcastroca/nest.git
cd nest
pip install -e .
```

## Commands

### `sort` — organize a folder

```bash
nest sort <path> [options]
```

| Option | Description |
|---|---|
| `--by extension` | Group files into category folders (Images, Documents, Videos…) |
| `--by date` | Organize into `YYYY/MM` subfolders by modification date |
| `--config rules.yaml` | Apply custom rules from a YAML file (takes priority over `--by`) |
| `--format "%Y/%m"` | Custom date folder format (used with `--by date`) |
| `--use mtime\|ctime` | Timestamp to use for date sorting (default: `mtime`) |
| `--dry-run` | Preview moves without touching any files |
| `--recursive` | Also process files inside subdirectories |
| `--no-interactive` | Auto-rename on conflict without prompting |

**Examples:**

```bash
# Preview what would happen
nest sort ~/Downloads --by extension --dry-run

# Organize by file type
nest sort ~/Downloads --by extension

# Organize by year/month
nest sort ~/Downloads --by date --format "%Y/%m"

# Custom rules with extension fallback
nest sort ~/Downloads --config rules.yaml --by extension
```

#### Conflict resolution

When a file already exists at the destination, Nest prompts:

```
[s] Skip  [o] Overwrite  [r] Rename  [A] All-rename  [S] All-skip  [q] Quit
```

---

### `undo` — restore files from a previous session

Every `sort` run records a session log (`.nest_log.json`) inside the organized folder. Use `undo` to reverse any of those sessions.

```bash
# Undo the most recent session
nest undo ~/Downloads

# Preview what would be restored without moving anything
nest undo ~/Downloads --dry-run

# List all recorded sessions
nest undo ~/Downloads --list

# Undo a specific session by ID
nest undo ~/Downloads --session 20240315_103045_a1b2c3
```

The session entry is removed from the log after a successful undo.

---

### `watch` — monitor a folder in real time

Organizes new files automatically as they appear. Press `Ctrl+C` to stop.

```bash
nest watch <path> [--by extension|date] [--config rules.yaml]
```

```bash
nest watch ~/Downloads --by extension
nest watch ~/Downloads --config rules.yaml --by date
```

---

### `config init` — generate an example rules file

```bash
nest config init --output rules.yaml
```

---

## Custom rules (YAML)

Rules are evaluated in order; the **first match wins**.  
If `--by extension` or `--by date` is also passed, it acts as a fallback for unmatched files.

```yaml
# rules.yaml
rules:
  - name: "Facturas"
    pattern: "*.pdf"
    match: "factura|invoice"   # optional regex on filename (case-insensitive)
    destination: "Facturas/"

  - name: "Screenshots"
    pattern: "Screenshot*.png"
    destination: "Capturas/"

  - name: "Datasets"
    pattern: "*.csv"
    destination: "Datasets/"
```

```bash
nest sort ~/Downloads --config rules.yaml
```

---

## Default extension categories

| Folder | Extensions |
|---|---|
| Images | jpg, jpeg, png, gif, bmp, svg, webp, tiff, ico, heic, raw |
| Documents | pdf, doc, docx, txt, odt, rtf, md, epub |
| Spreadsheets | xls, xlsx, csv, ods |
| Presentations | ppt, pptx, odp |
| Videos | mp4, avi, mkv, mov, wmv, flv, webm |
| Audio | mp3, wav, flac, aac, ogg, wma, m4a |
| Archives | zip, rar, 7z, tar, gz, bz2 |
| Code | py, js, ts, html, css, json, yaml, sh… |
| Datasets | parquet, feather, h5, npz, pkl… |
| Executables | exe, msi, dmg, pkg |
| Other | everything else |

---

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```
