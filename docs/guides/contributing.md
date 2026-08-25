# Contributing

## Before you start

Make sure the full stack runs locally before submitting a change:

```bash
docker compose up --build
```

See [Installation](../installation.md) for verification steps.

## Branching

Create a feature branch from `main`:

```bash
git checkout -b feat/your-feature-name
```

## Commit messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add keyword search filter
fix: correct OAuth redirect URI on staging
docs: update local SSO setup guide
refactor: extract search composable
chore: upgrade Nuxt to 4.2
```

Common prefixes: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`.

## Pull requests

- Keep PRs focused — one logical change per PR.
- Update or add documentation if your change affects developer-facing behaviour.
- Ensure `docker compose exec backend uv run pytest -v` passes before opening a PR.

## Code style

- **Backend:** Python 3.12, type hints required. Run `mypy` for type checking.
- **Frontend:** Vue 3 with `<script setup>` + TypeScript. Run `npx eslint .` for linting.

See `.github/copilot-instructions.md` for the full coding conventions used in this project.
