/**
 * Search API requests
 */
import { useNuxtApp } from '#app'
import searchBody from '@/utils/search/searchBody.js'

/**
 * Search for items
 * @param {Object} searchParams - Search parameters
 * @param {string} searchParams.q - Query string
 * @param {Date|string} searchParams.startDate - Start date
 * @param {Date|string} searchParams.endDate - End date
 * @param {Array} searchParams.keywords - Keywords array
 * @param {Array} searchParams.collections - Collection IDs array
 * @param {boolean} searchParams.includeEmptyGeometry - Include empty geometry
 * @param {Array} searchParams.bbox - Bounding box
 * @param {number} searchParams.limit - Result limit
 * @param {string} searchParams.token - Pagination token
 * @param {Array<Object>} searchParams.sortby - STAC sort extension fields,
 *   e.g. [{ field: 'properties.datetime', direction: 'desc' }]
 * @param {Function} [$api] - openFetch client captured synchronously by the
 *   caller. Pass this explicitly whenever the call happens after an `await`
 *   (e.g. inside useAsyncData handlers or store actions): Nuxt only restores
 *   the composable context automatically around awaits written directly in
 *   a <script setup> block, so calling useNuxtApp() here would silently
 *   throw once resumed from a prior await, be swallowed by the caller's
 *   try/catch, and result in no request ever being sent.
 *   See https://nuxt.com/docs/guide/concepts/auto-imports#vue-and-nuxt-composables
 * @returns {Promise<Object>} Search results
 */
export async function searchItems(searchParams = {}, $api = null) {
  const api = $api || useNuxtApp().$api

  try {
    const body = {
      ...searchBody({
        q: searchParams.q || '',
        startDate: searchParams.startDate,
        endDate: searchParams.endDate,
        keywords: searchParams.keywords || [],
        collections: searchParams.collections || [],
        includeEmptyGeometry: searchParams.includeEmptyGeometry || false,
        bbox: searchParams.bbox,
      }),
      limit: searchParams.limit || 1000,
    }

    if (searchParams.token) {
      body.token = searchParams.token
    }

    if (searchParams.sortby) {
      body.sortby = searchParams.sortby
    }

    // credentials/cookie forwarding for SSR is handled globally by the
    // openFetch plugin (plugins/openFetch.ts); it captures the request
    // cookie synchronously at plugin setup time, so it does not need to be
    // re-read here (which would be another composable call unsafe to make
    // after an await).
    const data = await api('/search', {
      method: 'POST',
      body,
      credentials: 'include',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    })
    
    return data
  } catch (error) {
    console.error('Search failed:', error?.message || error?.toString() || 'Unknown error')
    throw error
  }
}
