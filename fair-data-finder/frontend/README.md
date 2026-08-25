# Frontend

Nuxt 4 application that serves the browser UI. Uses [Vuetify](https://vuetifyjs.com/) for components, [Pinia](https://pinia.vuejs.org/) for state, and [Mapbox GL](https://docs.mapbox.com/mapbox-gl-js/) for the map.

The OpenAPI schema is fetched from the backend at build time (`API_URL + "/api/api"`) and used by `nuxt-open-fetch` to generate typed API client methods.

## Environment setup

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `API_URL` | Backend base URL. Use `http://localhost:8000` when running the frontend natively with `npm run dev`, or `http://backend:8000` inside Docker. |
| `VITE_MAPBOX_TOKEN` | Mapbox public access token — required for the map to load. |

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
