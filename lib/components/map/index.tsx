import set from 'lodash/set'
import dynamic from 'next/dynamic'
import {useEffect, useRef, useState} from 'react'
import {
  AttributionControl,
  Map as LeafletMap,
  Viewport,
  ZoomControl
} from 'react-leaflet'
import {useSelector} from 'react-redux'

import useRouteChanging from 'lib/hooks/use-route-changing'
import selectModificationSaveInProgress from 'lib/selectors/modification-save-in-progress'
import selectRegionBounds from 'lib/selectors/region-bounds'
import {getParsedItem, stringifyAndSet} from 'lib/utils/local-storage'

import Geocoder from './geocoder'

const MapboxGLLayer = dynamic(() => import('./mapbox-gl'))

const VIEWPORT_KEY = 'analysis-map-viewport'
const ZOOM = 12
const MIN_ZOOM = 3 // Odd map shifts happen at lower zoom levels
const DEFAULT_VIEWPORT: Viewport = {
  center: [38, -77],
  zoom: ZOOM
}

export default function Map({children, setLeafletContext}) {
  const leafletMapRef = useRef<LeafletMap>()
  const regionBounds = useSelector(selectRegionBounds)
  const [viewport, setViewport] = useState<Viewport>(() => ({
    ...DEFAULT_VIEWPORT,
    ...getParsedItem(VIEWPORT_KEY)
  }))
  const saveInProgress = useSelector(selectModificationSaveInProgress)
  const [routeChanging] = useRouteChanging()

  // On mount, store the leaflet element
  useEffect(() => {
    const map = leafletMapRef.current?.leafletElement
    if (map) {
      // Attach the leaflet map to `window` if it exists. Helpful with Cypress test
      set(window, 'LeafletMap', map)
      // Store the leaflet context for consuming elsewhere
      setLeafletContext({map, layerContainer: map})
    }
  }, [leafletMapRef, setLeafletContext])

  // Map container map change sizes between pages
  useEffect(() => {
    const map = leafletMapRef.current?.leafletElement
    if (map && !routeChanging) {
      map.invalidateSize()

      // Delay an additional inalidation to allow for elements to change the
      // viewport size. This is hacky, but we don't currently have an application
      // state to indicate that all elements have been drawn.
      const id = setTimeout(() => {
        map.invalidateSize()
      }, 100)
      return () => clearTimeout(id)
    }
  }, [routeChanging, leafletMapRef])

  // If center is not within region bounds, reset to center
  useEffect(() => {
    if (regionBounds) {
      const center = viewport?.center
      const regionCenter = regionBounds.getCenter()
      if (!center || !regionBounds.contains(center)) {
        setViewport({
          center: [regionCenter.lat, regionCenter.lng],
          zoom: ZOOM
        })
      }
    }
  }, [leafletMapRef, regionBounds, viewport])

  return (
    <>
      <LeafletMap
        attributionControl={false}
        className={routeChanging || saveInProgress ? 'disableAndDim' : ''}
        minZoom={MIN_ZOOM}
        onViewportChanged={(v) => stringifyAndSet(VIEWPORT_KEY, v)}
        preferCanvas={true}
        ref={leafletMapRef}
        tap={false}
        viewport={viewport || DEFAULT_VIEWPORT}
        zoomControl={false}
      >
        {process.env.NEXT_PUBLIC_BASEMAP_DISABLED !== 'true' && (
          <MapboxGLLayer />
        )}

        <AttributionControl position='bottomright' prefix={false} />
        <ZoomControl position='topright' />

        {!routeChanging && children ? children : null}
      </LeafletMap>

      <Geocoder
        isDisabled={routeChanging || saveInProgress}
        map={leafletMapRef.current?.leafletElement}
      />
    </>
  )
}
