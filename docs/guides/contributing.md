# Contributing

## Before you start

Make sure the full stack runs locally before submitting a change:

```bash
docker compose up --build
```

See [Installation](../installation.md) for verification steps.

## Branching

1. Every pull request goes into dev. Write Closes #41 in it so the ticket and the pull request are linked. After the merge, move the ticket to In Dev. It stays open.
2. When dev is ready for release, open one pull request from dev into main.
3. That release pull request lists all the tickets it releases:
Release 2026-12

Closes #41, closes #42, closes #47
4. When it is merged, GitHub closes all those tickets. You then move them from In Dev to Done, unless the board's automation does it for you.


- `main` is what runs in production. `dev` is the integration branch. We have different workflows. 
- Create a feature branch from `dev` and open the pull request back into `dev`.
- When a release is ready, `dev` is merged into `main` through a pull request.

```bash
git checkout dev
git pull
git checkout -b feat/your-feature-name
```

## Tickets and the board

Every change belongs to a ticket on the [Fair Data Finder Board](https://github.com/orgs/Deltares-research/projects/86).

| Status | Meaning |
|---|---|
| Backlog | Not planned yet |
| Ready | Planned and clear enough to start |
| In progress | Someone is working on it |
| In review | Pull request is open |
| In Dev | Merged into `dev`, not yet in `main` |
| Done | Merged into `main` (released) |

- Write `Closes #<number>` in the pull request description.
- After merging into `dev`, move the ticket to **In Dev**. It stays open.
- GitHub only closes tickets automatically for pull requests merged into `main`, so list all released tickets (`Closes #41, closes #42`) in the release pull request from `dev` into `main`. It only works when the pull request is merged into main.
- To see what is waiting for release: `git log main..dev --oneline`.

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

- Link the ticket with `Closes #<number>`.
- Keep PRs focused — one logical change per PR.
- Update or add documentation if your change affects developer-facing behaviour.
- Ensure `docker compose exec backend uv run pytest -v` passes before opening a PR.

## Code style

- **Backend:** Python 3.12, type hints required. Run `mypy` for type checking.
- **Frontend:** Vue 3 with `<script setup>` + TypeScript. Run `npx eslint .` for linting.

See `.github/copilot-instructions.md` for the full coding conventions used in this project.
