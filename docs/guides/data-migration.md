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

## Removing non-harvested stars4water Items

`fair-data-finder/backend/scripts/remove_non_harvested_items.py` selects only
the `datarecords.csv` rows with `isharvested` set to `n`. It is scoped to the
`stars4water` collection by default.

Run a dry run first. The bind mount makes the CSV available to the temporary
backend container and persists the report in the repository root:

```powershell
$databaseUrl = 'postgresql://<user>:<url-encoded-password>@<host>:5432/<database>'
docker compose -f fair-data-finder\docker-compose.yml run --rm --no-deps `
  -v "${PWD}:/workspace" `
  backend uv run python scripts/remove_non_harvested_items.py `
  --csv /workspace/datarecords.csv `
  --database-url $databaseUrl `
  --report /workspace/removal_report.json
```

Review `removal_report.json`. To delete only the IDs reported as found, rerun
the command with `--apply`:

```powershell
docker compose -f fair-data-finder\docker-compose.yml run --rm --no-deps `
  -v "${PWD}:/workspace" `
  backend uv run python scripts/remove_non_harvested_items.py `
  --csv /workspace/datarecords.csv `
  --database-url $databaseUrl `
  --report /workspace/removal_report.json `
  --apply
```

The script runs the deletion in a transaction and verifies that no targeted
IDs remain in `pgstac.items` for the selected collection.

## Converting ISO 19139 metadata to STAC Items

`fair-data-finder/backend/scripts/iso19139_to_stac.py` converts ISO 19139
`gmd:MD_Metadata` files into STAC 1.0 Item JSON. It uses the ISO
`fileIdentifier` as the Item ID and extracts the citation title, abstract,
bounding box, dates, language, keywords, topics, status, and distribution
links.

```powershell
docker compose -f fair-data-finder\docker-compose.yml run --rm --no-deps `
  -v "${PWD}:/workspace" `
  backend uv run python scripts/iso19139_to_stac.py `
  /workspace/metadata_s4w `
  /workspace/stac_output
```

Review the generated files in `stac_output` before uploading them. The
converter does not write to the database.
