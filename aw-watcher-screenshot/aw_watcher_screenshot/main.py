import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from aw_client import ActivityWatchClient
from aw_core.dirs import get_data_dir
from aw_core.log import setup_logging
from aw_core.models import Event

from .capture import capture_fullscreen, prune_old, save_jpeg
from .config import parse_args

logger = logging.getLogger(__name__)


def screenshot_dir() -> Path:
    return Path(get_data_dir("aw-watcher-screenshot")) / "screenshots"


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
    bucket_id = f"{client.client_name}_{client.client_hostname}"

    logger.info(
        "capturing the whole screen every %ss, files in %s",
        args.interval_seconds,
        directory,
    )

    client.wait_for_start(timeout=30)
    client.create_bucket(bucket_id, "screenshot", queued=False)

    def capture_and_send():
        path, size, monitors = take_screenshot(
            directory, args.quality, args.retention_days
        )
        _send_event(client, bucket_id, path, size, monitors, args.interval_seconds)

    if args.once:
        capture_and_send()
        return

    while True:
        started = time.monotonic()
        try:
            capture_and_send()
        except Exception:
            logger.exception("screenshot failed")
        remaining = args.interval_seconds - (time.monotonic() - started)
        if remaining > 0:
            time.sleep(remaining)
