import argparse

from aw_core.config import load_config_toml

from .interval import interval_to_seconds, parse_every

default_config = """
[aw-watcher-screenshot]
interval = 60
interval_unit = "seconds"
quality = 60
retention_days = 7
""".strip()


def load_config():
    return load_config_toml("aw-watcher-screenshot", default_config)["aw-watcher-screenshot"]


def parse_args(argv=None):
    config = load_config()

    parser = argparse.ArgumentParser(
        description=(
            "Takes a screenshot of the whole screen (all monitors) "
            "every N seconds or minutes and stores it for ActivityWatch."
        )
    )
    parser.add_argument("--host", dest="host")
    parser.add_argument("--port", dest="port")
    parser.add_argument("--testing", dest="testing", action="store_true")
    parser.add_argument("--verbose", dest="verbose", action="store_true")
    parser.add_argument(
        "--interval",
        type=float,
        default=float(config["interval"]),
        help="how often to capture, together with --unit (default from config)",
    )
    parser.add_argument(
        "--unit",
        default=str(config["interval_unit"]),
        help="seconds or minutes (also s or m)",
    )
    parser.add_argument(
        "--every",
        default=None,
        help="shortcut that overrides --interval and --unit, e.g. 30s or 5m",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=int(config["quality"]),
        help="JPEG quality 1-95",
    )
    parser.add_argument(
        "--retention-days",
        type=float,
        default=float(config["retention_days"]),
        help="delete screenshots older than this. 0 keeps them",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="capture a single screenshot and exit",
    )
    args = parser.parse_args(argv)

    if args.every:
        args.interval_seconds = parse_every(args.every)
    else:
        args.interval_seconds = interval_to_seconds(args.interval, args.unit)

    if not 1 <= args.quality <= 95:
        parser.error("--quality must be between 1 and 95")
    if args.retention_days < 0:
        parser.error("--retention-days must be >= 0")
    return args
