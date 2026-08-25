# Installation

## Prerequisites to run

- [Docker](https://docs.docker.com/get-docker/)

## Start the full stack

```bash
docker compose up --build
```

Services start in dependency order: `postgres` → `migrate` → `backend` → `frontend` → `proxy`.

The `migrate` service runs `pypgstac migrate && alembic upgrade head` against Postgres before the backend starts, then exits.

Browse the app at `https://localhost`. Accept the self-signed certificate warning once.

## Verify the app is running


| URL                                                                              | Expected                               |
| -------------------------------------------------------------------------------- | -------------------------------------- |
| [http://localhost:8000/api/_mgmt/health](http://localhost:8000/api/_mgmt/health) | `{"status":"UP"}`                      |
| [http://localhost:8000/api/](http://localhost:8000/api/)                         | STAC landing page                      |
| [http://localhost:8000/api/search](http://localhost:8000/api/search)             | Empty search results                   |
| [http://localhost:8000/api/api.html](http://localhost:8000/api/api.html)         | Swagger UI (interactive API docs)      |
| [http://localhost:8000/api/api](http://localhost:8000/api/api)                   | OpenAPI JSON schema                    |
| [http://localhost:3000](http://localhost:3000)                                   | Frontend loads                         |
| [https://localhost](https://localhost)                                           | App via Caddy (required for SSO login) |




## Stop and clean up

Stop all services:

```bash
docker compose down
```

Remove orphaned containers from old compose definitions:

```bash
docker compose down --remove-orphans
```

Destroy the database volume (triggers a full re-initialisation on next `up`):

```bash
docker compose down -v
```



## Frontend hot-reload (recommended for active development)

Run the backend and proxy in Docker and the frontend natively for fast hot-module replacement:

```bash
# Terminal 1 — backend + database + proxy
docker compose up postgres migrate backend proxy

# Terminal 2 — hot-reload frontend
cd fair-data-finder/frontend
npm install
npm run dev
```

The app is available at `http://localhost:3000`.

Set `FRONTEND_URL=http://localhost:3000/` in `fair-data-finder/backend/.env` so that after the OAuth login callback the backend redirects back to the dev server.

## Backend-only changes

The backend container has `RELOAD=true` set in `.env.example`, so FastAPI restarts automatically when Python files change inside the container. For a complete rebuild:

```bash
docker compose up --build backend
```



## Logging in (SSO)

Login requires HTTPS. The `proxy` (Caddy) service handles this locally — it must be running for login to work:

```bash
docker compose up postgres migrate backend proxy
```

**Azure redirect URI:** someone with access to the Azure App Registration must add:

```
https://localhost/api/auth/callback
```

**Key env vars** (see `fair-data-finder/backend/.env.example` for the full reference):


| Variable       | Full Docker | Frontend hot-reload (`npm run dev`) |
| -------------- | ----------- | ----------------------------------- |
| `APP_DOMAIN`   | `localhost` | `localhost`                         |
| `FRONTEND_URL` | optional    | `http://localhost:3000/` (required) |


