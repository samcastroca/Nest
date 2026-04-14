"""Session log — records every file move so they can be undone later.

The log is stored as ``.nest_log.json`` inside the source directory.

Log format::

    {
      "sessions": [
        {
          "id": "20240315_103045_a1b2c3",
          "timestamp": "2024-03-15T10:30:45",
          "moves": [
            {"from": "photo.jpg", "to": "Images/photo.jpg"},
            ...
          ]
        }
      ]
    }

``from`` and ``to`` are both paths *relative* to the source directory.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

LOG_FILENAME = ".nest_log.json"


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _load(log_file: Path) -> dict:
    if log_file.exists():
        return json.loads(log_file.read_text(encoding="utf-8"))
    return {"sessions": []}


def _save(log_file: Path, data: dict) -> None:
    log_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def new_session_id() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id = uuid.uuid4().hex[:6]
    return f"{timestamp}_{short_id}"


def record_session(source_dir: Path, session_id: str, moves: list[tuple[Path, Path]]) -> None:
    """Append a completed session to the log.

    Args:
        source_dir:  The directory that was organized.
        session_id:  Unique session identifier (from :func:`new_session_id`).
        moves:       List of ``(original_path, final_path)`` absolute paths.
                     Both must be inside *source_dir*.
    """
    if not moves:
        return

    log_file = source_dir / LOG_FILENAME
    data = _load(log_file)

    entries = [
        {
            "from": str(src.relative_to(source_dir)),
            "to": str(dst.relative_to(source_dir)),
        }
        for src, dst in moves
    ]

    data["sessions"].append(
        {
            "id": session_id,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "moves": entries,
        }
    )
    _save(log_file, data)


def list_sessions(source_dir: Path) -> list[dict]:
    """Return all recorded sessions for *source_dir*, newest first."""
    data = _load(source_dir / LOG_FILENAME)
    return list(reversed(data["sessions"]))


def get_session(source_dir: Path, session_id: str) -> dict | None:
    """Return the session dict for *session_id*, or ``None`` if not found."""
    data = _load(source_dir / LOG_FILENAME)
    for session in data["sessions"]:
        if session["id"] == session_id:
            return session
    return None


def remove_session(source_dir: Path, session_id: str) -> None:
    """Delete a session entry from the log after a successful undo."""
    log_file = source_dir / LOG_FILENAME
    data = _load(log_file)
    data["sessions"] = [s for s in data["sessions"] if s["id"] != session_id]
    _save(log_file, data)
