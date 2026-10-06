#!/usr/bin/env python3
"""Copy the screenshot settings script into the ActivityWatch web UI."""
import pathlib
import shutil
import sys

SNIPPET = '<script defer src="/screenshot-settings.js"></script>'
CONNECT_OLD = "connect-src 'self'"
CONNECT_NEW = "connect-src 'self' http://127.0.0.1:5617"
HERE = pathlib.Path(__file__).resolve().parents[2]
JS_SRC = HERE / "aw-watcher-screenshot" / "web" / "screenshot-settings.js"


def inject(static_dir: pathlib.Path) -> None:
    index = static_dir / "index.html"
    if not index.is_file():
        raise SystemExit(f"missing {index}")
    shutil.copyfile(JS_SRC, static_dir / "screenshot-settings.js")
    html = index.read_text(encoding="utf-8")
    original = html
    if SNIPPET not in html:
        if "</body>" not in html:
            raise SystemExit(f"no </body> in {index}")
        html = html.replace("</body>", SNIPPET + "</body>", 1)
    if "127.0.0.1:5617" not in html and CONNECT_OLD in html:
        html = html.replace(CONNECT_OLD, CONNECT_NEW, 1)
    if html != original:
        index.write_text(html, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <aw-server static dir>", file=sys.stderr)
        return 2
    inject(pathlib.Path(sys.argv[1]))
    print(f"injected screenshot settings into {sys.argv[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
