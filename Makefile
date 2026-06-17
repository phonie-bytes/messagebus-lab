.PHONY: install lint format test run clean

install:
\tuv sync --all-extras

lint:
\tuv run ruff check src tests
\tuv run mypy src

format:
\tuv run ruff format src tests

test:
\tuv run pytest -v

run:
\tuv run messagebus

clean:
\trm -rf .pytest_cache .mypy_cache .ruff_cache dist build *.egg-info