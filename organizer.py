"""Sort the files in a messy folder into subfolders by file type.

Safety features:
- plan_moves() only builds a plan; nothing moves until apply_moves() is called
- existing files are never overwritten (a number is added to the name instead)
- hidden files and subfolders are left alone
- every move is recorded in a log file
"""

import csv
import shutil
from datetime import datetime
from pathlib import Path

CATEGORIES = {
    "Images": ["jpg", "jpeg", "png", "gif", "webp", "bmp", "svg"],
    "Documents": ["pdf", "doc", "docx", "txt", "md", "rtf"],
    "Spreadsheets": ["xlsx", "xls"],
    "Data": ["csv", "tsv", "json"],
    "Code": ["py", "ipynb", "js", "html", "css", "sql"],
    "Archives": ["zip", "rar", "7z", "tar", "gz"],
}

EXTENSION_TO_CATEGORY = {
    ext: category for category, extensions in CATEGORIES.items() for ext in extensions
}


def categorize(path):
    """Return the category folder name for a file, based on its extension."""
    extension = Path(path).suffix.lower().lstrip(".")
    return EXTENSION_TO_CATEGORY.get(extension, "Other")


def unique_path(target, reserved=()):
    """Return a path that doesn't exist yet, adding _1, _2, ... if needed."""
    target = Path(target)
    candidate = target
    counter = 1
    while candidate.exists() or candidate in reserved:
        candidate = target.with_name(f"{target.stem}_{counter}{target.suffix}")
        counter += 1
    return candidate


def plan_moves(inbox, dest):
    """Return a list of (source, destination) pairs. Moves nothing."""
    inbox, dest = Path(inbox), Path(dest)
    if not inbox.is_dir():
        raise FileNotFoundError(f"Inbox folder not found: {inbox}")

    moves = []
    reserved = set()
    for file in sorted(inbox.iterdir()):
        if not file.is_file() or file.name.startswith("."):
            continue
        target = unique_path(dest / categorize(file) / file.name, reserved)
        reserved.add(target)
        moves.append((file, target))
    return moves


def apply_moves(moves, log_file=None):
    """Carry out the plan. Returns a list of (source, destination, status)."""
    results = []
    for source, target in moves:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
            results.append((source, target, "moved"))
        except Exception as e:  # one failure shouldn't stop the rest
            results.append((source, target, f"failed: {e}"))

    if log_file:
        write_log(results, log_file)
    return results


def write_log(results, log_file):
    log_file = Path(log_file)
    new_file = not log_file.exists()
    with open(log_file, "a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["timestamp", "source", "destination", "status"])
        stamp = datetime.now().isoformat(timespec="seconds")
        for source, target, status in results:
            writer.writerow([stamp, source, target, status])
