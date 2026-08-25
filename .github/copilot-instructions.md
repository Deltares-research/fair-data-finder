# Fair Data Finder — Copilot Instructions

## Overview

Web application for discovering and managing FAIR geospatial metadata. Exposes a STAC-compliant REST API and a browser UI for searching STAC Items and Collections on a map.

## Architecture

fair-data-finder/        ← all source lives here (not the repo root)

backend/ ← FastAPI app (package: dmsapi, managed with uv)
frontend/ ← Nuxt 4 app
database/ ← PostgreSQL + PostGIS + pgSTAC setup

docker-compose.yml ← orchestrates all services

Services start in order: `postgres` → `migrate` (runs pypgstac + alembic) → `backend` (port 8000) → `frontend` (port 3000).

The frontend proxies `/api/**` to the backend. The OpenAPI schema is fetched at build time (`API_URL + "/api/api"`) and used by `nuxt-open-fetch` to generate typed API client methods.

## General Editing Philosophy

- Make the smallest possible change that satisfies the request.
- Prefer modifying existing code over introducing new abstractions.
- Preserve the project's existing coding style and architecture.
- Do not perform unrelated refactoring.
- Do not rename files, modules, classes or functions unless explicitly requested.
- Reuse existing utilities, helper functions and patterns whenever possible.
- If multiple implementations already exist, follow the established project convention rather than introducing a new one.

## Changes

Before making changes affecting more than three files or multiple modules:

1. Briefly explain the implementation approach.
2. List the files that will be modified.
3. Wait for confirmation before making the changes.

## Dependencies

- Do not introduce new Python or JavaScript dependencies unless explicitly requested.
- Prefer existing project libraries and utilities.

## Architecture

### Dual-database pattern (backend)

The backend uses two separate database connections:

- pgSTAC (`app.state.readpool` / `writepool`) for STAC Collections, Items and Search.
- SQLModel for RBAC entities and application data.

Never mix responsibilities between these two database layers.

### Extension pattern (backend)

Each feature domain is implemented as a FastAPI extension under `api/extensions/`.

Examples:

- KeywordExtension
- RBACExtension
- SSOAuthExtension

New API functionality should follow this extension pattern unless there is a strong reason not to.

### RBAC

Every write endpoint must validate permissions through the `RBACClient`.

Never bypass RBAC checks.

## Backend Conventions

- Use `uv` for dependency management.
- Type hints are required on every function.
- All FastAPI route handlers must include OpenAPI docstrings.
- Never expose raw PostGIS or pgSTAC exceptions.
- Wrap backend errors using `api/core/errors.py`.
- Follow STAC naming conventions.
- Spatial responses must include CRS (default EPSG:4326).
- Access configuration through `Settings.get()`.

### Logging

- Use the project's existing logging infrastructure.
- Never use `print()` for debugging or logging.

## Frontend Conventions

- Use `<script setup>` only.
- Never use the Vue Options API.
- State belongs in Pinia stores.
- Use the generated `useApiClient()` instead of raw `fetch`.
- Respect existing store and composable patterns.
- Do not introduce new stores or composables unless there is a clear architectural reason.

## Testing

- Tests use SQLite and mocked pgSTAC.
- Fixtures should remain `scope="function"`.
- Async tests use `pytest-asyncio`.
- Prefer running only the tests relevant to the modified code.
- Do not run the full test suite unless requested.

## Documentation

Update documentation only when functionality changes.

Do not rewrite documentation for style or wording unless explicitly requested.

## Git

Use Conventional Commits:

- feat:
- fix:
- docs:
- refactor:
- chore:
- test:

Do not create commits unless explicitly requested.