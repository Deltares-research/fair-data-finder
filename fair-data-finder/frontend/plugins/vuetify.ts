// import this after install `@mdi/font` package
import '@mdi/font/css/materialdesignicons.css'

import 'vuetify/styles'
import { createVuetify } from 'vuetify'

export default defineNuxtPlugin((app) => {
  const { public: { theme } } = useRuntimeConfig()

  const vuetify = createVuetify({
    // Vuetify components measure the viewport internally (v-app-bar,
    // v-data-table, v-dialog). Without this the server assumes a desktop
    // viewport and the client re-measures, causing hydration mismatches.
    ssr: true,
    defaults: {
      VAppBar: {
        color: 'surface',
        elevation: 1,
      },
      VBtn: {
        rounded: 'lg',
        style: 'text-transform: none; font-weight: 500; letter-spacing: 0;',
      },
      VCard: {
        rounded: 'xl',
        elevation: 1,
      },
      VDialog: {
        rounded: 'xl',
      },
      VTextField: {
        color: 'primary',
        rounded: 'lg',
      },
      VTextarea: {
        color: 'primary',
        rounded: 'lg',
      },
      VSelect: {
        color: 'primary',
        rounded: 'lg',
      },
      VAutocomplete: {
        color: 'primary',
        rounded: 'lg',
      },
      VCombobox: {
        color: 'primary',
        rounded: 'lg',
      },
      VDataTable: {
        hover: true,
      },
    },
    theme: {
      defaultTheme: 'light',
      themes: {
        light: {
          dark: false,
          colors: {
            primary: theme.primary,
            secondary: theme.secondary,
            background: theme.background,
            surface: theme.surface,
            info: theme.info,
            error: theme.error,
            success: theme.success,
            warning: theme.warning,
            'on-background': theme.onBackground,
            'on-surface': theme.onSurface,
            outline: theme.outline,
          },
        },
      },
    },
  })
  app.vueApp.use(vuetify)
})
