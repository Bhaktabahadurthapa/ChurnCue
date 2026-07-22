.PHONY: install data run lint format-check test check docker-up

install:
	python3.12 -m venv .venv
	.venv/bin/pip install -e '.[dev]'

data:
	.venv/bin/python scripts/generate_demo_data.py

run:
	.venv/bin/clientrevive

lint:
	.venv/bin/ruff check .

format-check:
	.venv/bin/ruff format --check .

test:
	.venv/bin/pytest

check: lint format-check test

docker-up:
	docker compose up --build
