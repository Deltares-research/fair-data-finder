import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchCollections as fetchCollectionsApi, fetchKeywords as fetchKeywordsApi } from '~/requests'
import { searchItems } from '~/requests/search'

export const useSearchPageStore = defineStore('searchPage', () => {
  //State
  const q = ref('')
  const startDate = ref(undefined)
  const endDate = ref(undefined)
  const keywords = ref([]) // Change from array of IDs to array of objects with {id, count, selected}
  const collections = ref([]) // Already has selected property
  const includeEmptyGeometry = ref(false)
  const bbox = ref([ 180, 90, -180, -90 ])
  const bboxFilter = ref([ 180, 90, -180, -90 ])
  
  const featureCollection = ref(null)
  const totalMatched = ref(0)
  const searchStatus = ref('idle')
  const searchError = ref(null)
  const selectedFeatureId = ref(null)
  const selectedFeatureBbox = ref(null)
  const areaDrawMode = ref(false)

  // Getter: Feature collection with only features that have valid geometry
  const featureCollectionWithGeometry = computed(() => {
    if (!featureCollection.value || !featureCollection.value.features) {
      return null
    }
    
    // Filter out features with null or missing geometry and those marked as global dataset
    const validFeatures = featureCollection.value.features
      .filter(feature => feature.geometry && feature.geometry.type)
      .filter(feature => !feature.properties?.globaldataset)
      .map(feature => {
        // Ensure properties.id is set to feature.id if it exists
        if (feature.id && !feature.properties?.id) {
          return {
            ...feature,
            properties: {
              ...feature.properties,
              id: feature.id,
            },
          }
        }
        return feature
      })
    
    if (validFeatures.length === 0) {
      return null
    }
    
    return {
      ...featureCollection.value,
      features: validFeatures,
    }
  })


  //Functions
  async function search(limit = 1000) {
    // Get selected collections (collections that are marked as selected)
    const selected = (collections.value || []).filter(c => c.selected)
    const selectedIds = selected.map(c => c.id)
    
    // Get selected keywords
    const selectedKeywords = (keywords.value || []).filter(k => k.selected)
    const selectedKeywordIds = selectedKeywords.map(k => k.id)
    
    searchStatus.value = 'pending'
    searchError.value = null
  
    try {
      const data = await searchItems({
        q: q.value,
        startDate: startDate.value,
        endDate: endDate.value,
        keywords: selectedKeywordIds, // Pass array of selected keyword IDs
        collections: selectedIds,
        includeEmptyGeometry: includeEmptyGeometry.value,
        bbox: bboxFilter.value,
        limit: limit,
      })

      // Mark features that have no geometry (null geometry = no spatial extent)
      if (data && data.features && Array.isArray(data.features)) {
        data.features = data.features.map(feature => {
          if (feature.geometry === null || feature.geometry === undefined) {
            return {
              ...feature,
              properties: {
                ...feature.properties,
                globaldataset: true,
              },
            }
          }
          return feature
        })
      }

      featureCollection.value = data
      totalMatched.value = data?.numMatched || 0
      searchStatus.value = 'success'
      
    } catch (e) {
      searchError.value = e?.message || e?.toString() || 'Unknown error'
      searchStatus.value = 'error'
      totalMatched.value = 0
    }
  }

  async function fetchCollections() {
    try {
      const data = await fetchCollectionsApi({ includeHeaders: false })
      collections.value = (data?.collections || []).map(c => ({ ...c, selected: false }))
    } catch (e) {
      console.error('Failed to fetch collections:', e?.message || e?.toString() || 'Unknown error')
      collections.value = []
    }
  }

  function setSelectedFeature(featureId) {
    selectedFeatureId.value = featureId
  }

  function setSelectedFeatureBbox(bbox) {
    selectedFeatureBbox.value = bbox
  }

  function clearSelectedFeature() {
    selectedFeatureId.value = null
    selectedFeatureBbox.value = null
  }

  async function fetchKeywords() {
    try {
      const data = await fetchKeywordsApi()
      // data is now an array of keywords, not an object with keywords property
      keywords.value = (Array.isArray(data) ? data : []).map(k => ({ ...k, selected: false }))
    } catch (e) {
      console.error('Failed to fetch keywords:', e?.message || e?.toString() || 'Unknown error')
      keywords.value = []
    }
  }

  return { q, startDate, endDate, keywords, collections, includeEmptyGeometry, bbox, bboxFilter, featureCollection, featureCollectionWithGeometry, totalMatched, searchStatus, searchError, selectedFeatureId, selectedFeatureBbox, areaDrawMode, search, fetchCollections, setSelectedFeature, setSelectedFeatureBbox, clearSelectedFeature, fetchKeywords }

})


