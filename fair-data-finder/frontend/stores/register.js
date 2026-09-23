import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { searchItems } from '~/requests/search'

export const useRegisterStore = defineStore('register', () => {
  // State
  const items = ref([])
  const currentPage = ref(1)
  const itemsPerPage = ref(10)
  const nextToken = ref(null)
  const tokenHistory = ref([]) // Stack of tokens for back navigation
  const totalMatched = ref(0)
  const isLoading = ref(false)
  const error = ref(null)
  // True once the first fetch has completed, so subsequent visits to the
  // register list can show cached data immediately and refresh silently
  // instead of blocking the whole table behind a spinner again.
  const hasLoaded = ref(false)

  // Computed
  const hasNextPage = computed(() => nextToken.value !== null)

  const hasPreviousPage = computed(() => {
    return tokenHistory.value.length > 0 || currentPage.value > 1
  })

  // Actions
  // `silent` skips the isLoading toggle so a background refresh (e.g. when
  // revisiting the page with data already cached) doesn't blank the table.
  async function fetchItems(token = null, { silent = false } = {}) {
    if (!silent) {
      isLoading.value = true
    }
    error.value = null

    try {
      const data = await searchItems({
        limit: itemsPerPage.value,
        token,
      })

      // Handle response structure
      if (data && data.features) {
        items.value = data.features || []
        totalMatched.value = data?.numberMatched ?? data?.numberReturned ?? data?.features?.length ?? 0

        // Extract the next-page token. POST search responses (what this app
        // always uses) carry the token nested in `link.body.token`.
        const links = data.links || []
        const nextLink = links.find(link => link.rel === 'next')
        nextToken.value = nextLink?.body?.token ?? null

        // Update current page based on token history.
        if (token) {
          currentPage.value = tokenHistory.value.length + 1
        } else {
          tokenHistory.value = []
          currentPage.value = 1
        }
      } else {
        items.value = []
        totalMatched.value = 0
        nextToken.value = null
      }

      hasLoaded.value = true
      return true

    } catch (err) {
      console.error('Failed to fetch items:', err?.message || err?.toString() || 'Unknown error')
      // Keep any already-cached items visible on a silent background
      // refresh failure instead of wiping the table out from under the user.
      if (!silent) {
        error.value = err?.message || 'Failed to fetch items'
        items.value = []
        totalMatched.value = 0
      }
      return false
    } finally {
      if (!silent) {
        isLoading.value = false
      }
    }
  }

  // Optimistically reflect a create/update in the cached list so navigating
  // back to the register page shows it instantly, without waiting on a
  // fresh fetch. A background refresh (see fetchItems' silent mode) still
  // reconciles with the server shortly after.
  function upsertItem(item) {
    if (!item?.id) return
    const index = items.value.findIndex(existing => existing.id === item.id)
    if (index >= 0) {
      items.value[index] = item
    } else if (currentPage.value === 1) {
      items.value = [ item, ...items.value ]
      totalMatched.value += 1
    }
  }

  async function nextPage() {
    if (!hasNextPage.value || !nextToken.value) return false

    tokenHistory.value.push(nextToken.value)
    return await fetchItems(nextToken.value)
  }

  async function previousPage() {
    if (!hasPreviousPage.value) return false

    if (tokenHistory.value.length > 0) {
      tokenHistory.value.pop()
      const prevTokenToUse = tokenHistory.value.length > 0
        ? tokenHistory.value[tokenHistory.value.length - 1]
        : null
      return await fetchItems(prevTokenToUse)
    }

    if (currentPage.value > 1) {
      tokenHistory.value = []
      return await fetchItems(null)
    }

    return false
  }

  function setItemsPerPage(value) {
    itemsPerPage.value = value
    // Reset to first page when changing items per page
    tokenHistory.value = []
    currentPage.value = 1
    fetchItems(null)
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    items,
    currentPage,
    itemsPerPage,
    nextToken,
    totalMatched,
    isLoading,
    error,
    hasLoaded,
    
    // Computed
    hasNextPage,
    hasPreviousPage,
    
    // Actions
    fetchItems,
    upsertItem,
    nextPage,
    previousPage,
    setItemsPerPage,
    clearError,
  }
})
