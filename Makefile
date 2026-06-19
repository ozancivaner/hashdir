.PHONY: check format test test-pinned-regression

check:
	python -m ruff check .
	python -m ruff format --check .

format:
	python -m ruff check --fix .
	python -m ruff format .

test:
	python -m unittest discover tests

test-pinned-regression:
	python -m unittest tests/test_pinned_regression.py

package:
	python -m build
	python -m twine upload --non-interactive --verbose --skip-existing dist/*
