# Deployment

## Production topology

Local and production topologies differ — services run on separate hosts, there is no local Caddy, and Postgres is managed by ICT. Production does **not** override `docker-compose.yml`. Each server gets its own slim standalone compose file.

```
                          ┌─────────────────────────────┐
                          │           Browser            │
                          └───────────────┬──────────────┘
                                          │ https://<public-domain>
                                          ▼
                ┌────────────────────────────────────────────────┐
                │         Frontend server (public-facing)         │
                │                                                  │
                │   ┌───────────────┐      ┌────────────────┐     │
                │   │ Caddy (:443)  │─────▶│ Nuxt (:3000)   │     │
                │   │ TLS + routing │      └────────────────┘     │
                │   └───────┬───────┘                             │
                └───────────┼──────────────────────────────────────┘
                 /api/* over internal network
                            ▼
                ┌────────────────────────────────────────────────┐
                │         Backend server (internal only)          │
                │            FastAPI (:8000, via uv)              │
                └───────────────────┬────────────────────────────┘
                                    │ DB_CONNECTION_URL over internal network
                                    ▼
                ┌────────────────────────────────────────────────┐
                │              Database server                    │
                │          Postgres + PostGIS (:5432)             │
                └────────────────────────────────────────────────┘

    Migrations (pypgstac migrate + alembic upgrade head) are run once
    (and on each deploy) from the backend server against the database
    server.
```

## Compose files per server

| Server | File | Env template |
|--------|------|--------------|
| Backend | `compose.backend.prod.yml` | `backend/.env.example` → `backend/.env` |
| Frontend | `compose.frontend.prod.yml` | `frontend/.env.example` → `frontend/.env` |
| Database | none | native PostgreSQL 16 + PostGIS (ICT-managed) |

## Deploy steps

**Backend host:**

```bash
cp fair-data-finder/backend/.env.example fair-data-finder/backend/.env
# edit secrets, DB_CONNECTION_URL, APP_DOMAIN, etc.

export HARBOR_REGISTRY=<registry-host>
export IMAGE_TAG=<git-sha>
docker compose -f compose.backend.prod.yml pull
docker compose -f compose.backend.prod.yml up -d

# After first deploy and on every schema change:
docker compose -f compose.backend.prod.yml run --rm backend \
  sh -c "pypgstac migrate && alembic upgrade head"
```

**Frontend host:**

```bash
cp fair-data-finder/frontend/.env.example fair-data-finder/frontend/.env

export HARBOR_REGISTRY=<registry-host>
export IMAGE_TAG=<git-sha>
docker compose -f compose.frontend.prod.yml pull
docker compose -f compose.frontend.prod.yml up -d
```

## Container images

Images are pulled from the registry set via `HARBOR_REGISTRY`:

- `${HARBOR_REGISTRY}/fair-data-finder/backend:${IMAGE_TAG}`
- `${HARBOR_REGISTRY}/fair-data-finder/frontend:${IMAGE_TAG}`

Built from the Dockerfiles' `production` / `run-prod` targets.

## Notes

- If the hosting organisation already provides a reverse proxy or load balancer with TLS termination and path-based routing, it can replace the Caddy instance — the requirement is that *something* terminates TLS and keeps frontend + backend under one public origin.
- Docker is optional in production: the backend requires Python 3.12 + `uv`, and the frontend requires Node.js 22 — both can run as plain systemd services.
- Size the backend host for ingestion load (bulk STAC writes / larger payloads), not only lightweight UI API reads.
