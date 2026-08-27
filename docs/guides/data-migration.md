# Migrating Production Data to Local pgSTAC

The script `fair-data-finder/backend/scripts/migrate_to_pgstac.py` fetches all STAC Collections and Items from the live production API and loads them into your local pgSTAC database.

## Run inside the backend container

The container already has all required dependencies installed:

```bash
docker compose exec backend uv run python scripts/migrate_to_pgstac.py \
  --source-url https://devs4w.deltares-fairdata.com/api \
  --database-url postgresql://postgres:postgres@postgres:5432/postgres
```

This fetches STAC Collections and Items from the production `--source-url` API and
loads them into the pgSTAC database identified by `--database-url`.

`--database-url` is a standard PostgreSQL connection string:
`postgresql://<user>:<password>@<host>:<port>/<dbname>`.

- When running via `docker compose exec backend`, use host `postgres` (the compose
  service name) with the credentials from `backend/.env` (`PG*` variables).
- When running from the host machine against the compose-mapped port, use
  `localhost:5433` instead.

## Options


| Flag              | Default                                              | Description                                               |
| ----------------- | ---------------------------------------------------- | --------------------------------------------------------- |
| `--source-url`    | `your url`                                           | Source STAC API base URL                                  |
| `--database-url`  | `postgresql://postgres:password@localhost:5432/stac` | pgSTAC connection string                                  |
| `--dms-token`     | *(empty)*                                            | Auth cookie value for the source API if needed            |
| `--page-size`     | `500`                                                | Items per page when paginating                            |
| `--request-delay` | `0.1`                                                | Seconds to wait between paginated requests                |
| `--dry-run`       | *(off)*                                              | Fetch and write NDJSON files but skip loading into pgSTAC |


