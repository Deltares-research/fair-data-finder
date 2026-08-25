# Database

## Overview

Fair Data Finder uses a single PostgreSQL + PostGIS instance with two schemas:

| Schema | Purpose | Managed by |
|--------|---------|------------|
| `pgstac` | STAC Collections and Items | `pypgstac migrate` |
| `public` | Application tables — users, groups, keywords, RBAC | `alembic upgrade head` |

The backend talks to Postgres via two separate connection pools: a pgSTAC pool (read/write for STAC data) and a SQLModel/SQLAlchemy connection (for app tables).

## PostgreSQL extensions

The file `fair-data-finder/database/postgres/init-extensions.sql` installs the required PostgreSQL extensions (PostGIS, pgSTAC, etc.) and runs once per cluster.

In Docker Compose the file is automatically bind-mounted into the `postgis/postgis` container at `/docker-entrypoint-initdb.d/01-init-extensions.sql` and executed once when the Docker volume is first created.

To trigger a re-run (for example, after changing the file), destroy the volume and restart:

```bash
docker compose down -v
docker compose up
```

## Migration workflow

On every `docker compose up`, the `migrate` service runs both migration tools against Postgres before the backend starts, then exits. The backend only starts after migrations complete successfully.

For creating and applying migrations manually, see [Migrations](../guides/migrations.md).

## Local connection details

| Setting | Value |
|---------|-------|
| Host (from host machine) | `localhost` |
| Port (from host machine) | `5433` (mapped from container's `5432`) |
| Username | `postgres` |
| Password | `postgres` |
| Database | `postgres` |

The container exposes Postgres on host port **5433** (not 5432) to avoid conflicting with a local Postgres installation.

`DB_CONNECTION_URL` for connecting from the host:
```
postgresql+psycopg://postgres:postgres@localhost:5433/postgres
```
