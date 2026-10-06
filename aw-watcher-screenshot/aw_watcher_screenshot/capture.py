from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path


def capture_fullscreen():
    """Grab every monitor as one image. Returns (image, monitor_count)."""
    import mss
    from PIL import Image

    with mss.mss() as sct:
        if not sct.monitors:
            raise RuntimeError("no monitors found")
        raw = sct.grab(sct.monitors[0])
        if raw.width <= 0 or raw.height <= 0:
            raise RuntimeError(f"empty capture {raw.width}x{raw.height}")
        image = Image.frombytes("RGB", raw.size, raw.rgb)
        return image, max(len(sct.monitors) - 1, 1)


def save_jpeg(image, directory, quality: int, when: datetime | None = None) -> Path:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    when = when or datetime.now()
    name = when.strftime("%Y-%m-%d_%H-%M-%S") + f"-{when.microsecond // 1000:03d}.jpg"
    final = directory / name
    tmp = directory / f"{name}.tmp"
    image.save(tmp, format="JPEG", quality=int(quality), optimize=True)
    os.replace(tmp, final)
    return final


def prune_old(directory, retention_days: float, now: datetime | None = None) -> list[Path]:
    directory = Path(directory)
    if not directory.exists():
        return []

    removed: list[Path] = []
    now = now or datetime.now()

    if retention_days > 0:
        cutoff = (now - timedelta(days=float(retention_days))).timestamp()
        for path in directory.glob("*.jpg"):
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink()
                    removed.append(path)
            except OSError:
                continue

    tmp_cutoff = (now - timedelta(hours=1)).timestamp()
    for path in directory.glob("*.jpg.tmp"):
        try:
            if path.stat().st_mtime < tmp_cutoff:
                path.unlink()
                removed.append(path)
        except OSError:
            continue

    return removed
