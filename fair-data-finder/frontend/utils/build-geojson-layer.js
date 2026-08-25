import { getType } from '@turf/invariant'

export default (featureCollection) => {
  if (!featureCollection || !featureCollection.features || featureCollection.features.length === 0) {
    return null
  }

  // At this point I assume that the featureCollection is a valid GeoJSON feature collection
  const feature = featureCollection.features[0]
  const type = getType(feature)
  
  if (type === 'Point' || type === 'MultiPoint') {
    return {
      id: 'features-collection',
      type: 'symbol',
      source: {
        type: 'geojson',
        data: featureCollection,
      },
      layout: {
        'icon-image': 'custom-marker',
        'icon-size': 0.04,
        'icon-allow-overlap': true,
        'icon-anchor': 'bottom',
      },
      paint: {},
    }
  }
  
  if (type === 'Polygon' || type === 'MultiPolygon') {
    // For polygons, return an array with both fill and line layers
    return [
      {
        id: 'features-collection-fill',
        type: 'fill',
        source: {
          type: 'geojson',
          data: featureCollection,
        },
        paint: {
          'fill-color': '#008fc5',
          'fill-opacity': 0.2,
        },
      },
      {
        id: 'features-collection-stroke',
        type: 'line',
        source: {
          type: 'geojson',
          data: featureCollection,
        },
        layout: {
          'line-cap': 'round',
          'line-join': 'round',
        },
        paint: {
          'line-color': '#ff0000',
          'line-width': 2,
        },
      },
    ]
  }

  if (type === 'LineString' || type === 'MultiLineString') {
    return {
      id: 'features-collection-line',
      type: 'line',
      source: {
        type: 'geojson',
        data: featureCollection,
      },
      layout: {
        'line-cap': 'round',
        'line-join': 'round',
      },
      paint: {
        'line-color': '#008fc5',
        'line-width': 2,
      },
    }
  }
  
  return null
}