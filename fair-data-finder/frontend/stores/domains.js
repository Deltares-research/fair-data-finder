import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchCollections } from '~/requests/collections'

export const useDomainsStore = defineStore('domains', () => {
  // State
  const collections = ref([])
  const isLoading = ref(false)
  const error = ref(null)
  // True once the first fetch has completed, so subsequent visits to the
  // domains list can show cached data immediately and refresh silently
  // instead of blocking the whole table behind a spinner again.
  const hasLoaded = ref(false)

  // Computed
  const hasCollections = computed(() => collections.value.length > 0)

  // Actions
  // `silent` skips the isLoading toggle so a background refresh (e.g. when
  // revisiting the page with data already cached) doesn't blank the table.
  async function fetchDomains({ silent = false } = {}) {
    if (!silent) {
      isLoading.value = true
    }
    error.value = null

    try {
      const data = await fetchCollections({ limit: 1000 })
      collections.value = data?.collections || []
      hasLoaded.value = true
      return true
    } catch (err) {
      console.error('Failed to fetch domains:', err?.message || err?.toString() || 'Unknown error')
      // Keep any already-cached collections visible on a silent background
      // refresh failure instead of wiping the table out from under the user.
      if (!silent) {
        error.value = err?.message || 'Failed to fetch domains'
        collections.value = []
      }
      return false
    } finally {
      if (!silent) {
        isLoading.value = false
      }
    }
  }

  // Optimistically reflect a create/update in the cached list so navigating
  // back to the domains page shows it instantly, without waiting on a fresh
  // fetch. A background refresh (see fetchDomains' silent mode) still
  // reconciles with the server shortly after.
  function upsertCollection(collection) {
    if (!collection?.id) return
    const index = collections.value.findIndex(existing => existing.id === collection.id)
    if (index >= 0) {
      collections.value[index] = collection
    } else {
      collections.value = [ collection, ...collections.value ]
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    collections,
    isLoading,
    error,
    hasLoaded,
    
    // Computed
    hasCollections,
    
    // Actions
    fetchDomains,
    upsertCollection,
    clearError,
  }
})

