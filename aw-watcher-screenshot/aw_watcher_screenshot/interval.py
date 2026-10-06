import re

_UNIT_SECONDS = {
    "s": 1,
    "sec": 1,
    "secs": 1,
    "second": 1,
    "seconds": 1,
    "сек": 1,
    "секунда": 1,
    "секунды": 1,
    "секунд": 1,
    "m": 60,
    "min": 60,
    "mins": 60,
    "minute": 60,
    "minutes": 60,
    "мин": 60,
    "минута": 60,
    "минуты": 60,
    "минут": 60,
}

_EVERY_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*([a-zA-Zа-яА-Я]+)\s*$"
)


def interval_to_seconds(interval: float, unit: str) -> float:
    try:
        amount = float(interval)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"interval must be a number, got {interval!r}") from exc

    key = str(unit).strip().lower()
    if key not in _UNIT_SECONDS:
        allowed = "seconds, minutes"
        raise ValueError(f"unknown interval unit {unit!r}, use {allowed}")

    seconds = amount * _UNIT_SECONDS[key]
    if seconds <= 0:
        raise ValueError(f"interval must be > 0, got {amount} {key}")
    return seconds


def parse_every(text: str) -> float:
    match = _EVERY_RE.match(text)
    if not match:
        raise ValueError(f"bad interval {text!r}, use 30s or 5m")
    return interval_to_seconds(float(match.group(1)), match.group(2))
