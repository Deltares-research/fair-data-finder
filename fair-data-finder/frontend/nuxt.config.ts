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

  runtimeConfig: {
    public: {
      aboutTabEnabled: process.env.ABOUT_TAB_ENABLED === 'true',
      // Opt-out flags: unset keeps the full Fair Data Finder behaviour.
      authEnabled: process.env.AUTH_ENABLED !== 'false',
      registerTabEnabled: process.env.REGISTER_TAB_ENABLED !== 'false',
      adminTabsEnabled: process.env.ADMIN_TABS_ENABLED !== 'false',
    },
  },

  openFetch: {
    clients: {
      api: {
        schema: process.env.API_URL + "/api/api",
        baseURL: "/api",
      },
    },
  },

  routeRules: {
    "/api/**": {
      proxy: process.env.API_URL + "/api/**",
      headers: {
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Allow-Origin': 'http://localhost:3000',
      }
    },
  },

})
