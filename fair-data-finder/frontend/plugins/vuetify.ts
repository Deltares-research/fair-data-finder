// import this after install `@mdi/font` package
import '@mdi/font/css/materialdesignicons.css'

import 'vuetify/styles'
import { createVuetify } from 'vuetify'

export default defineNuxtPlugin((app) => {
  const vuetify = createVuetify({
    // Vuetify components measure the viewport internally (v-app-bar,
    // v-data-table, v-dialog). Without this the server assumes a desktop
    // viewport and the client re-measures, causing hydration mismatches.
    ssr: true,
  })
  app.vueApp.use(vuetify)
})
