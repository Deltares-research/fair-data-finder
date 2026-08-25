# PostgreSQL provisioning

This folder contains one SQL file used to bootstrap PostgreSQL for the Fair Data Finder:
`init-extensions.sql` installs the required PostgreSQL extensions and runs once per cluster.

---

## Development (Docker Compose)

`init-extensions.sql` is automatically bind-mounted into the `postgis/postgis` container
at `/docker-entrypoint-initdb.d/01-init-extensions.sql` and executed once when the
Docker volume is first created.

To trigger a re-run (e.g. after changing the file), destroy the volume:

```bash
docker compose down -v
docker compose up
```

The `migrate` Compose service then runs `pypgstac migrate && alembic upgrade head`
against the fresh cluster before the backend starts.
