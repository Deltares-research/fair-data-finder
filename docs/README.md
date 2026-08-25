# Documentation

This is the single source of truth for Fair Data Finder developer documentation.

## Getting started

| Document | Description |
|----------|-------------|
| [Installation](installation.md) | Start the full stack with Docker Compose, frontend hot-reload workflow, verify, stop and clean up, logging in with SSO |

## Architecture

| Document | Description |
|----------|-------------|
| [Overview](architecture/overview.md) | Components, local Docker Compose diagram, source layout |
| [Deployment](architecture/deployment.md) | Production topology, compose files, deploy steps |
| [Database](architecture/database.md) | Schemas, PostgreSQL extensions, connection model |

## API

| Document | Description |
|----------|-------------|
| [STAC API](stac-api.md) | Search endpoint, CQL2 filter extension, examples |

## Guides

| Document | Description |
|----------|-------------|
| [Migrations](guides/migrations.md) | Creating and applying Alembic migrations |
| [Testing](guides/testing.md) | Running the backend test suite |
| [Data migration](guides/data-migration.md) | Loading production STAC data into local pgSTAC |
| [Contributing](guides/contributing.md) | Branching, commit messages, PR guidelines |

## User manual

The end-user manual lives in [`manual/`](manual/README.md). It is written in Quarto and can be rendered to HTML or PDF.
