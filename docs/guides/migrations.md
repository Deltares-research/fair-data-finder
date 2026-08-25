# Database Migrations

Fair Data Finder uses two migration tools in sequence:

1. `pypgstac migrate` — manages the `pgstac` schema (STAC Collections + Items)
2. `alembic upgrade head` — manages the `public` schema (users, groups, keywords, RBAC)

In the normal `docker compose up` workflow, the `migrate` service runs both automatically before the backend starts. You only need to run them manually when developing new models 

## Alembic config location

Alembic configuration and migration scripts live at:

```
fair-data-finder/backend/api/alembic/
├── env.py
├── script.py.mako
└── versions/
    └── *.py   ← generated migration files
```

The `alembic.ini` file is at `fair-data-finder/backend/alembic.ini`.

## Creating a new migration

After adding or modifying a SQLModel/SQLAlchemy model, auto-generate a revision:

```bash
docker compose exec backend alembic revision --autogenerate -m "Add new table"
```

Replace `"Add new table"` with a short description of the change. This creates a new file under `api/alembic/versions/`. Always review the generated file before applying it — autogenerate can miss some changes (e.g. custom types, indexes with expressions).

## Applying migrations

```bash
docker compose exec backend alembic upgrade head
```



## Rolling back one step

```bash
docker compose exec backend alembic downgrade -1
```



## Checking current revision

```bash
docker compose exec backend alembic current
```



## Running outside Docker

If you are running the backend with `uv` on your host (against the Compose-mapped Postgres on port 5433), set `DB_CONNECTION_URL` and `PG*` variables accordingly before running alembic commands. See `fair-data-finder/backend/.env.example` for the host-side values.