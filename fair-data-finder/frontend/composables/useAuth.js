import { useAuthStore } from '~/stores/auth'
import { usePermissionsStore } from '~/stores/permissions'
import { useConfigStore } from '~/stores/config'
import { computed } from 'vue'

export function useAuth() {
  const authStore = useAuthStore()
  const permissionsStore = usePermissionsStore()
  const configStore = useConfigStore()

  const authEnabled = computed(() => configStore.authEnabled)

  // Combined authentication and permission checking
  const isAuthenticated = computed(() => authStore.isLoggedIn)
  const user = computed(() => authStore.user)
  const displayName = computed(() => authStore.displayName)
  const isLoading = computed(() => authStore.isLoading || permissionsStore.isLoading)

  function hasPermission(permission) {
    if (!isAuthenticated.value) {
      return false
    }
    return permissionsStore.hasPermission(permission)
  }

  function requirePermission(permission) {
    if (!isAuthenticated.value) {
      authStore.login()
      return false
    }
    return permissionsStore.requirePermission(permission)
  }

  // Authentication actions
  async function login() {
    return await authStore.login()
  }

  async function logout() {
    return await authStore.logout()
  }

  async function checkAuth($api = null) {
    if (!authEnabled.value) {
      return false
    }
    const authResult = await authStore.checkAuth($api)
    if (authResult) {
      // Refresh permissions when user is authenticated
      await permissionsStore.fetchPermissions($api)
    }
    return authResult
  }

  return {
    authEnabled,
    isAuthenticated,
    user,
    displayName,
    isLoading,
    hasPermission,
    requirePermission,
    login,
    logout,
    checkAuth,
  }
}
