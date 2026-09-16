import vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'

export default defineNuxtConfig({
  imports: {
    autoImport: true,
  },
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  css: [
    'mapbox-gl/dist/mapbox-gl.css',
    '~/assets/css/app.css',
  ],
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

      // Branding shown in the app bar logo. Override per environment with
      // NUXT_PUBLIC_BRANDING_APP_NAME, NUXT_PUBLIC_BRANDING_TAGLINE and
      // NUXT_PUBLIC_BRANDING_LOGO_URL (path/URL to a custom logo image;
      // leave empty to use the built-in icon).
      branding: {
        appName: 'Fair Data Finder',
        tagline: 'Discover · Share · Reuse',
        logoUrl: '',
      },

      // Vuetify theme colors. Override per environment with
      // NUXT_PUBLIC_THEME_PRIMARY, NUXT_PUBLIC_THEME_SECONDARY, etc.
      theme: {
        primary: '#2563EB',
        secondary: '#0F766E',
        background: '#F8FAFC',
        surface: '#FFFFFF',
        info: '#0284C7',
        success: '#16A34A',
        warning: '#D97706',
        error: '#DC2626',
        onBackground: '#111827',
        onSurface: '#111827',
        outline: '#E2E8F0',
      },
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
