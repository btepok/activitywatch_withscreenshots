import os
from datetime import datetime, timedelta

from PIL import Image

from aw_watcher_screenshot.capture import prune_old, save_jpeg


def test_save_jpeg_replaces_tmp(tmp_path):
    image = Image.new("RGB", (16, 8), (12, 34, 56))
    when = datetime(2026, 10, 6, 8, 36, 1, 120000)
    path = save_jpeg(image, tmp_path, quality=50, when=when)

    assert path.name == "2026-10-06_08-36-01-120.jpg"
    assert path.exists()
    assert path.stat().st_size > 0
    assert list(tmp_path.glob("*.tmp")) == []

    loaded = Image.open(path)
    assert loaded.size == (16, 8)


def test_prune_keeps_fresh_files(tmp_path):
    old = tmp_path / "old.jpg"
    fresh = tmp_path / "fresh.jpg"
    old.write_bytes(b"old")
    fresh.write_bytes(b"fresh")

    old_ts = (datetime.now() - timedelta(days=10)).timestamp()
    os.utime(old, (old_ts, old_ts))

    removed = prune_old(tmp_path, retention_days=7)
    assert old in removed
    assert not old.exists()
    assert fresh.exists()


def test_prune_disabled(tmp_path):
    old = tmp_path / "old.jpg"
    old.write_bytes(b"old")
    old_ts = (datetime.now() - timedelta(days=30)).timestamp()
    os.utime(old, (old_ts, old_ts))

    assert prune_old(tmp_path, retention_days=0) == []
    assert old.exists()
