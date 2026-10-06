from __future__ import annotations

SETTINGS_BUCKET = "aw-watcher-screenshot-settings"


def as_bool(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def normalize(data: dict, base: dict | None = None) -> dict:
    merged = dict(base or {})
    if "enabled" in data:
        merged["enabled"] = as_bool(data["enabled"])
    if "interval" in data:
        merged["interval"] = float(data["interval"])
    if "interval_unit" in data:
        merged["interval_unit"] = str(data["interval_unit"]).strip().lower()
    if "quality" in data:
        merged["quality"] = int(data["quality"])
    if "retention_days" in data:
        merged["retention_days"] = float(data["retention_days"])
    merged.setdefault("enabled", True)
    return merged


def same_capture_settings(left: dict, right: dict) -> bool:
    return (
        as_bool(left.get("enabled", True)) == as_bool(right.get("enabled", True))
        and float(left.get("interval")) == float(right.get("interval"))
        and str(left.get("interval_unit")) == str(right.get("interval_unit"))
    )


class SettingsSync:
    """File is the fallback. A newer event from the web UI wins until the file changes."""

    def __init__(self, read_file, write_file, file_mtime, fetch_event, push_event):
        self.read_file = read_file
        self.write_file = write_file
        self.file_mtime = file_mtime
        self.fetch_event = fetch_event
        self.push_event = push_event
        self.last_written_mtime = None

    def current(self) -> dict:
        file_settings = normalize(self.read_file())
        file_mtime = self.file_mtime()
        event = self.fetch_event()

        if event is None:
            self._publish(file_settings)
            return file_settings

        event_settings = normalize(event, file_settings)
        event_ts = event.get("_timestamp")
        file_newer_than_event = (
            self.last_written_mtime is None
            and event_ts is not None
            and file_mtime > float(event_ts) + 0.5
            and not same_capture_settings(file_settings, event_settings)
        )
        user_edited_file = (
            self.last_written_mtime is not None
            and file_mtime > self.last_written_mtime + 0.5
            and not same_capture_settings(file_settings, event_settings)
        )
        if user_edited_file or file_newer_than_event:
            self._publish(file_settings)
            return file_settings

        if not same_capture_settings(file_settings, event_settings):
            self._mirror(event_settings)
        return event_settings

    def _publish(self, settings: dict) -> None:
        self.push_event(settings)
        self._mirror(settings)

    def _mirror(self, settings: dict) -> None:
        self.write_file(settings)
        self.last_written_mtime = self.file_mtime()
