import zipfile

from aw_watcher_screenshot.archive import usage, write_zip


def test_usage_counts_only_jpgs(tmp_path):
    (tmp_path / "a.jpg").write_bytes(b"1234")
    (tmp_path / "b.jpg").write_bytes(b"12")
    (tmp_path / "skip.tmp").write_bytes(b"99999")

    info = usage(tmp_path)
    assert info["files"] == 2
    assert info["bytes"] == 6
    assert info["folder"] == str(tmp_path)


def test_write_zip_packs_jpg_names(tmp_path):
    (tmp_path / "one.jpg").write_bytes(b"aaaa")
    (tmp_path / "two.jpg").write_bytes(b"bbbb")
    destination = tmp_path / "out.zip"

    assert write_zip(tmp_path, destination) == 2
    with zipfile.ZipFile(destination) as archive:
        assert sorted(archive.namelist()) == ["one.jpg", "two.jpg"]
