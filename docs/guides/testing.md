# Testing

## Backend tests

Backend tests use SQLite and a mocked pgSTAC — no running database is required.

Run the full test suite inside the backend container:

```bash
docker compose exec backend uv run pytest -v
```

The backend container must be running (`docker compose up backend` or `docker compose up --build`).

## Running a specific test file or test

```bash
docker compose exec backend uv run pytest -v fair-data-finder/backend/tests/test_search.py
docker compose exec backend uv run pytest -v -k "test_search"
```

## Running tests outside Docker

If you have a local Python environment set up with `uv`:

```bash
cd fair-data-finder/backend
uv run pytest -v
```

No database connection is needed — the tests mock all database interactions.

## Frontend

There are no automated frontend tests at this time. Manual verification steps are in [Installation](../installation.md#verify-the-app-is-running).