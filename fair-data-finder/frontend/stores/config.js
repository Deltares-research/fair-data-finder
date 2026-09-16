import { defineStore } from 'pinia'
import { useRuntimeConfig } from '#app'

export const useConfigStore = defineStore('config', () => {
  const config = useRuntimeConfig()

  const aboutTabEnabled = config.public.aboutTabEnabled ?? false
  const branding = config.public.branding ?? {}
  const theme = config.public.theme ?? {}

  return {
    aboutTabEnabled,
    branding,
    theme,
  }
})

