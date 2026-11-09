import { defineStore } from 'pinia'
import { ref } from 'vue'

export const usePermissionsStore = defineStore('permissions', () => {
  // State
  const permissions = ref([])
  const isLoading = ref(false)
  const error = ref(null)

  // Actions
  async function fetchPermissions($api) {
    isLoading.value = true
    error.value = null
    
    try {
      const permissionData = await $api('/permissions', {
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      })      
      
      if (!permissionData) {
        permissions.value = []
        return false
      }
      
      permissions.value = permissionData.value || permissionData || []
      
      return true
      
    } catch (err) {
      console.error('Failed to fetch permissions:', err?.message || err?.toString() || 'Unknown error')
      error.value = err?.message || 'Failed to fetch permissions'
      permissions.value = []
      return false
    } finally {
      isLoading.value = false
    }
  }

  // Permission checking functions
  function hasPermission(permission) {
    if (!permissions.value || !Array.isArray(permissions.value)) {
      return false
    }
    
    return permissions.value.includes(permission)
  }

  function requirePermission(permission) {
    if (!hasPermission(permission)) {
      // Show error message (you'll need to implement toast notification)
      console.warn(`Permission required: ${ permission }`)
      
      // Redirect to home page
      if (process.client) {
        window.location.href = '/'
      }
      return false
    }
    return true
  }

  // Collection-specific permissions
  async function fetchCollectionPermissions(collectionId, $api) {
    isLoading.value = true
    error.value = null
    
    try {
      const permissionData = await $api(`/collection-permissions/${ collectionId }`, {
        credentials: 'include',
      })
      
      if (!permissionData) {
        return []
      }
      
      return permissionData.value || permissionData || []
      
    } catch (err) {
      console.error('Failed to fetch collection permissions:', err?.message || err?.toString() || 'Unknown error')
      error.value = err?.message || 'Failed to fetch collection permissions'
      return []
    } finally {
      isLoading.value = false
    }
  }

  function hasCollectionPermission() {
    // This would need to be implemented based on your collection permissions structure
    // For now, returning false as a placeholder
    return false
  }

  // Item permissions: roles on a collection allow editing every item in it,
  // whole-app roles only allow editing the items the user created.
  const collectionPermissionsList = ref([])
  const ownedItems = ref([])

  async function fetchItemPermissions($api) {
    try {
      const [ collectionData, ownedData ] = await Promise.all([
        $api('/collection-permissions', { credentials: 'include' }),
        $api('/owned-items', { credentials: 'include' }),
        fetchPermissions($api),
      ])
      collectionPermissionsList.value = collectionData || []
      ownedItems.value = ownedData || []
      return true
    } catch (err) {
      console.error('Failed to fetch item permissions:', err?.message || err?.toString() || 'Unknown error')
      collectionPermissionsList.value = []
      ownedItems.value = []
      return false
    }
  }

  function hasPermissionOnCollection(collectionId, permission) {
    return collectionPermissionsList.value.some(entry =>
      entry.collection_id === collectionId &&
      entry.permissions?.includes(permission),
    )
  }

  function isOwnItem(collectionId, itemId) {
    return ownedItems.value.some(owned =>
      owned.collection_id === collectionId && owned.item_id === itemId,
    )
  }

  function canEditItem(collectionId, itemId) {
    return hasPermissionOnCollection(collectionId, 'item:update') ||
      (hasPermission('item:update') && isOwnItem(collectionId, itemId))
  }

  function canDeleteItem(collectionId) {
    return hasPermissionOnCollection(collectionId, 'item:delete')
  }

  function clearError() {
    error.value = null
  }

  // Permissions will be fetched explicitly when needed

  return {
    // State
    permissions,
    isLoading,
    error,
    
    // Actions
    fetchPermissions,
    hasPermission,
    requirePermission,
    fetchCollectionPermissions,
    hasCollectionPermission,
    fetchItemPermissions,
    canEditItem,
    canDeleteItem,
    clearError,
  }
})
