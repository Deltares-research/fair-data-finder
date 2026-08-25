# Architecture Overview

Fair Data Finder is composed of five services orchestrated with Docker Compose for local development. In production each service runs on a dedicated server. See [Deployment](deployment.md) for the production topology.

## Components

- **Database (Postgres + PostGIS)** — stores STAC Collections and Items via the `pgstac` schema, and application data (RBAC, keywords, users) in the `public` schema. See [Database](database.md) for schema details.
- **Backend** — FastAPI app (`dmsapi`), exposes the STAC-compliant REST API on port `8000`. Managed with `uv`. Talks to Postgres via two separate connections: a pgSTAC read/write pool and SQLModel for RBAC/app data.
- **Frontend** — Nuxt 4 app, serves the browser UI on port `3000`. Fetches the OpenAPI schema from the backend at build time to generate a typed API client (`nuxt-open-fetch`), and proxies `/api/`** requests to the backend at runtime.
- **Proxy (Caddy)** — single public entry point. Terminates HTTPS and routes requests by path: `/api/`* → backend, everything else → frontend. Keeping frontend and backend on one origin is required for the Azure SSO session cookie to work.
- **Migrate (one-shot)** — runs `pypgstac migrate && alembic upgrade head` against Postgres on startup, then exits. Ensures the database schema is always up to date before the backend starts.



## Local development (Docker Compose, one machine)

All five services run as containers on the same host, defined in `docker-compose.yml`.

```
                          ┌─────────────────────────────┐
                          │           Browser            │
                          └───────────────┬──────────────┘
                                          │ https://localhost
                                          ▼
                          ┌─────────────────────────────┐
                          │   proxy (Caddy)  :80/:443    │
                          └───────┬───────────────┬──────┘
                   /api/* ────────┘               └──────── everything else
                          ▼                               ▼
            ┌───────────────────────┐        ┌───────────────────────┐
            │   backend (FastAPI)   │        │   frontend (Nuxt)     │
            │        :8000          │        │        :3000          │
            └───────────┬───────────┘        └───────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  postgres (PostGIS)   │
            │        :5432          │
            └───────────┬───────────┘
                        ▲
                        │ runs once, then exits
            ┌───────────────────────┐
            │  migrate (one-shot)   │
            │  pypgstac migrate +   │
            │  alembic upgrade head │
            └───────────────────────┘
```



## Source layout

```
fair-data-finder/        ← all application source lives here
├── backend/             FastAPI app (package: dmsapi), managed with uv
├── frontend/            Nuxt 4 app
├── database/            PostgreSQL + PostGIS + pgSTAC bootstrap SQL
├── proxy/               Caddy configuration and Dockerfile
├── docker-compose.yml   Local development orchestration
├── compose.backend.prod.yml   Production backend deployment
└── compose.frontend.prod.yml  Production frontend deployment
```



## Further reading

- [Deployment](deployment.md) — production topology and deploy steps
- [Database](database.md) — schemas, extensions, connection model
- [STAC API](../stac-api.md) — search endpoint and CQL2 filter usage

