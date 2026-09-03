import { defineStore } from 'pinia'
import { useRuntimeConfig } from '#app'

export const useConfigStore = defineStore('config', () => {
  const config = useRuntimeConfig()

  const aboutTabEnabled = config.public.aboutTabEnabled ?? false
  const authEnabled = config.public.authEnabled ?? true
  const registerTabEnabled = config.public.registerTabEnabled ?? true
  const adminTabsEnabled = config.public.adminTabsEnabled ?? true

  return {
    aboutTabEnabled,
    authEnabled,
    registerTabEnabled,
    adminTabsEnabled,
  }
})

