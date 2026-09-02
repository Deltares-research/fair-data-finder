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
    <NuxtPage />
  </NuxtLayout>
</template>

<script setup>
  import { useAuth } from '~/composables/useAuth'
  import { computed } from 'vue'
  import { useNuxtApp, callOnce } from '#app'

  const nuxtApp = useNuxtApp()
  const { authEnabled, isAuthenticated, isLoading, checkAuth } = useAuth()

  // Runs during SSR only; the resulting auth and permission state reaches the
  // client through the Nuxt payload, so hydration does not repeat /auth/me
  // and /permissions.
  await callOnce('check-auth', () => checkAuth(nuxtApp.$api))

  const layoutName = computed(() => {
    if (authEnabled.value && isAuthenticated.value) {
      return 'logged-in'
    }
    return 'default'
  })
</script>
