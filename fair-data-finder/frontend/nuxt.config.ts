import vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'

export default defineNuxtConfig({
  imports: {
    autoImport: true,
  },
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  css: ['mapbox-gl/dist/mapbox-gl.css'],
  build: {
    transpile: ['vuetify'],
  },
  modules: [
    '@pinia/nuxt',
    'nuxt-open-fetch',
    (_options, nuxt) => {
      nuxt.hooks.hook('vite:extendConfig', (config) => {
        // @ts-expect-error
        config.plugins.push(vuetify({ autoImport: true }))
      })
    }
  ],
  vite: {
    vue: {
      template: {
        transformAssetUrls, // To resolve relative asset URLs
      },
    },
  },

  // Every value below is resolved when the container starts, not when the
  // image is built, so the same image tag can be promoted between
  // environments. Defaults are the neutral "nothing configured" values.
  runtimeConfig: {
    // Server-only; never serialised into the browser payload.
    // Set per environment with NUXT_INTERNAL_API_BASE_URL.
    internalApiBaseUrl: '',

    // Serialised into the browser payload and visible in devtools.
    // Set per environment with NUXT_PUBLIC_*.
    public: {
      aboutTabEnabled: false,
      mapboxToken: '',
    },
  },

  openFetch: {
    clients: {
      api: {
        // Read from the committed schema rather than fetched from a running
        // backend, so the build needs no network access and no deployment URL.
        // Refresh it with `npm run schema:update` when the API changes.
        schema: './openapi/api.json',
        baseURL: '/api',
      },
    },
  },

  nitro: {
    // Dev server only; Nitro drops this from production builds. It serves the
    // browser's relative /api calls while there is no nginx in front of Nuxt.
    // In production nginx owns /api, and SSR goes straight to the backend via
    // runtimeConfig.internalApiBaseUrl.
    devProxy: {
      '/api': {
        target: process.env.NUXT_INTERNAL_API_BASE_URL || 'http://localhost:8000/api',
        changeOrigin: true,
      },
    },
  },

})
