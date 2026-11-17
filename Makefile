.PHONY: test lint serve ingest
serve:
	uv run uvicorn app.main:app --reload
test:
	uv run pytest -q
lint:
	uv run ruff check app scripts tests
ingest:
	uv run python scripts/ingest.py
