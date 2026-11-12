<template>
  <div class="map-wrapper">
    <mapbox-map
      v-model:map="mapInstance"
      :access-token="accessToken"
      map-style="mapbox://styles/mapbox/light-v11"
      :center="[5.1, 52.07]"
      :zoom="10.5"
      @mb-created="onMapCreated"
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
    </mapbox-map>
  </div>
</template>

<script setup>
  import { ref, computed, watch, nextTick, onActivated } from 'vue'
  import { useRuntimeConfig } from '#app'
  import { MapboxMap, MapboxCluster, MapboxNavigationControl, MapboxLayer } from '@studiometa/vue-mapbox-gl'
  import { bbox } from '@turf/turf'
  import { isEqual } from 'lodash-es'
  import { useSearchPageStore } from '~/stores/searchPage'
  import MapControlsZoom from '@/components/MapControlsZoom.vue'
  import MapCustomImage from '@/components/MapCustomImage.vue'
  import MapSelectTool from '@/components/MapSelectTool.vue'
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
  const accessToken = useRuntimeConfig().public.mapboxToken
  const imageLoaded = ref(false)
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
  
  // Timestamp that updates when featureCollectionWithGeometry changes — used as layer key
  const layerTimestamp = ref(Date.now())
  
  watch(
    () => store.featureCollectionWithGeometry,
    () => {
      layerTimestamp.value = Date.now()
    },
    { deep: true }
  )
  
  const clusterKey = computed(() => {
    if (!pointFeatures.value) return null
    return `cluster-${layerTimestamp.value}`
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

  // The Search page is kept alive (see app.vue), so this component is
  // hidden rather than destroyed when navigating away. Its container has
  // zero size while hidden, which leaves Mapbox's internal canvas size
  // stale; resize() re-measures the container once it's visible again.
  onActivated(() => {
    mapInstance.value?.resize()
  })

  // Prevents the cluster from zooming in when clicked; the map is not clickable.
  function onClusterClicked(_clusterId, event) {
    event?.preventDefault()
  }

  function onDrawChange({ feature }) {
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
