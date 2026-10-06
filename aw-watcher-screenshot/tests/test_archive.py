import sqlite3
import zipfile

from aw_watcher_screenshot.archive import usage, write_zip


def test_usage_counts_every_file(tmp_path):
    shots = tmp_path / "aw-watcher-screenshot" / "screenshots"
    shots.mkdir(parents=True)
    (shots / "a.jpg").write_bytes(b"1234")
    (tmp_path / "aw-qt").mkdir()
    (tmp_path / "aw-qt" / "aw-qt.toml").write_bytes(b"12")

    info = usage(tmp_path)
    assert info["files"] == 2
    assert info["bytes"] == 6
    assert info["folder"] == str(shots)
    assert info["data_folder"] == str(tmp_path)


def test_write_zip_packs_data_tree(tmp_path):
    root = tmp_path / "data"
    shots = root / "aw-watcher-screenshot" / "screenshots"
    shots.mkdir(parents=True)
    (shots / "one.jpg").write_bytes(b"aaaa")
    (root / "aw-server").mkdir()
    (root / "aw-server" / "aw-server.toml").write_text("port = 5600\n", encoding="utf-8")
    db_path = root / "aw-server" / "peewee-sqlite.v2.db"
    db = sqlite3.connect(db_path)
    db.execute("create table eventmodel (id integer primary key, data text)")
    db.execute("insert into eventmodel (data) values ('window')")
    db.commit()
    db.close()
    (root / "aw-server" / "peewee-sqlite.v2.db-wal").write_bytes(b"wal")
    destination = tmp_path / "out.zip"

    assert write_zip(root, destination) == 3
    with zipfile.ZipFile(destination) as archive:
        names = sorted(archive.namelist())
    assert names == [
        "aw-server/aw-server.toml",
        "aw-server/peewee-sqlite.v2.db",
        "aw-watcher-screenshot/screenshots/one.jpg",
    ]
    with zipfile.ZipFile(destination) as archive:
        snapshot = archive.read("aw-server/peewee-sqlite.v2.db")
    unpacked = tmp_path / "restored.db"
    unpacked.write_bytes(snapshot)
    restored = sqlite3.connect(unpacked)
    row = restored.execute("select data from eventmodel").fetchone()
    restored.close()
    assert row == ("window",)
