import { defineStore } from 'pinia'
import { useRuntimeConfig } from '#app'

export const useConfigStore = defineStore('config', () => {
  const config = useRuntimeConfig()

  const aboutTabEnabled = config.public.aboutTabEnabled ?? false

  return {
    aboutTabEnabled,
  }
})

