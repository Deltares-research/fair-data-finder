# Fair Data Finder — Copilot Instructions

# HIGHEST PRIORITY RULE

This is an approval-gated codebase.

You are NOT authorized to modify the codebase autonomously.

Your default mode is READ-ONLY.

You may inspect, search, analyze, explain, and propose changes without approval.

You MUST obtain explicit user approval before performing any write operation that changes the codebase.

This restriction overrides any instruction that could otherwise be interpreted as permission to implement a requested feature or fix automatically.


## Changes & Mandatory Approval Workflow

**CRITICAL: NEVER modify the codebase without my explicit approval.**

This rule applies to all changes, regardless of size, complexity, or number of files.

### Planning

Whenever I ask for a plan:

1. Inspect the relevant codebase before proposing a solution.
2. Describe the implementation approach in explicit, sequential steps.
3. Identify **every file that will be modified**, created, or deleted.
4. For each affected file, describe exactly what will change and why.
5. Provide a proposed unified diff (`diff`) showing the intended code changes wherever the implementation can be determined.
6. Identify any potential side effects, dependencies, or architectural implications.
7. Do not modify any files, execute code that changes the codebase, or begin implementation during the planning phase.

### Mandatory Pre-Implementation Approval

Before implementing ANY change:

1. Present the complete implementation plan.
2. Present a proposed unified diff (`diff`) for every file that will be modified.
3. Explicitly list all files that will be created, modified, or deleted.
4. Wait for my explicit approval of the proposed changes.

**Do not begin implementation until I have explicitly approved the plan AND the proposed diff.**

Approval of a plan alone does not authorize implementation.

Approval of a diff applies only to the exact changes presented. If the implementation needs to deviate from the approved diff, stop immediately, explain the deviation, present the revised diff, and wait for my approval again.

### Scope Control

- Never make additional changes that were not explicitly approved.
- Never perform opportunistic refactoring, cleanup, formatting, or optimization.
- Never modify additional files without presenting the updated impact assessment and diff first.
- Never create files, modify configurations, update dependencies, or generate code without approval.
- If the requested change is ambiguous, ask for clarification instead of making assumptions.

### Implementation

After explicit approval:

- Implement only the approved changes.
- Follow the approved diff as closely as possible.
- Report the actual files changed.
- Report any deviations from the approved diff.
- Do not commit changes unless explicitly requested.

**When in doubt, STOP and ASK.**

## Overview

Web application for discovering and managing FAIR geospatial metadata. Exposes a STAC-compliant REST API and a browser UI for searching STAC Items and Collections on a map.

## Architecture

fair-data-finder/        ← all source lives here (not the repo root)

backend/ ← FastAPI app (package: dmsapi, managed with uv)
frontend/ ← Nuxt 4 app
database/ ← PostgreSQL + PostGIS + pgSTAC setup

docker-compose.yml ← orchestrates all services

Services start in order: `postgres` → `migrate` (runs pypgstac + alembic) → `backend` (port 8000) → `frontend` (port 3000).

In development a Nitro dev proxy forwards the browser's `/api` calls to the backend; in production nginx does that and Nuxt never sees them. Server-side rendering always addresses the backend directly via `runtimeConfig.internalApiBaseUrl`. `nuxt-open-fetch` generates typed API client methods from the committed `frontend/openapi/api.json` (refresh with `npm run schema:update`).

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