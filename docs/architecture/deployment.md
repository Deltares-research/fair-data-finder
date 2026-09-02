# Deployment

## Production topology

Local and production topologies differ — there is no local Caddy in production, and Postgres is managed by ICT. Production does **not** override `docker-compose.yml`; it uses a single standalone compose file, `deployment/docker-compose.prod.yml`.

The backend and frontend containers run on the **same host and the same Docker network**. This is required, not incidental: Nuxt server-side rendering calls the backend directly at `http://backend:8000/api`, which only resolves if both containers share a Compose network. See "SSR requires a shared network" below.

```
                          ┌─────────────────────────────┐
                          │           Browser            │
                          └───────────────┬──────────────┘
                                          │ https://<public-domain>
                                          ▼
                ┌────────────────────────────────────────────────┐
                │              Application server                 │
                │                                                  │
                │   ┌───────────────┐                             │
                │   │ nginx (:443)  │  TLS + path routing         │
                │   └───┬───────┬───┘                             │
                │       │ /     │ /api                            │
                │       ▼       ▼                                 │
                │  ┌─────────┐ ┌──────────────┐                   │
                │  │  Nuxt   │ │   FastAPI    │                   │
                │  │ (:3000) │ │   (:8000)    │                   │
                │  └────┬────┘ └──────┬───────┘                   │
                │       │             ▲                           │
                │       └─────────────┘                           │
                │     SSR: http://backend:8000/api                │
                │     (Docker network, never via nginx)           │
                └───────────────────┬────────────────────────────┘
                                    │ DB_CONNECTION_URL over internal network
                                    ▼
                ┌────────────────────────────────────────────────┐
                │              Database server                    │
                │          Postgres + PostGIS (:5432)             │
                └────────────────────────────────────────────────┘

    Migrations (pypgstac migrate + alembic upgrade head) run as the
    `migrate` service on each deploy, before the backend starts.
```

## Compose file

| Component | File | Env template |
|--------|------|--------------|
| Backend + frontend | `deployment/docker-compose.prod.yml` | `backend/.env.example` and `frontend/.env.example` → `.env` |
| Database | none | native PostgreSQL 16 + PostGIS (ICT-managed) |

## Deploy steps

```bash
cd deployment
cp ../fair-data-finder/backend/.env.example .env
# append the frontend variables and edit secrets, DB_CONNECTION_URL, APP_DOMAIN, etc.

export HARBOR_REGISTRY=<registry-host>
export PROJECT_NAME=<backend-image-project-name>
export IMAGE_TAG=<git-sha>
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

The `migrate` service runs `pypgstac migrate && alembic upgrade head` automatically and the backend waits for it to complete successfully.

## SSR requires a shared network

The frontend makes two kinds of request, and they take different paths:

- **Browser requests** always use the relative URL `/api`, so they go through nginx.
- **SSR requests** use `NUXT_INTERNAL_API_BASE_URL`, set to `http://backend:8000/api`, and go straight over the Docker network. They never touch nginx.

If the backend is unreachable at that address, the frontend does **not** fail loudly. It returns HTTP 200 with a page rendered from empty data, and the browser does not retry — so an authenticated user sees a permanently logged-out page. Requests also hang until the connection times out, which was measured at roughly 28 seconds per render.

Consequences:

- Do not split the backend and frontend across separate hosts without giving them a shared Docker network (for example an `external` network) and updating `NUXT_INTERNAL_API_BASE_URL` accordingly.
- Health checks that only assert HTTP 200 will not catch a misconfigured `NUXT_INTERNAL_API_BASE_URL`. After deploying, verify that a logged-in page server-renders the username.

## Container images

Images are pulled from the registry set via `HARBOR_REGISTRY`:

- `${HARBOR_REGISTRY}/fair-data-finder/backend:${IMAGE_TAG}`
- `${HARBOR_REGISTRY}/fair-data-finder/frontend:${IMAGE_TAG}`

Built from the Dockerfiles' `production` / `run-prod` targets.

## Notes

- If the hosting organisation already provides a reverse proxy or load balancer with TLS termination and path-based routing, it can replace the Caddy instance — the requirement is that *something* terminates TLS and keeps frontend + backend under one public origin.
- Docker is optional in production: the backend requires Python 3.12 + `uv`, and the frontend requires Node.js 22 — both can run as plain systemd services.
- Size the backend host for ingestion load (bulk STAC writes / larger payloads), not only lightweight UI API reads.
