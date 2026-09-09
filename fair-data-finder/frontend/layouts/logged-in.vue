<template>
  <v-app>
    <v-app-bar>
      <v-tabs
        align-tabs="start"
      >
        <v-tab
          to="/"
        >
          Search
        </v-tab>
        <v-tab
          v-if="isAuthenticated"
          to="/register"
        >
          Register
        </v-tab>
        <v-tab
          v-if="hasPermission('collection:create')"
          to="/domains"
        >
          Domains
        </v-tab>
        <v-tab 
          v-if="hasPermission('keyword:all')"
          to="/keywords"
        >
          Keywords
        </v-tab>
        <v-tab
          v-if="hasPermission('group:read')"
          to="/groups"
        >
          Groups
        </v-tab>
        <v-tab
          v-if="configStore.aboutTabEnabled"
          to="/about"
        >
          About
        </v-tab>
      </v-tabs>
      
     
      <v-spacer />
      <div v-if="isAuthenticated" class="d-flex align-center">
        <span class="text-subtitle2 me-3">{{ displayName }}</span>
        <v-btn
          :loading="isLoading"
          color="error"
          size="small"
          variant="text"
          @click="handleLogout"
        >
          <v-icon class="me-2">
            mdi-logout
          </v-icon>
          Logout
        </v-btn>
      </div>
      <div v-else>
        <v-btn
          :loading="isLoading"
          color="primary"
          variant="text"
          @click="handleLogin"
        >
          <v-icon class="me-2">
            mdi-account
          </v-icon>
          Login
        </v-btn>
      </div>
    </v-app-bar>
    <v-main>
      <slot />
    </v-main>
  </v-app>
</template>

<script setup>
  import { useAuth } from '~/composables/useAuth'
  import { useConfigStore } from '~/stores/config'

  const { 
    isAuthenticated, 
    hasPermission, 
    displayName, 
    login, 
    logout, 
    isLoading,
  } = useAuth()

  const configStore = useConfigStore()

  const handleLogin = () => {
    login()
  }

  const handleLogout = () => {
    logout()
  }
</script>

<style scoped>
/* Vuetify computes v-main's top offset (--v-layout-top) once the app-bar
   registers with the client-side layout system, but during SSR it renders
   as 0px. That gap makes page content render flush under the app bar and
   then jump down as soon as the client corrects it. The app bar here is a
   single fixed-height (64px) row, so pin the fallback to that value; an
   author-stylesheet !important declaration beats Vuetify's non-important
   inline style, and is a no-op once hydration sets the same real value.
*/
.v-main {
  --v-layout-top: 64px !important;
}
</style>