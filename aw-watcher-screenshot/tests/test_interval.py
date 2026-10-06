import pytest

from aw_watcher_screenshot.interval import interval_to_seconds, parse_every


def test_seconds_and_minutes():
    assert interval_to_seconds(30, "seconds") == 30
    assert interval_to_seconds(2, "minutes") == 120
    assert interval_to_seconds(1, "m") == 60
    assert interval_to_seconds(5, "мин") == 300
    assert interval_to_seconds(10, "сек") == 10


def test_every_shortcut():
    assert parse_every("30s") == 30
    assert parse_every("5m") == 300
    assert parse_every("1.5 minutes") == 90


def test_rejects_bad_interval():
    with pytest.raises(ValueError):
        interval_to_seconds(0, "seconds")
    with pytest.raises(ValueError):
        interval_to_seconds(1, "hours")
    with pytest.raises(ValueError):
        parse_every("soon")
