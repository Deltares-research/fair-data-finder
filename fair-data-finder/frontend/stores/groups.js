import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchGroups } from '~/requests/groups'

export const useGroupsStore = defineStore('groups', () => {
  // State
  const groups = ref([])
  const isLoading = ref(false)
  const error = ref(null)
  // True once the first fetch has completed, so subsequent visits to the
  // groups list can show cached data immediately and refresh silently
  // instead of blocking the whole table behind a spinner again.
  const hasLoaded = ref(false)

  // Computed
  const hasGroups = computed(() => groups.value.length > 0)

  // Actions
  // `silent` skips the isLoading toggle so a background refresh (e.g. when
  // revisiting the page with data already cached) doesn't blank the table.
  async function fetchGroupsList({ silent = false } = {}) {
    if (!silent) {
      isLoading.value = true
    }
    error.value = null

    try {
      const data = await fetchGroups()
      groups.value = data || []
      hasLoaded.value = true
      return true
    } catch (err) {
      console.error('Failed to fetch groups:', err?.message || err?.toString() || 'Unknown error')
      // Keep any already-cached groups visible on a silent background
      // refresh failure instead of wiping the table out from under the user.
      if (!silent) {
        error.value = err?.message || 'Failed to fetch groups'
        groups.value = []
      }
      return false
    } finally {
      if (!silent) {
        isLoading.value = false
      }
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    groups,
    isLoading,
    error,
    hasLoaded,
    
    // Computed
    hasGroups,
    
    // Actions
    fetchGroupsList,
    clearError,
  }
})

