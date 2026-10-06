from __future__ import annotations

import zipfile
from pathlib import Path


def screenshot_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(path for path in directory.glob("*.jpg") if path.is_file())


def usage(directory: Path) -> dict:
    files = screenshot_files(directory)
    total = 0
    for path in files:
        try:
            total += path.stat().st_size
        except OSError:
            continue
    return {"folder": str(directory), "files": len(files), "bytes": total}


def write_zip(directory: Path, destination: Path) -> int:
    files = screenshot_files(directory)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=path.name)
    return len(files)
