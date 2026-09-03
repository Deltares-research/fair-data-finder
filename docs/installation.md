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


## Feature flags

The application can be deployed either as the full data-management suite or as a
public, search-only portal. This is controlled entirely through environment
variables — no code changes are needed to switch between the two.

**Backend** (`fair-data-finder/backend/.env`):

| Variable              | Default | Effect                                                                                                                    |
| --------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------- |
| `AUTH_ENABLED`        | `true`  | Registers the Microsoft SSO extension. When `false`, no login endpoints exist and the `AZURE_*` variables are unused.       |
| `PUBLIC_READ_ENABLED` | `false` | Exposes the STAC read endpoints (`/search`, `/collections`, `/keywords`, `/conformance`, ...) without an auth cookie.       |

Write endpoints are always protected by RBAC, regardless of these flags.

**Frontend** (`fair-data-finder/frontend/.env`):

These are runtime values, resolved when the container starts rather than when the
image is built, so the same image tag can be promoted between environments.

| Variable                            | Default | Effect                                                       |
| ----------------------------------- | ------- | ------------------------------------------------------------ |
| `NUXT_PUBLIC_AUTH_ENABLED`          | `true`  | Shows the login/logout button and performs the auth check.   |
| `NUXT_PUBLIC_REGISTER_TAB_ENABLED`  | `true`  | Shows the Register tab and enables the `/register/*` routes.  |
| `NUXT_PUBLIC_ADMIN_TABS_ENABLED`    | `true`  | Shows the Domains, Keywords and Groups tabs and their routes. |
| `NUXT_PUBLIC_ABOUT_TAB_ENABLED`     | `false` | Shows the About tab.                                         |

Disabled routes return a 404 even when navigated to directly. The item detail page
`/register/{id}/view` stays reachable regardless of `NUXT_PUBLIC_REGISTER_TAB_ENABLED`, because the
search results link to it.

### Public search-only deployment

Backend `.env`:

```
AUTH_ENABLED=false
PUBLIC_READ_ENABLED=true
```

Frontend `.env`:

```
NUXT_PUBLIC_AUTH_ENABLED=false
NUXT_PUBLIC_REGISTER_TAB_ENABLED=false
NUXT_PUBLIC_ADMIN_TABS_ENABLED=false
NUXT_PUBLIC_ABOUT_TAB_ENABLED=true
```

This yields a Search and About interface with no login, usable by anonymous visitors.
To re-enable dataset registration later, set `AUTH_ENABLED=true` on the backend and
`NUXT_PUBLIC_AUTH_ENABLED=true` on the frontend, together with
`NUXT_PUBLIC_REGISTER_TAB_ENABLED=true` (and `NUXT_PUBLIC_ADMIN_TABS_ENABLED=true` for domain, keyword and
group management), supply the `AZURE_*` credentials and `APP_SECRET_KEY`, and keep
`PUBLIC_READ_ENABLED=true` so that search remains publicly accessible.

