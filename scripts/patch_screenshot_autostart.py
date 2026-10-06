#!/usr/bin/env python3
"""Add aw-watcher-screenshot to aw-qt's default autostart list.

The watcher lives in this repo. aw-qt is a submodule, so the default module
list is patched at build time instead of moving the submodule pointer.
"""
import pathlib
import sys

OLD = 'autostart_modules = ["aw-server", "aw-watcher-afk", "aw-watcher-window"]'
NEW = 'autostart_modules = ["aw-server", "aw-watcher-afk", "aw-watcher-window", "aw-watcher-screenshot"]'


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path/to/aw_qt/config.py>", file=sys.stderr)
        return 2

    path = pathlib.Path(sys.argv[1])
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"ERROR: {path} not found", file=sys.stderr)
        return 1

    if OLD not in text:
        if NEW in text:
            print(f"Already patched: {path}")
            return 0
        print(f"ERROR: autostart_modules list not found in {path}", file=sys.stderr)
        return 1

    path.write_text(text.replace(OLD, NEW), encoding="utf-8")
    print(f"Patched {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
