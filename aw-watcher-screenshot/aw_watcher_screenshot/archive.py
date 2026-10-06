from __future__ import annotations

import sqlite3
import tempfile
import zipfile
from pathlib import Path

ZIP_NAME = "activitywatch-data.zip"


def screenshot_folder(root: Path) -> Path:
    return root / "aw-watcher-screenshot" / "screenshots"


def iter_data_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*") if path.is_file())


def usage(root: Path) -> dict:
    total = 0
    count = 0
    for path in iter_data_files(root):
        try:
            total += path.stat().st_size
            count += 1
        except OSError:
            continue
    shots = screenshot_folder(root)
    return {
        "folder": str(shots if shots.exists() else root),
        "data_folder": str(root),
        "files": count,
        "bytes": total,
    }


def _snapshot_sqlite(source: Path, destination: Path) -> bool:
    try:
        src = sqlite3.connect(source)
        dst = sqlite3.connect(destination)
        src.backup(dst)
        dst.close()
        src.close()
    except sqlite3.Error:
        return False
    return destination.exists() and destination.stat().st_size > 0


def write_zip(root: Path, destination: Path) -> int:
    count = 0
    skipped = set()
    dest = destination.resolve()
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in iter_data_files(root):
            try:
                if path.resolve() == dest:
                    continue
            except OSError:
                continue
            rel = path.relative_to(root).as_posix()
            if rel in skipped:
                continue
            if path.suffix == ".db" and _add_sqlite(archive, path, rel, skipped):
                count += 1
                continue
            try:
                archive.write(path, arcname=rel)
            except OSError:
                continue
            count += 1
    return count


def _add_sqlite(archive: zipfile.ZipFile, path: Path, rel: str, skipped: set[str]) -> bool:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        snap = Path(tmp.name)
    try:
        if not _snapshot_sqlite(path, snap):
            return False
        archive.write(snap, arcname=rel)
    finally:
        snap.unlink(missing_ok=True)
    parent = rel.rsplit("/", 1)[0] if "/" in rel else ""
    prefix = parent + "/" if parent else ""
    skipped.add(prefix + path.name + "-wal")
    skipped.add(prefix + path.name + "-shm")
    return True
