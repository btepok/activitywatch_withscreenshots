import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from aw_client import ActivityWatchClient
from aw_core.config import save_config_toml
from aw_core.dirs import get_config_dir, get_data_dir
from aw_core.log import setup_logging
from aw_core.models import Event

from .capture import capture_fullscreen, prune_old, save_jpeg
from .config import load_config, parse_args
from .http_api import serve_screenshot_http
from .interval import interval_to_seconds
from .settings_sync import SETTINGS_BUCKET, SettingsSync, as_bool

logger = logging.getLogger(__name__)


def screenshot_dir() -> Path:
    return Path(get_data_dir("aw-watcher-screenshot")) / "screenshots"


def _start_http(directory: Path) -> None:
    thread = threading.Thread(
        target=serve_screenshot_http,
        args=(directory,),
        name="screenshot-http",
        daemon=True,
    )
    thread.start()


def take_screenshot(directory: Path, quality: int, retention_days: float):
    image, monitors = capture_fullscreen()
    path = save_jpeg(image, directory, quality)
    removed = prune_old(directory, retention_days)
    if removed:
        logger.info("deleted %s old screenshots", len(removed))
    return path, image.size, monitors


def _send_event(client, bucket_id: str, path: Path, size, monitors: int, interval_seconds: float):
    width, height = size
    event = Event(
        timestamp=datetime.now(timezone.utc),
        duration=interval_seconds,
        data={
            "path": str(path),
            "filename": path.name,
            "width": width,
            "height": height,
            "monitors": monitors,
            "bytes": path.stat().st_size,
        },
    )
    try:
        client.insert_event(bucket_id, event)
    except Exception:
        logger.exception("saved %s but failed to send the event", path)
        return
    logger.info("saved %s (%sx%s, %s monitors)", path, width, height, monitors)


def _config_path() -> str:
    return os.path.join(get_config_dir("aw-watcher-screenshot"), "aw-watcher-screenshot.toml")


def _read_file_settings() -> dict:
    config = load_config()
    return {
        "enabled": as_bool(config.get("enabled", True)),
        "interval": config["interval"],
        "interval_unit": str(config["interval_unit"]),
        "quality": config["quality"],
        "retention_days": config["retention_days"],
    }


def _write_file_settings(settings: dict) -> None:
    enabled = "true" if as_bool(settings["enabled"]) else "false"
    text = "\n".join(
        [
            "[aw-watcher-screenshot]",
            f"enabled = {enabled}",
            f"interval = {settings['interval']}",
            f'interval_unit = "{settings["interval_unit"]}"',
            f"quality = {int(settings['quality'])}",
            f"retention_days = {settings['retention_days']}",
            "",
        ]
    )
    save_config_toml("aw-watcher-screenshot", text)


def _make_store(client: ActivityWatchClient) -> SettingsSync:
    def fetch_event():
        try:
            events = client.get_events(SETTINGS_BUCKET, limit=1)
        except Exception:
            logger.exception("failed to read screenshot settings")
            return None
        if not events:
            return None
        data = dict(events[0].data)
        timestamp = events[0].timestamp
        data["_timestamp"] = timestamp.timestamp()
        return data

    def push_event(settings: dict):
        client.insert_event(
            SETTINGS_BUCKET,
            Event(timestamp=datetime.now(timezone.utc), duration=0, data=dict(settings)),
        )

    return SettingsSync(
        read_file=_read_file_settings,
        write_file=_write_file_settings,
        file_mtime=lambda: os.path.getmtime(_config_path()),
        fetch_event=fetch_event,
        push_event=push_event,
    )


def _sleep_until_next(store: SettingsSync, settings: dict) -> dict:
    started = time.monotonic()
    seconds = interval_to_seconds(settings["interval"], settings["interval_unit"])
    while True:
        settings = store.current()
        if not as_bool(settings["enabled"]):
            return settings
        seconds = interval_to_seconds(settings["interval"], settings["interval_unit"])
        if time.monotonic() >= started + seconds:
            return settings
        time.sleep(0.4)


def main():
    args = parse_args()
    setup_logging(
        name="aw-watcher-screenshot",
        testing=args.testing,
        verbose=args.verbose,
        log_stderr=True,
        log_file=True,
    )

    client = ActivityWatchClient(
        "aw-watcher-screenshot",
        host=args.host,
        port=args.port,
        testing=args.testing,
    )
    directory = screenshot_dir()
    _start_http(Path(get_data_dir()))
    bucket_id = f"{client.client_name}_{client.client_hostname}"

    client.wait_for_start(timeout=30)
    client.create_bucket(bucket_id, "screenshot", queued=False)
    client.create_bucket(SETTINGS_BUCKET, "screenshot-settings", queued=False)
    store = _make_store(client)
    logged = None

    def capture_and_send(settings: dict):
        seconds = interval_to_seconds(settings["interval"], settings["interval_unit"])
        path, size, monitors = take_screenshot(
            directory, int(settings["quality"]), float(settings["retention_days"])
        )
        _send_event(client, bucket_id, path, size, monitors, seconds)

    if args.once:
        capture_and_send(store.current())
        return

    while True:
        try:
            settings = store.current()
        except Exception:
            logger.exception("failed to load screenshot settings")
            time.sleep(1)
            continue

        state = (
            as_bool(settings["enabled"]),
            settings["interval"],
            settings["interval_unit"],
        )
        if state != logged:
            logger.info(
                "screenshots %s, every %s %s",
                "on" if state[0] else "off",
                state[1],
                state[2],
            )
            logged = state

        if not state[0]:
            time.sleep(0.4)
            continue

        try:
            capture_and_send(settings)
        except Exception:
            logger.exception("screenshot failed")
        try:
            _sleep_until_next(store, settings)
        except Exception:
            logger.exception("failed while waiting for the next screenshot")
            time.sleep(1)
