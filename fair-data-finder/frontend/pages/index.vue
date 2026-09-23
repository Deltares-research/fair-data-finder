<template>
  <v-container fluid class="ma-0 three-col-page">
    <v-row no-gutters class="three-col-row">
      <!-- LEFT: Filters sidebar (its own scroll) -->
      <v-col
        v-if="canAccess"
        :cols="12"
        :md="3"
        class="filters-col"
      >
        <v-sheet class="filters-scroll pa-4">
          <div class="mb-4">
            <h1 class="text-h5 font-weight-bold mb-1">
              {{ configStore.branding.appName }}
            </h1>
            <p class="text-body-2 text-grey mb-0">
              {{ configStore.branding.tagline }}
            </p>
          </div>

          <feature-filters :options="filterOptions" />

          <v-card
            class="mt-4 dataset-count-card"
            variant="flat"
          >
            <v-card-text class="text-center">
              <v-icon
                size="32"
                color="primary"
                class="mb-2"
              >
                mdi-database
              </v-icon>
              <div class="text-body-1 font-weight-medium">
                {{ store.totalMatched }} datasets available
              </div>
            </v-card-text>
          </v-card>
        </v-sheet>
      </v-col>

      <!-- RIGHT: Search header (spanning results + map) with results list and map below -->
      <v-col
        :cols="12"
        :md="canAccess ? 9 : 12"
        class="content-col"
      >
        <!-- Not authenticated state -->
        <div
          v-if="!canAccess && !authLoading"
          class="d-flex flex-column justify-center align-center text-center pa-4"
          style="height: 200px;"
        >
          <v-icon
            size="64"
            color="grey-lighten-1"
            class="mb-4"
          >
            mdi-account-circle
          </v-icon>
          <h3 class="text-h6 mb-2">
            Please log in to search data
          </h3>
          <p class="text-body-2 text-grey">
            Use the login button in the top right to access the FAIR data finder
          </p>
        </div>

        <!-- Authenticated state with features -->
        <template v-else-if="canAccess">
          <!-- Header: branding, search bar and dataset count sit above both the
               results list and the map, without covering either -->
          <div class="content-header pa-4 pb-2">
            <!-- Search input -->
            <v-row class="mb-2">
              <v-col cols="12">
                <form @submit.prevent="applyQuery">
                  <div class="d-flex align-center ga-2">
                    <v-text-field
                      v-model="queryInput"
                      variant="outlined"
                      placeholder="Search title or description"
                      hide-details
                      clearable
                      class="flex-grow-1"
                      @click:clear="queryInput = ''; applyQuery()"
                    />
                    <v-btn type="submit" color="primary" variant="flat">
                      Search
                    </v-btn>
                  </div>
                </form>
              </v-col>
            </v-row>

            <div class="d-flex align-center">
              <h2 class="text-h6 font-weight-bold">
                {{ store.totalMatched }} datasets found
              </h2>
            </div>
          </div>

          <!-- Results list (its own scroll) and map (fixed), side by side below the header -->
          <v-row no-gutters class="content-body">
            <v-col
              :cols="12"
              :md="7"
              class="results-col"
            >
              <v-sheet class="results-scroll pa-4 pt-0">
                <v-row>
                  <v-col
                    v-for="f in features"
                    :key="f.id"
                    cols="12"
                  >
                    <v-card 
                      class="mb-4 result-card" 
                      variant="outlined"
                      :class="{ 'selected-feature': f.id === store.selectedFeatureId }"
                    >
                      <v-card-title class="d-flex align-start ga-3 flex-nowrap py-3">
                        <!-- Left: dataset thumbnail. Only rendered when the
                             item actually has its own thumbnail/photo/
                             snapshot image asset. -->
                        <v-avatar
                          v-if="thumbnailAsset(f)"
                          rounded="lg"
                          size="48"
                          class="flex-shrink-0"
                        >
                          <v-img
                            :src="thumbnailAsset(f).href"
                            :alt="f.properties?.title || 'Dataset thumbnail'"
                            cover
                          />
                        </v-avatar>

                        <div class="flex-grow-1 d-flex align-center flex-wrap ga-2 text-wrap">
                          <span class="flex-grow-1">{{ f.properties?.title || 'Untitled' }}</span>
                          <v-chip
                            v-if="f.properties?.globaldataset"
                            color="primary"
                            size="small"
                          >
                            Global Dataset
                          </v-chip>
                          <!-- Right: domain label, matching the mockup's domain badge -->
                          <v-chip
                            size="small"
                            variant="flat"
                            :color="domainInfo(f).color"
                          >
                            {{ domainInfo(f).title }}
                          </v-chip>
                        </div>
                      </v-card-title>

                      <v-card-text>
                        <p class="mb-3 line-clamp-3">
                          {{ f.properties?.description || 'No description.' }}
                        </p>

                        <div class="d-flex align-center mb-3">
                          <v-icon class="mr-2" size="small">
                            mdi-link-variant
                          </v-icon>
                          <span v-if="firstAssetHref(f)">
                            {{ firstAssetHref(f) }}
                          </span>
                          <span v-else>—</span>
                        </div>

                        <!-- Add this new paragraph for view details -->
                        <div class="mb-3">
                          <NuxtLink
                            :to="`/register/${f.id}/view`"
                            class="text-body-2 text-primary"
                            style="text-decoration: none; cursor: pointer;"
                          >
                            View details
                          </NuxtLink>
                        </div>

                        <div class="text-body-2">
                          {{ formatDate(f) }}
                        </div>
                      </v-card-text>

                      <v-card-actions
                        v-if="f.bbox && !f.properties?.globaldataset"
                        class="justify-end pt-0"
                      >
                        <v-btn
                          variant="text"
                          color="primary"
                          size="small"
                          prepend-icon="mdi-image-filter-center-focus"
                          @click="zoomToFeature(f)"
                        >
                          Zoom to data
                        </v-btn>
                      </v-card-actions>
                    </v-card>
                  </v-col>
                </v-row>
              </v-sheet>
            </v-col>

            <!-- Map (fixed to visible viewport below the header) -->
            <v-col
              :cols="12"
              :md="5"
              class="map-col"
            >
              <v-sheet class="map-panel">
                <!-- Mapbox GL needs a real DOM and cannot be server-rendered. The
                     fallback reserves the same box so hydration causes no shift. -->
                <ClientOnly>
                  <search-map-component />
                  <template #fallback>
                    <div class="map-placeholder" />
                  </template>
                </ClientOnly>
              </v-sheet>
            </v-col>
          </v-row>
        </template>
      </v-col>
    </v-row>
  </v-container>
</template>

  <script setup>
  // Named so <NuxtPage :keepalive="{ include: ['index'] }"> in app.vue can
  // match this page and keep it (and its Mapbox map) alive across navigation
  // instead of destroying/recreating it on every visit.
  defineOptions({ name: 'index' })

  import { computed, watch, ref } from 'vue'
  import { useSearchPageStore } from '~/stores/searchPage'
  import { useConfigStore } from '~/stores/config'
  import { useRoute } from 'vue-router'
  import { useAsyncData, useNuxtApp } from '#app'
  import { useAuth } from '~/composables/useAuth'
  import FeatureFilters from '@/components/FeatureFilters.vue'
  import { formatDate } from '~/utils/helpers'

  const { isAuthenticated, isLoading: authLoading } = useAuth()
  const configStore = useConfigStore()

  // Captured synchronously (before any await) so it can be threaded through
  // to store.search() inside the useAsyncData handler below. Composables
  // like useNuxtApp() are only guaranteed to work when called before an
  // await; calling them again after the Promise.all(...) await further down
  // silently throws during SSR and is swallowed by store.search()'s
  // try/catch, which is why the very first authenticated page load never
  // issued a /api/search request.
  const { $api } = useNuxtApp()

  const canAccess = computed(() => isAuthenticated.value)

  const store = useSearchPageStore()
  const route = useRoute()
  
  const q = route.query
  
  store.q = q.q || ''
  store.startDate = q.start || undefined
  store.endDate = q.end || undefined
  store.keywords = toArr(q.keywords)
  // If URL has includeEmptyGeometry parameter, use it; otherwise keep default (false)
  if (q.includeEmptyGeometry !== undefined) {
    store.includeEmptyGeometry = q.includeEmptyGeometry === 'on'
  }

  // Fetched once on the server and transferred via the Nuxt payload, so
  // hydration does not repeat these requests. Collections and keywords are
  // independent, so they run in parallel; the search depends on the selection
  // state derived from them and therefore runs afterwards.
  await useAsyncData('index-initial-data', async () => {
    await Promise.all([store.fetchCollections(), store.fetchKeywords()])

    const ids = toArr(q.collections)
    if (ids.length > 0) {
      store.collections = store.collections.map(c => ({
        ...c,
        selected: ids.includes(c.id)
      }))
    }

    const keywordIds = toArr(q.keywords)
    if (keywordIds.length > 0) {
      store.keywords = store.keywords.map(k => ({
        ...k,
        selected: keywordIds.includes(k.id)
      }))
    }

    if (canAccess.value) {
      await store.search(500, $api)
    }

    return true
  })

  const queryInput = ref(store.q || '')
  function applyQuery() {
    store.q = (queryInput.value || '').trim()
  }

  watch(
    () => [store.q, store.startDate, store.endDate, store.keywords, store.collections, store.includeEmptyGeometry, store.bboxFilter, canAccess.value],
    () => {
      if (canAccess.value) {
        store.search(1000)
      }
    },
    { deep: true }
  )

  const features = computed(() => {
    if (!canAccess.value) {
      return []
    }
    const collection = store.featureCollection
    return Array.isArray(collection?.features) ? collection.features : []
  })

  // Helper functions
  function toArr(val) {
    if (!val) return []
    return Array.isArray(val) ? val : [val]
  }

  function norm(str) {
    return (str || '').toString().trim().toLowerCase()
  }

  function sortAsc(a, b) {
    return norm(a).localeCompare(norm(b))
  }

  function firstAssetHref(feature) {
    const assets = feature?.assets
    if (!assets) return null
    const firstKey = Object.keys(assets)[0]
    return firstKey ? assets[firstKey]?.href : null
  }

  // Selects the feature and (re-)pushes its bbox to the store so the map
  // zooms/pans to it, even if this same feature was already selected.
  function zoomToFeature(feature) {
    store.setSelectedFeature(feature.id)
    if (feature.bbox) {
      store.setSelectedFeatureBbox([...feature.bbox])
    }
  }

  // Finds a dataset thumbnail/photo/snapshot among the item's own assets, so
  // the card can display the real image instead of a generic placeholder
  // whenever the dataset actually provides one.
  function thumbnailAsset(feature) {
    const assets = feature?.assets
    if (!assets) return null

    const isImageAsset = ([key, asset]) => {
      const type = (asset?.type || '').toLowerCase()
      const roles = asset?.roles || []
      const nameHints = `${key} ${asset?.title || ''}`.toLowerCase()
      return (
        type.startsWith('image/') ||
        roles.includes('thumbnail') ||
        /thumbnail|photo|snapshot|snap/.test(nameHints)
      )
    }

    const found = Object.entries(assets).find(isImageAsset)
    return found ? found[1] : null
  }

  // Single Deltares-style light blue used for the domain badge.
  const DOMAIN_COLOR = '#4C6FDC'

  // Reads the dataset's domain from its own collection reference (not
  // guessed); the color is fixed rather than derived per domain.
  function domainInfo(feature) {
    const collectionId = feature?.collection
    const match = store.collections.find(c => c.id === collectionId)
    const title = match?.title || collectionId || 'Unknown domain'
    return { title, color: DOMAIN_COLOR }
  }

  // Filter options
  const filterOptions = computed(() => {
    const col = new Set()
    const kw = new Set()

    features.value.forEach(f => {
      if (f.collection) col.add(f.collection)
      const keywords = f.properties?.keywords || []
      keywords.forEach(k => {
        if (k?.en_keyword) kw.add(k.en_keyword)
      })
    })

    return {
      collection: [...col].sort(sortAsc),
      keyword: [...kw].sort(sortAsc),
    }
  })

/*   function navigateToView(itemId) {
    navigateTo(`/register/${itemId}/view`).catch(() => {
      // Handle navigation errors silently
    })
  } */
</script>

<style scoped>
/* Three-column layout with scrolling: filters | results | map.
   A gap below the app bar (and around the edges) mirrors the breathing
   room around the header card in the mockup. */
.three-col-page {
  height: calc(100vh - 64px);
  padding: 20px;
  background-color: #F6F9FC;
}

.three-col-row {
  height: 100%;
}

.filters-col {
  height: 100%;
  overflow: hidden;
  border-right: 1px solid rgba(0, 0, 0, 0.08);
}

.filters-scroll {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
}

.content-col {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Search bar + dataset count: fixed above the results list and the map,
   spanning both without covering either. */
.content-header {
  flex: 0 0 auto;
}

.content-body {
  flex: 1 1 auto;
  min-height: 0;
}

.results-col {
  height: 100%;
  overflow: hidden;
}

.results-scroll {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  background-color: #F6F9FC;
}

.map-col {
  height: 100%;
}

.map-panel {
  height: 100%;
}

.dataset-count-card {
  background-color: rgba(var(--v-theme-primary), 0.06);
}

/* Reserves the map box during SSR so hydration causes no layout shift. */
.map-placeholder {
  height: 100%;
  width: 100%;
}

/* Clamp long descriptions to 3 lines */
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Flat dataset cards, matching the mockup (no drop shadow, subtle border only) */
.result-card {
  box-shadow: none !important;
  border-color: rgba(0, 0, 0, 0.08);
}

/* Selected feature highlighting */
.selected-feature {
  border: 2px solid rgb(var(--v-theme-primary));
  background-color: rgba(var(--v-theme-primary), 0.05);
}
</style>

