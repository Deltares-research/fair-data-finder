<template>
  <v-container class="pa-6">
    <v-row justify="center">
      <v-col
        cols="12"
        md="10"
        lg="8"
        xl="6"
      >
        <!-- Loading state -->
        <v-card v-if="isLoading" class="mb-4">
          <v-card-text class="d-flex flex-column align-center justify-center py-12">
            <v-progress-circular
              indeterminate
              color="primary"
              size="64"
              class="mb-4"
            />
            <p class="text-body-2 text-grey-darken-1">
              Loading item...
            </p>
          </v-card-text>
        </v-card>

        <!-- Error state -->
        <v-card v-else-if="error" class="mb-4">
          <v-card-text class="d-flex flex-column align-center justify-center py-12 text-center">
            <v-icon
              size="64"
              color="error"
              class="mb-4"
            >
              mdi-alert-circle
            </v-icon>
            <h3 class="text-h6 mb-2">
              Error loading item
            </h3>
            <p class="text-body-2 text-grey-darken-1 mb-4">
              {{ error }}
            </p>
            <v-btn variant="outlined" to="/">
              Return to search
            </v-btn>
          </v-card-text>
        </v-card>

      
        <div v-else-if="item">
          <h1 class="text-h4 font-weight-bold mb-4">
            {{ item.properties?.title || 'Untitled Item' }}
          </h1>

          <div class="d-flex align-center text-body-2 text-grey-darken-1 mb-6">
            <v-icon size="small" class="mr-1">
              mdi-calendar
            </v-icon>
            <span>{{ formatDate(item) }}</span>
          </div>

          <!-- Same sections, order and labels as the register form -->
          <template v-for="group in itemFieldGroups" :key="group.id">
            <v-card v-if="group.type === 'geometry'" class="mb-4">
              <v-card-title class="text-h6">
                {{ group.title }}
              </v-card-title>
              <v-card-text v-if="item.geometry" style="min-height: 300px;">
                <div class="map-wrapper">
                  <ClientOnly>
                    <item-map-component
                      :draw-mode="false"
                      :center="mapCenter"
                      :layer-options="layerOptions"
                      :zoom-bounds="bounds"
                    />
                    <template #fallback>
                      <div style="height: 300px;" />
                    </template>
                  </ClientOnly>
                </div>
              </v-card-text>
              <v-card-text v-else class="text-body-2 text-grey-darken-1">
                —
              </v-card-text>
            </v-card>

            <v-card v-else-if="group.type === 'assets'" class="mb-4">
              <v-card-title class="text-h6">
                {{ group.title }}
              </v-card-title>
              <v-card-text>
                <div v-if="assets.length === 0" class="text-body-2 text-grey-darken-1">
                  —
                </div>
                <v-table
                  v-for="asset in assets"
                  :key="asset.key"
                  density="compact"
                  class="mb-4 border rounded"
                >
                  <tbody>
                    <tr v-for="field in group.fields" :key="field.key">
                      <td class="text-subtitle-2 font-weight-medium label-cell">
                        {{ field.label }}
                      </td>
                      <td style="word-break: break-all;">
                        <template v-if="field.key === 'href' && asset.href">
                          <a
                            v-if="isUrl(asset.href)"
                            :href="asset.href"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="text-primary"
                          >
                            {{ asset.href }}
                            <v-icon size="small" class="ml-1">mdi-open-in-new</v-icon>
                          </a>
                          <span v-else>
                            {{ asset.href }}
                            <v-btn
                              variant="text"
                              size="small"
                              prepend-icon="mdi-content-copy"
                              @click="copyToClipboard(asset.href, asset.key)"
                            >
                              {{ copiedAssets[asset.key] ? 'Copied!' : 'Copy' }}
                            </v-btn>
                          </span>
                        </template>
                        <span v-else>{{ asset[field.key] || '—' }}</span>
                      </td>
                    </tr>
                  </tbody>
                </v-table>
              </v-card-text>
            </v-card>

            <v-card v-else class="mb-4">
              <v-card-title class="text-h6">
                {{ group.title }}
              </v-card-title>
              <v-card-text>
                <v-table density="compact">
                  <tbody>
                    <tr v-for="field in group.fields" :key="field.key">
                      <td class="text-subtitle-2 font-weight-medium label-cell">
                        {{ field.label }}
                      </td>
                      <td>
                        <div
                          v-if="field.type === 'keywords'"
                          class="d-flex flex-wrap py-2"
                          style="gap: 8px;"
                        >
                          <v-chip
                            v-for="keyword in keywords"
                            :key="keyword.id"
                            size="small"
                            variant="tonal"
                          >
                            {{ keyword.nl_keyword || keyword.en_keyword }}
                          </v-chip>
                          <span v-if="keywords.length === 0">—</span>
                        </div>
                        <span v-else style="white-space: pre-line;">{{ displayValue(field) }}</span>
                      </td>
                    </tr>
                  </tbody>
                </v-table>
              </v-card-text>
            </v-card>
          </template>

          <!-- Everything the search returns that the register form does not cover -->
          <v-card v-if="otherInformation.length > 0" class="mb-4">
            <v-card-title class="text-h6">
              Other information
            </v-card-title>
            <v-card-text>
              <v-table density="compact">
                <tbody>
                  <tr v-for="entry in otherInformation" :key="entry.key">
                    <td class="text-subtitle-2 font-weight-medium label-cell">
                      {{ entry.label }}
                    </td>
                    <td style="word-break: break-all;">
                      <div v-if="entry.key === 'links'">
                        <div v-for="link in entry.value" :key="`${link.rel}-${link.href}`">
                          <a
                            :href="link.href"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="text-primary"
                          >
                            {{ link.rel }}: {{ link.href }}
                          </a>
                        </div>
                      </div>
                      <a
                        v-else-if="isUrl(entry.value)"
                        :href="entry.value"
                        target="_blank"
                        rel="noopener noreferrer"
                        class="text-primary"
                      >
                        {{ entry.value }}
                      </a>
                      <span v-else style="white-space: pre-wrap;">{{ formatOtherValue(entry.key, entry.value) }}</span>
                    </td>
                  </tr>
                </tbody>
              </v-table>
            </v-card-text>
          </v-card>

          <!-- Back button -->
          <div class="mt-4">
            <v-btn variant="outlined" to="/">
              Back to search
            </v-btn>
          </div>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
  import { ref, computed, onMounted } from 'vue'
  import { useRoute } from 'vue-router'
  import { center } from '@turf/turf'
  import dateFormat from 'dateformat'
  import itemFieldGroups from '~/configuration/itemFieldGroups.json'
  import languageOptions from '~/configuration/languageOptions.json'
  import legalRestrictionsOptions from '~/configuration/legalRestrictionsOptions.json'
  import spatialReferenceSystemOptions from '~/configuration/spatialReferenceSystemOptions.json'
  import facilityTypeOptions from '~/configuration/facilityTypeOptions.json'
  import { fetchItemById } from '~/requests/items'
  import { formatDate, humanizeKey } from '~/utils/helpers'
  import buildGeoJsonLayer from '~/utils/build-geojson-layer'

  const route = useRoute()
  const itemId = route.params['id']
 
  const item = ref(null)
  const isLoading = ref(true)
  const error = ref(null)
  

  const copiedAssets = ref({})

  const optionLists = {
    languageOptions,
    legalRestrictionsOptions,
    spatialReferenceSystemOptions,
    facilityTypeOptions,
  }

  // Top-level item fields shown in their own sections (Domain, Geometry,
  // Storage location data set); every other top-level field goes to Other information.
  const SECTION_TOP_LEVEL_KEYS = [ 'id', 'properties', 'collection', 'geometry', 'assets' ]

  // Properties covered by the configured sections, including fallback keys
  const groupedPropertyKeys = new Set(
    itemFieldGroups
      .filter(group => !group.type)
      .flatMap(group => group.fields.flatMap(field => [ field.key, field.fallbackKey ]))
      .filter(Boolean),
  )

  // Computed properties
  const assets = computed(() => {
    if (!item.value?.assets) return []
    return Object.entries(item.value.assets).map(([key, asset]) => ({
      key,
      title: asset.title || key,
      href: asset.href || '',
      type: asset.type || '',
      description: asset.description || '',
    }))
  })

  const keywords = computed(() => {
    const value = item.value?.properties?.keywords
    return Array.isArray(value) ? value : []
  })

  const otherInformation = computed(() => {
    if (!item.value) return []
    const properties = item.value.properties || {}
    const entries = [
      [ 'id', item.value.id ],
      ...Object.entries(properties).filter(([ key ]) => !groupedPropertyKeys.has(key)),
      ...Object.entries(item.value).filter(([ key ]) => !SECTION_TOP_LEVEL_KEYS.includes(key)),
    ]
    return entries
      .filter(([ , value ]) => !isEmpty(value))
      .map(([ key, value ]) => ({ key, value, label: humanizeKey(key) }))
  })

  // Methods
  function isEmpty(value) {
    return value === null || value === undefined || value === '' ||
      (Array.isArray(value) && value.length === 0)
  }

  function fieldValue(field) {
    if (field.key === 'collection') return item.value?.collection
    const properties = item.value?.properties || {}
    return properties[field.key] ?? (field.fallbackKey ? properties[field.fallbackKey] : undefined)
  }

  // Same day format as the register form (dd-mm-yyyy, UTC date part)
  function formatDay(value) {
    const date = new Date(value)
    return isNaN(date.getTime()) ? String(value) : dateFormat(date, 'dd-mm-yyyy', true)
  }

  function displayValue(field) {
    const value = fieldValue(field)
    if (isEmpty(value)) return '—'
    if (field.type === 'date') return formatDay(value)
    if (field.options) {
      return optionLists[field.options]?.find(option => option.value === value)?.title || String(value)
    }
    return String(value)
  }

  function formatOtherValue(key, value) {
    if (Array.isArray(value) && value.every(entry => typeof entry !== 'object')) {
      return value.join(', ')
    }
    if (typeof value === 'object') return JSON.stringify(value, null, 2)
    if (typeof value === 'string' && /date|time|created|updated/i.test(key)) {
      const date = new Date(value)
      if (!isNaN(date.getTime())) return dateFormat(date, 'dd-mm-yyyy HH:MM:ss')
    }
    return String(value)
  }

  function isUrl(value) {
    if (typeof value !== 'string') return false
    try {
      const url = new URL(value)
      return url.protocol === 'http:' || url.protocol === 'https:'
    } catch {
      return false
    }
  }

  async function copyToClipboard(text, assetKey) {
    try {
      await navigator.clipboard.writeText(text)
      copiedAssets.value[assetKey] = true
      setTimeout(() => {
        copiedAssets.value[assetKey] = false
      }, 2000)
    } catch (err) {
      console.error('Failed to copy text:', err)
    }
  }
  const bounds = computed(() => {
    if (!item.value || !item.value.geometry || !item.value.bbox) return []
    return Array.isArray(item.value.bbox) ? item.value.bbox : []
  })

  // Build layer options from the item
  const layerOptions = computed(() => {
    if (!item.value || !item.value.geometry) return null
    
    // Convert single item to featureCollection format
    const featureCollection = {
      type: 'FeatureCollection',
      features: [item.value],
    }
    return buildGeoJsonLayer(featureCollection)
  })



  // Fetch item on mount
  onMounted(async () => {
    isLoading.value = true
    error.value = null
    try {
      item.value = await fetchItemById(itemId)
    } catch (err) {
      error.value = err.message || 'Failed to load item'
      console.error('Error loading item:', err)
    } finally {
      isLoading.value = false
    }
  })
</script>

<style scoped>
  .map-wrapper, .map-wrapper .mapboxgl-map {
    width: 100%;
    height: 100%;
    min-height: 300px;
  }

  .label-cell {
    width: 40%;
    vertical-align: top;
    padding-top: 8px !important;
  }
</style>
