# Migrating Production Data to Local pgSTAC

The script `fair-data-finder/backend/scripts/migrate_to_pgstac.py` fetches all STAC Collections and Items from the live production API and loads them into your local pgSTAC database.

## Run inside the backend container

The container already has all required dependencies installed:

```bash
docker compose exec backend uv run python scripts/migrate_to_pgstac.py 
```

This connects to the production API and loads data into the database

## Options


| Flag              | Default                                              | Description                                               |
| ----------------- | ---------------------------------------------------- | --------------------------------------------------------- |
| `--source-url`    | `your url`                                           | Source STAC API base URL                                  |
| `--database-url`  | `postgresql://postgres:password@localhost:5432/stac` | pgSTAC connection string                                  |
| `--dms-token`     | *(empty)*                                            | Auth cookie value for the source API if needed            |
| `--page-size`     | `500`                                                | Items per page when paginating                            |
| `--request-delay` | `0.1`                                                | Seconds to wait between paginated requests                |
| `--dry-run`       | *(off)*                                              | Fetch and write NDJSON files but skip loading into pgSTAC |


