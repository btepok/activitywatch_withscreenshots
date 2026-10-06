.PHONY: build test package clean

build:
	poetry install

test:
	poetry run aw-watcher-screenshot --help
	poetry run python -m pytest tests/ -q

package:
	pyinstaller aw-watcher-screenshot.spec --clean --noconfirm

clean:
	rm -rf build dist
	rm -rf aw_watcher_screenshot/__pycache__
