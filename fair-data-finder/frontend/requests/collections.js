/**
 * Collections API requests
 * Centralized functions for all collection-related API calls
 */
import { useNuxtApp } from '#app'

/**
 * Fetch all collections
 * @param {Object} options - Optional parameters
 * @param {number} options.limit - Limit number of results
 * @returns {Promise<Object>} Collections data
 */
export async function fetchCollections(options = {}) {
  const { limit } = options
  const { $api } = useNuxtApp()
  
  try {
    const data = await $api('/collections', {
      query: limit ? { limit } : {},
      credentials: 'include',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    })
    
    return data
  } catch (error) {
    console.error('Failed to fetch collections:', error?.message || error?.toString() || 'Unknown error')
    throw error
  }
}

/**
 * Fetch a single collection by ID
 * @param {string} collectionId - Collection ID
 * @returns {Promise<Object>} Collection data
 */
export async function fetchCollectionById(collectionId) {
  const { $api } = useNuxtApp()
  
  try {
    const collection = await $api('/collections/{collection_id}', {
      path: {
        collection_id: collectionId,
      },
      credentials: 'include',
    })
    
    return collection
  } catch (error) {
    console.error('Failed to fetch collection:', error?.message || error?.toString() || 'Unknown error')
    throw error
  }
}

/**
 * Fetch collection permissions
 * @returns {Promise<Array>} Collection permissions array
 */
export async function fetchCollectionPermissions() {
  const { $api } = useNuxtApp()
  
  try {
    const permissions = await $api('/collection-permissions', {
      credentials: 'include',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    })
    
    return permissions || []
  } catch (error) {
    console.error('Failed to fetch collection permissions:', error?.message || error?.toString() || 'Unknown error')
    throw error
  }
}

/**
 * Fetch collections with permissions filtered by item:create permission
 * @param {Object} options - Optional parameters
 * @returns {Promise<Object>} Object with filtered collections and permissions
 */
export async function fetchCollectionsWithCreatePermission(options = {}) {
  try {
    const [ collectionsData, permissionsData ] = await Promise.all([
      fetchCollections(options),
      fetchCollectionPermissions(),
    ])

    const allCollections = collectionsData?.collections || []
    const permissions = permissionsData || []

    // Filter collections by item:create permission
    const filteredCollections = allCollections.filter(collection => {
      return permissions.some(permission =>
        permission.collection_id === collection.id &&
        permission.permissions?.includes('item:create'),
      )
    })

    return {
      collections: filteredCollections,
      permissions,
    }
  } catch (error) {
    console.error('Failed to fetch collections with permissions:', error)
    throw error
  }
}

/**
 * Create a new collection
 * @param {Object} collectionData - Collection data to create
 * @returns {Promise<Object>} Created collection
 */
export async function createCollection(collectionData) {
  const { $api } = useNuxtApp()
  
  try {
    const result = await $api('/collections', {
      method: 'POST',
      body: collectionData,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    return result
  } catch (error) {
    console.error('Failed to create collection:', error?.message || error?.toString() || 'Unknown error')
    throw error
  }
}

/**
 * Update an existing collection
 * @param {string} collectionId - Collection ID
 * @param {Object} collectionData - Updated collection data
 * @returns {Promise<Object>} Updated collection
 */
export async function updateCollection(collectionId, collectionData) {
  const { $api } = useNuxtApp()
  
  try {
    const result = await $api('/collections/{collection_id}', {
      method: 'PUT',
      body: collectionData,
      path: {
        collection_id: collectionId,
      },
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    return result
  } catch (error) {
    console.error('Failed to update collection:', error?.message || error?.toString() || 'Unknown error')
    throw error
  }
}

/**
 * Delete a collection
 * @param {string} collectionId - Collection ID
 * @returns {Promise<void>}
 */
export async function deleteCollection(collectionId) {
  const { $api } = useNuxtApp()
  
  try {
    await $api('/collections/{collection_id}', {
      method: 'DELETE',
      path: {
        collection_id: collectionId,
      },
      credentials: 'include',
    })
  } catch (error) {
    console.error('Failed to delete collection:', error?.message || error?.toString() || 'Unknown error')
    throw error
  }
}

/**
 * Fetch facilities (for keywords dropdown)
 * @returns {Promise<Array>} Facilities array
 */
export async function fetchFacilities() {
  const { $api } = useNuxtApp()
  
  try {
    const facilities = await $api('/facilities', {
      credentials: 'include',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    })
    
    return facilities || []
  } catch (error) {
    console.error('Failed to fetch facilities:', error?.message || error?.toString() || 'Unknown error')
    throw error
  }
}

