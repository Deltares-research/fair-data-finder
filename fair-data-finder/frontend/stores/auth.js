import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useNuxtApp } from '#app'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(null)
  const isAuthenticated = ref(false)
  const isLoading = ref(false)
  const error = ref(null)

  // Getters
  const displayName = computed(() => user.value?.display_name || '')
  const userEmail = computed(() => user.value?.email || '')
  const isLoggedIn = computed(() => isAuthenticated.value && user.value !== null)

  // Actions
  async function checkAuth($api = null) {
    isLoading.value = true
    error.value = null
    
    try {
      // Get $api from parameter or useNuxtApp (fallback for client-side calls)
      const api = $api || useNuxtApp().$api
      
      const userData = await api('/auth/me', {
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      })
      
      if (!userData) {
        // User is not authenticated
        user.value = null
        isAuthenticated.value = false
        return false
      }
      
      // User is authenticated
      user.value = userData
      isAuthenticated.value = true
      return true
      
    } catch (err) {
      // 401 Unauthorized is normal for unauthenticated users - don't log as error
      if (err?.status !== 401) {
        console.error('Auth check failed:', err?.message || err?.toString() || 'Unknown error')
        error.value = err?.message || 'Authentication failed'
      } else {
        // Clear any previous errors for normal unauthenticated state
        error.value = null
      }
      user.value = null
      isAuthenticated.value = false
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function login() {
    // Redirect to Microsoft SSO login
    window.location.href = '/api/auth/login'
  }

  async function logout() {
    isLoading.value = true
    error.value = null

    user.value = null
    isAuthenticated.value = false

    // The cookie is HttpOnly, so only the backend can clear it. That endpoint
    // expires the cookie and redirects to FRONTEND_URL; the resulting full page
    // load rebuilds client state from scratch.
    if (process.client) {
      window.location.href = '/api/auth/logout'
    }
  }

  function clearError() {
    error.value = null
  }

  // Auth check will be called explicitly when needed

  return {
    // State
    user,
    isAuthenticated,
    isLoading,
    error,
    
    // Getters
    displayName,
    userEmail,
    isLoggedIn,
    
    // Actions
    checkAuth,
    login,
    logout,
    clearError,
  }
})
