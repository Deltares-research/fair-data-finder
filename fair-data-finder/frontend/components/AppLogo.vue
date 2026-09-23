<template>
  <div class="d-flex align-center app-logo">
    <v-img
      v-if="branding.logoUrl"
      :src="branding.logoUrl"
      :alt="branding.appName"
      height="40"
      width="160"
      class="flex-grow-0"
    />
    <v-avatar
      v-else
      color="primary"
      size="40"
    >
      <v-icon color="white" icon="mdi-map-marker-radius" />
    </v-avatar>
  </div>
</template>

<script setup>
  import { useConfigStore } from '~/stores/config'

  const configStore = useConfigStore()
  const branding = configStore.branding
</script>

