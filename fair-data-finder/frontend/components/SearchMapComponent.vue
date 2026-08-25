<template>
  <div class="map-wrapper">
    <mapbox-map
      v-model:map="mapInstance"
      :access-token="accessToken"
      map-style="mapbox://styles/mapbox/light-v11"
      :center="[5.1, 52.07]"
      :zoom="10.5"
      @mb-created="onMapCreated"
      @mb-click="onMapClick"
    >
      <!-- Points: clustered marker layer -->
      <MapboxCluster
        v-if="pointFeatures && imageLoaded"
        :key="clusterKey"
        :data="pointFeatures"
        :cluster-max-zoom="14"
        :cluster-radius="50"
        :cluster-min-points="2"
        :unclustered-point-layer-type="'symbol'"
        :unclustered-point-layout="unclusteredPointLayout"
        :unclustered-point-paint="unclusteredPointPaint"
        :clusters-paint="clustersPaint"
        :cluster-count-layout="clusterCountLayout"
        :cluster-count-paint="clusterCountPaint"
        @mb-feature-click="onFeatureClicked"
        @mb-cluster-click="onClusterClicked"
      />

      <!-- Polygons and lines: layers built by build-geojson-layer.js -->
      <MapboxLayer
        v-for="layer in mapLayers"
        :key="layer.id"
        :id="layer.id"
        :options="layer"
      />
    
      <MapControlsZoom
        v-if="bounds.length >= 4 && !hasActivePolygonFilter"
        :bounds="bounds"
      />
      <MapCustomImage
        image-path="/custom-marker.png"
        image-name="custom-marker"
        @image-loaded="imageLoaded = true"
      />
      <MapboxNavigationControl position="bottom-right" :show-compass="false" />
      <MapControlsZoom
        v-if="mapInstance && store.selectedFeatureBbox"
        :bounds="store.selectedFeatureBbox"
        :padding="50"
        :duration="1000"
        :zoom-on-mount="false"
      />
      <MapSelectTool
        v-if="mapInstance"
        ref="drawControlRef"
        :show-buttons="true"
        :enabled-tools="['polygon']"
        @change="onDrawChange"
      />
      
      <MapPopup
        v-if="selectedFeature && popupCoordinates && Array.isArray(popupCoordinates) && popupCoordinates.length === 2"
        :selected-feature="selectedFeature"
        :coordinates="popupCoordinates"
        :close-button="false"
        :close-on-click="true"
        :close-on-move="false"
        max-width="420px"
        @close="onPopupClose"
      />
    </mapbox-map>
  </div>
</template>

<script setup>
  import { ref, computed, watch, nextTick, onUnmounted } from 'vue'
  import { MapboxMap, MapboxCluster, MapboxNavigationControl, MapboxLayer } from '@studiometa/vue-mapbox-gl'
  import { center, bbox } from '@turf/turf'
  import { isEqual } from 'lodash-es'
  import { useSearchPageStore } from '~/stores/searchPage'
  import MapControlsZoom from '@/components/MapControlsZoom.vue'
  import MapCustomImage from '@/components/MapCustomImage.vue'
  import MapSelectTool from '@/components/MapSelectTool.vue'
  import MapPopup from '@/components/MapPopup.vue'
  import * as geojsonBounds from 'geojson-bounds'
  import {
    unclusteredPointLayout,
    unclusteredPointPaint,
    clustersPaint,
    clusterCountLayout,
    clusterCountPaint
  } from '~/utils/mapbox-cluster-config'
  import buildGeoJsonLayer from '~/utils/build-geojson-layer'

  const POINT_TYPES = new Set([ 'Point', 'MultiPoint' ])
  const POLYGON_TYPES = new Set([ 'Polygon', 'MultiPolygon' ])
  const LINE_TYPES = new Set([ 'LineString', 'MultiLineString' ])

  const mapInstance = ref(null)
  const accessToken = import.meta.env.VITE_MAPBOX_TOKEN
  const imageLoaded = ref(false)
  const selectedFeature = ref(null)
  const justClickedFeature = ref(false)
  const isDrawingActive = ref(false)
  let mapClickTimeout = null
  
  const store = useSearchPageStore()
  
  // Draw control reference
  const drawControlRef = ref(null)
  
  // Default bbox (whole world)
  const DEFAULT_BBOX = [180, 90, -180, -90]
  
  // Flag to prevent recursive updates
  const isClearingPolygon = ref(false)

  // Split feature collection by geometry type for separate map layers
  function filterByType (types) {
    return computed(() => {
      const fc = store.featureCollectionWithGeometry
      if (!fc) return null
      const features = fc.features.filter(f => f.geometry && types.has(f.geometry.type))
      if (features.length === 0) return null
      return { ...fc, features }
    })
  }

  const pointFeatures = filterByType(POINT_TYPES)
  const polygonFeatures = filterByType(POLYGON_TYPES)
  const lineFeatures = filterByType(LINE_TYPES)

  // All non-point layers built by build-geojson-layer.js, keyed by timestamp so
  // Vue unmounts/remounts them when search results change (avoids Mapbox GL
  // "layer already added" errors).
  const mapLayers = computed(() => {
    const ts = layerTimestamp.value
    return [
      buildGeoJsonLayer(polygonFeatures.value),
      buildGeoJsonLayer(lineFeatures.value),
    ]
      .flat()
      .filter(Boolean)
      .map(layer => ({ ...layer, id: `${layer.id}-${ts}` }))
  })
  
  // Check if polygon filter is active (bbox is not default)
  const hasActivePolygonFilter = computed(() => {
    if (!store.bboxFilter || store.bboxFilter.length !== 4) return false
    return !isEqual(store.bboxFilter, DEFAULT_BBOX)
  })
  
  // Watch for bboxFilter changes to clear polygon when reset to default
  watch(
    () => store.bboxFilter,
    (newBbox, oldBbox) => {
      // Skip if we're already clearing (prevent recursion)
      if (isClearingPolygon.value) return
      
      // Only clear if bboxFilter was changed from non-default to default
      const wasNonDefault = oldBbox && oldBbox.length === 4 && !isEqual(oldBbox, DEFAULT_BBOX)
      
      if (wasNonDefault &&
        newBbox &&
        newBbox.length === 4 &&
        isEqual(newBbox, DEFAULT_BBOX) &&
        drawControlRef.value) {
        const draw = drawControlRef.value.getDraw()
        if (draw) {
          const { features } = draw.getAll()
          if (features && features.length > 0) {
            isClearingPolygon.value = true
            drawControlRef.value.clear()
            nextTick(() => {
              setTimeout(() => {
                isClearingPolygon.value = false
              }, 100)
            })
          }
        }
      }
    }
  )
  
  // Watch for changes to selectedFeatureId from store (e.g., when clicking a card in the list)
  watch(
    () => store.selectedFeatureId,
    (newFeatureId) => {
      if (!newFeatureId) {
        selectedFeature.value = null
        justClickedFeature.value = false
        return
      }
      
      if (selectedFeature.value?.id === newFeatureId) {
        return
      }
      
      const isMapClickUpdate = justClickedFeature.value && 
        selectedFeature.value?.id === newFeatureId
      
      if (isMapClickUpdate) {
        return
      }
      
      justClickedFeature.value = false
      
      if (mapClickTimeout) {
        clearTimeout(mapClickTimeout)
        mapClickTimeout = null
      }
      
      if (store.featureCollectionWithGeometry && store.featureCollectionWithGeometry.features) {
        const feature = store.featureCollectionWithGeometry.features.find(f => f.id === newFeatureId)
        if (feature) {
          selectedFeature.value = feature
          if (feature.bbox) {
            store.setSelectedFeatureBbox(feature.bbox)
          }
        }
      }
    }
  )
  
  // Timestamp that updates when featureCollectionWithGeometry changes — used as layer key
  const layerTimestamp = ref(Date.now())
  
  watch(
    () => store.featureCollectionWithGeometry,
    () => {
      layerTimestamp.value = Date.now()
    },
    { deep: true }
  )
  
  // Track cleanup functions for direct Mapbox GL click listeners on polygon/line layers.
  // We bypass MapboxLayer's emit system because the component declares no `emits`, so
  // emit('mb-click') falls through to the root <div> instead of calling the parent handler.
  let layerClickCleanup = []

  watch(
    mapLayers,
    (newLayers) => {
      // Remove listeners registered for the previous set of layers
      layerClickCleanup.forEach(fn => fn())
      layerClickCleanup = []

      if (!mapInstance.value || !newLayers.length) return

      newLayers.forEach(layer => {
        const handler = (event) => onLayerFeatureClicked(event)
        mapInstance.value.on('click', layer.id, handler)
        layerClickCleanup.push(() => {
          mapInstance.value?.off('click', layer.id, handler)
        })
      })
    },
    { flush: 'post' }
  )

  onUnmounted(() => {
    layerClickCleanup.forEach(fn => fn())
    layerClickCleanup = []
  })
  
  const clusterKey = computed(() => {
    if (!pointFeatures.value) return null
    return `cluster-${layerTimestamp.value}`
  })
  
  // Popup coordinates computed property
  const popupCoordinates = computed(() => {
    if (!selectedFeature.value?.geometry) {
      return null
    }
    
    const geometry = selectedFeature.value.geometry
    
    if (geometry.type === 'Point') {
      const coords = geometry.coordinates
      if (Array.isArray(coords) && coords.length >= 2) {
        return [coords[0], coords[1]]
      }
      return null
    }
    
    try {
      const centerPoint = center(selectedFeature.value)
      const coords = centerPoint.geometry.coordinates
      if (Array.isArray(coords) && coords.length >= 2) {
        return [coords[0], coords[1]]
      }
      return null
    } catch {
      return null
    }
  })

  const bounds = computed(() => {
    if (!store.featureCollectionWithGeometry) {
      return []
    }
    const extent = geojsonBounds.extent(store.featureCollectionWithGeometry)
    if (!extent || extent.length < 4) {
      return []
    }
    return extent
  })
  
  function onMapCreated(map) {
    mapInstance.value = map
  }

  // Shared feature-selection logic used by both cluster and layer click handlers
  async function selectFeature(featureId) {
    if (!featureId) {
      justClickedFeature.value = false
      return
    }

    let matchedFeature = null
    if (store.featureCollectionWithGeometry && store.featureCollectionWithGeometry.features) {
      matchedFeature = store.featureCollectionWithGeometry.features.find(f => f.id === featureId)
    }

    if (!matchedFeature) return

    const currentId = selectedFeature.value?.id
    if (currentId && currentId === matchedFeature.id) {
      setTimeout(() => { justClickedFeature.value = false }, 100)
      return
    }

    selectedFeature.value = matchedFeature
    store.setSelectedFeature(matchedFeature.id)
    if (matchedFeature.bbox) {
      store.setSelectedFeatureBbox(matchedFeature.bbox)
    }

    await nextTick()
    setTimeout(() => { justClickedFeature.value = false }, 400)
  }
  
  async function onFeatureClicked(feature, event) {
    if (isDrawingActive.value) return

    if (mapClickTimeout) {
      clearTimeout(mapClickTimeout)
      mapClickTimeout = null
    }
    
    justClickedFeature.value = true
    
    if (event) {
      if (event.originalEvent) {
        event.originalEvent.stopPropagation()
        event.originalEvent.preventDefault()
      }
      if (event.stopPropagation) {
        event.stopPropagation()
      }
    }
    
    const featureId = feature.properties?.id || feature.id
    await selectFeature(featureId)
  }

  // Click handler for MapboxLayer (polygon / line layers)
  async function onLayerFeatureClicked(event) {
    if (isDrawingActive.value) return

    if (mapClickTimeout) {
      clearTimeout(mapClickTimeout)
      mapClickTimeout = null
    }

    justClickedFeature.value = true

    if (event?.originalEvent) {
      event.originalEvent.stopPropagation()
    }

    const feature = event?.features?.[0]
    const featureId = feature?.properties?.id || feature?.id
    await selectFeature(featureId)
  }
  
  function onClusterClicked() {
    selectedFeature.value = null
    store.clearSelectedFeature()
  }
  
  function onMapClick() {
    if (isDrawingActive.value) return

    if (mapClickTimeout) {
      clearTimeout(mapClickTimeout)
    }
    
    mapClickTimeout = setTimeout(() => {
      mapClickTimeout = null
      if (justClickedFeature.value) {
        return
      }
      selectedFeature.value = null
      store.clearSelectedFeature()
    }, 150)
  }

  function onPopupClose() {
    if (!justClickedFeature.value && !store.selectedFeatureId) {
      selectedFeature.value = null
      store.clearSelectedFeature()
    }
  }

  function onDrawChange({ feature, active }) {
    isDrawingActive.value = !!active
    if (isClearingPolygon.value) return
    if (!feature || !feature.geometry) {
      const currentBbox = store.bboxFilter
      if (!currentBbox || !isEqual(currentBbox, DEFAULT_BBOX)) {
        store.bboxFilter = [...DEFAULT_BBOX]
      }
      return
    }
    
    const featureBbox = bbox(feature)
    store.bboxFilter = featureBbox
  }
</script>

<style>
.map-wrapper, .map-wrapper .mapboxgl-map { width: 100%; height: 100%; }
</style>
