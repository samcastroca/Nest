from pathlib import Path

from prometeus.rules.base import Rule

# Default extension → category mapping.
# Keys are folder names; values are sets of lowercase extensions (no dot).
DEFAULT_CATEGORIES: dict[str, list[str]] = {
    "Images":       ["jpg", "jpeg", "png", "gif", "bmp", "svg", "webp", "tiff", "ico", "heic", "raw"],
    "Documents":    ["pdf", "doc", "docx", "txt", "odt", "rtf", "md", "epub", "pages"],
    "Spreadsheets": ["xls", "xlsx", "csv", "ods", "numbers"],
    "Presentations":["ppt", "pptx", "odp", "key"],
    "Videos":       ["mp4", "avi", "mkv", "mov", "wmv", "flv", "webm", "m4v"],
    "Audio":        ["mp3", "wav", "flac", "aac", "ogg", "wma", "m4a", "opus"],
    "Archives":     ["zip", "rar", "7z", "tar", "gz", "bz2", "xz", "tgz"],
    "Code":         ["py", "js", "ts", "html", "css", "json", "yaml", "yml", "sh", "bat",
                     "java", "c", "cpp", "h", "go", "rs", "rb", "php", "swift", "kt"],
    "Datasets":     ["parquet", "feather", "h5", "hdf5", "npz", "npy", "pkl", "pickle",
                     "jsonl", "arrow"],
    "Executables":  ["exe", "msi", "dmg", "pkg", "deb", "rpm", "appimage"],
}

# Build a reverse lookup: extension -> category
_EXT_TO_CATEGORY: dict[str, str] = {}
for _cat, _exts in DEFAULT_CATEGORIES.items():
    for _ext in _exts:
        _EXT_TO_CATEGORY[_ext] = _cat


class ByExtensionRule(Rule):
    """Organizes files into category folders based on their extension.

    Uses *categories* as an override mapping ``{category: [ext, ...]}``.
    Falls back to ``DEFAULT_CATEGORIES`` for any extension not covered.
    Unrecognized extensions go into ``Other/``.
    """

    def __init__(self, categories: dict[str, list[str]] | None = None) -> None:
        if categories:
            self._lookup: dict[str, str] = {}
            for cat, exts in categories.items():
                for ext in exts:
                    self._lookup[ext.lower().lstrip(".")] = cat
        else:
            self._lookup = _EXT_TO_CATEGORY

    def resolve(self, file: Path) -> Path | None:
        ext = file.suffix.lower().lstrip(".")
        category = self._lookup.get(ext, "Other")
        return Path(category) / file.name
