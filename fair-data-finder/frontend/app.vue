<template>
  <div
    v-if="isLoading"
    class="d-flex justify-center align-center"
    style="height: 100vh;"
  >
    <v-progress-circular
      indeterminate
      color="primary"
      size="64"
    />
  </div>
  <NuxtLayout v-else :name="layoutName">
    <!-- Keeps the Search page (and its Mapbox map) alive in memory when
         navigating to other tabs, instead of destroying/recreating the map
         on every visit. Other pages are unaffected and unmount as normal. -->
    <NuxtPage :keepalive="{ include: ['index'] }" />
  </NuxtLayout>
</template>

<script setup>
  import { useAuth } from '~/composables/useAuth'
  import { computed } from 'vue'
  import { useNuxtApp, callOnce } from '#app'

  const nuxtApp = useNuxtApp()
  const { isAuthenticated, isLoading, checkAuth } = useAuth()

  // Runs during SSR only; the resulting auth and permission state reaches the
  // client through the Nuxt payload, so hydration does not repeat /auth/me
  // and /permissions.
  await callOnce('check-auth', () => checkAuth(nuxtApp.$api))

  const layoutName = computed(() => {
    if (isAuthenticated.value) {
      return 'logged-in'
    }
    return 'default'
  })
</script>
