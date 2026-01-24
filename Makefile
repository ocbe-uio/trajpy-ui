.PHONY: check-format fix test lint type-check all

check-format:
	.venv/bin/ruff format trajpy_ui --check

fix:
	.venv/bin/ruff format trajpy_ui
	.venv/bin/ruff check trajpy_ui --fix

test:
	.venv/bin/python -m pytest -s tests

lint:
	.venv/bin/ruff check trajpy_ui

type-check:
	.venv/bin/pyright trajpy_ui

all: lint type-check check-format fix test
