# Fair Data Finder (FDF)

A web application for discovering and managing FAIR geospatial metadata. It exposes a STAC-compliant REST API and a browser UI for searching STAC Items and Collections on a map.

## Quick start

```bash
docker compose up --build
```

Browse to `https://localhost` (accept the self-signed cert once). See [Installation](docs/installation.md) for verification steps and the recommended hot-reload workflow.

## Repository structure

```
fair-data-finder/        ← all application source
├── backend/             FastAPI app (Python, uv)
├── frontend/            Nuxt 4 UI (Node.js, Vue)
├── database/            PostgreSQL + PostGIS bootstrap
├── proxy/               Caddy reverse proxy
└── docker-compose.yml   Local orchestration

docs/                    ← documentation
```

## Documentation

Full documentation lives in [`docs/`](docs/README.md):

- [Installation](docs/installation.md)
- [Architecture overview](docs/architecture/overview.md)
- [Contributing](docs/guides/contributing.md)

## Contributing

Create a branch from `main`, follow [Conventional Commits](https://www.conventionalcommits.org/), and open a pull request. See [Contributing](docs/guides/contributing.md) for details.
