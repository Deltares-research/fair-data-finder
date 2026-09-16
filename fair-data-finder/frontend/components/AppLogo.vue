<template>
  <div class="d-flex align-center app-logo">
    <v-img
      v-if="branding.logoUrl"
      :src="branding.logoUrl"
      :alt="branding.appName"
      width="36"
      height="36"
      class="me-3 flex-grow-0"
    />
    <v-avatar
      v-else
      color="primary"
      size="36"
      class="me-3"
    >
      <v-icon color="white" icon="mdi-map-marker-radius" />
    </v-avatar>
    <div class="d-flex flex-column">
      <span class="text-subtitle-1 font-weight-bold app-logo-name">{{ branding.appName }}</span>
      <span class="text-caption text-medium-emphasis app-logo-tagline">{{ branding.tagline }}</span>
    </div>
  </div>
</template>

<script setup>
  import { useConfigStore } from '~/stores/config'

  const configStore = useConfigStore()
  const branding = configStore.branding
</script>

<style scoped>
.app-logo-name,
.app-logo-tagline {
  line-height: 1.1;
}
</style>
