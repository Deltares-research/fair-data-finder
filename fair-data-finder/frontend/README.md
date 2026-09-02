# Frontend

Nuxt 4 application that serves the browser UI. Uses [Vuetify](https://vuetifyjs.com/) for components, [Pinia](https://pinia.vuejs.org/) for state, and [Mapbox GL](https://docs.mapbox.com/mapbox-gl-js/) for the map.

`nuxt-open-fetch` generates the typed API client from `openapi/api.json`, which is committed to the repository. The build therefore needs no backend and no network access. Refresh the schema whenever the backend API changes:

```bash
npm run schema:update              # reads http://localhost:8000
API_URL=http://host:8000 npm run schema:update
```

## Environment setup

```bash
cp .env.example .env
```

The image contains no environment-specific values; all three variables are read when the process starts, so the same image can be promoted between environments. `NUXT_PUBLIC_*` values are serialised into the HTML payload and are readable in browser devtools — never put a secret in one.

| Variable | Scope | Description |
|----------|-------|-------------|
| `NUXT_INTERNAL_API_BASE_URL` | Runtime, server-only | Where SSR reaches the backend. `http://localhost:8000/api` natively, `http://backend:8000/api` in Docker. In dev it is also the Nitro dev-proxy target for the browser's `/api` calls. |
| `NUXT_PUBLIC_MAPBOX_TOKEN` | Runtime, public | Mapbox public access token (`pk.*`); the map will not load without it. Restrict it by URL in the Mapbox dashboard. |
| `NUXT_PUBLIC_ABOUT_TAB_ENABLED` | Runtime, public | Shows the About tab. |

## Install dependencies

```bash
npm install
```

## Development server

```bash
npm run dev
```

The app is available at `http://localhost:3000`. The backend must be running for API calls to work. The recommended setup is:

```bash
# Terminal 1 — backend + database + proxy in Docker
docker compose up postgres migrate backend proxy

# Terminal 2 — hot-reload frontend
npm run dev
```

See [Installation](../../docs/installation.md) for the full workflow and SSO notes.

## Build for production

```bash
npm run build
```

## Preview production build locally

```bash
npm run preview
```

## Linting

```bash
npx eslint .
```

## Folder structure

```
frontend/
├── components/      Vue components
├── composables/     Reusable Vue composables
├── configuration/   App-level configuration files
├── content/         Static Markdown content served by the app
├── layouts/         Nuxt layout files
├── pages/           Route pages (about, domains, groups, keywords, register, …)
├── plugins/         Nuxt plugins
├── public/          Static assets
├── requests/        API request helpers
├── server/          Nuxt server routes
├── stores/          Pinia stores
├── utils/           Utility functions
├── app.vue          Root component
├── nuxt.config.ts   Nuxt configuration
└── .env.example     Environment variable template
```

## Further reading

- [Architecture overview](../../docs/architecture/overview.md)
- [Installation](../../docs/installation.md)
- [STAC API](../../docs/stac-api.md)
