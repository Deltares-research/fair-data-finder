# Backend

FastAPI application (`dmsapi`) that exposes a STAC-compliant REST API. Managed with [uv](https://docs.astral.sh/uv/).

Key libraries: [stac-fastapi-pgstac](https://github.com/stac-utils/stac-fastapi-pgstac), [SQLModel](https://sqlmodel.tiangolo.com/), [Alembic](https://alembic.sqlalchemy.org/), [FastAPI](https://fastapi.tiangolo.com/).

## Environment setup

```bash
cp .env.example .env
# Edit .env — set AZURE_APP_CLIENT_ID, AZURE_APP_CLIENT_SECRET, AZURE_TENANT_ID, APP_SECRET_KEY
```

See `.env.example` for the full reference.

## Run with Docker (recommended)

```bash
# From the repository root
docker compose up --build backend
```

The backend is available at `http://localhost:8000/api`.

The `migrate` service runs `pypgstac migrate && alembic upgrade head` automatically before the backend starts — no manual migration step is needed during normal development.

## Run locally with uv

Requires Postgres to be running (e.g. via `docker compose up postgres`). Postgres is exposed on host port **5433**.

```bash
uv sync
uv run fastapi dev api/app.py
```

Set `DB_CONNECTION_URL=postgresql+psycopg://postgres:postgres@localhost:5433/postgres` and the `PG*` variables for the host-side connection (see `.env.example`).

> SSO login does not work when the backend runs outside Docker unless you also reconfigure Caddy. See [Installation](../../docs/installation.md#logging-in-sso).

## Run tests

Tests use SQLite and a mocked pgSTAC — no running database required.

```bash
docker compose exec backend uv run pytest -v
```

## Database migrations

```bash
# Generate a new revision after changing a model
docker compose exec backend alembic revision --autogenerate -m "Describe the change"

# Apply all pending migrations
docker compose exec backend alembic upgrade head

# Check current revision
docker compose exec backend alembic current
```

For the full migration guide, see [Migrations](../../docs/guides/migrations.md).

## Useful commands

```bash
# Open a shell inside the running backend container
docker compose exec backend bash

# View live logs
docker compose logs -f backend

# Rebuild only the backend image
docker compose up --build backend
```

## Folder structure

```
backend/
├── api/
│   ├── alembic/         Database migration scripts
│   │   └── versions/    Generated migration files
│   ├── core/            App configuration, auth, middleware
│   ├── database/        Database connection pools
│   ├── extensions/      Custom STAC API extensions (RBAC, keywords, topics)
│   ├── schemas/         Pydantic / SQLModel models
│   ├── app.py           FastAPI application entry point
│   └── config.py        Settings (pydantic-settings)
├── scripts/             Utility scripts (e.g. migrate_to_pgstac.py)
├── tests/               Pytest test suite
├── Dockerfile
├── pyproject.toml
└── .env.example
```

## Further reading

- [Architecture overview](../../docs/architecture/overview.md)
- [Database](../../docs/architecture/database.md)
- [Installation](../../docs/installation.md)
- [Migrations](../../docs/guides/migrations.md)
- [Testing](../../docs/guides/testing.md)
