from aw_watcher_screenshot.settings_sync import SettingsSync, normalize, same_capture_settings


def test_gui_event_overrides_file_until_file_is_edited():
    file_settings = {"enabled": True, "interval": 60, "interval_unit": "seconds", "quality": 60}
    mtime = {"value": 10.0}
    events = []

    def read_file():
        return dict(file_settings)

    def write_file(settings):
        file_settings.update(settings)
        mtime["value"] += 1

    store = SettingsSync(
        read_file=read_file,
        write_file=write_file,
        file_mtime=lambda: mtime["value"],
        fetch_event=lambda: events[-1] if events else None,
        push_event=lambda settings: events.append(dict(settings)),
    )

    first = store.current()
    assert first["enabled"] is True
    assert first["interval"] == 60
    assert len(events) == 1

    events.append({"enabled": False, "interval": 5, "interval_unit": "minutes"})
    updated = store.current()
    assert updated["enabled"] is False
    assert updated["interval"] == 5
    assert updated["interval_unit"] == "minutes"
    assert file_settings["enabled"] is False

    file_settings["enabled"] = True
    file_settings["interval"] = 15
    mtime["value"] += 5
    edited = store.current()
    assert edited["enabled"] is True
    assert edited["interval"] == 15
    assert events[-1]["interval"] == 15


def test_normalize_does_not_treat_false_string_as_true():
    assert normalize({"enabled": "false", "interval": "30", "interval_unit": "minutes"})["enabled"] is False
    assert same_capture_settings(
        {"enabled": True, "interval": 1, "interval_unit": "minutes"},
        {"enabled": True, "interval": 1.0, "interval_unit": "minutes"},
    )
