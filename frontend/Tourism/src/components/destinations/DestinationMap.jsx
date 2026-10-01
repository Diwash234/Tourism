import { useEffect } from "react"
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents } from "react-leaflet"
import { destinationIcon, userIcon } from "../map/icons"
import { DEFAULT_MAP_CENTER } from "../../utils/constants"

/**
 * Destination map used by the nearby-places explorers.
 *
 * Callers pass:
 *   destinations - result rows; coordinates may be latitude/longitude or lat/lng
 *   center       - { lat, lng } of the picked/user location (or null)
 *   onMapClick   - (lat, lng) => void so a visitor can pick a location by clicking
 *   height       - CSS height of the map ("400px" by default)
 *
 * This file used to contain a stray copy of NearbyPlacesAdvanced that imported
 * itself, so rendering it recursed until the tab crashed and the import of the
 * not-installed "react-fi" package broke the production build.
 */
const toLatLng = (value) => {
  const lat = Number(value?.latitude ?? value?.lat)
  const lng = Number(value?.longitude ?? value?.lng)
  return Number.isFinite(lat) && Number.isFinite(lng) ? { lat, lng } : null
}

function MapEvents({ onMapClick }) {
  useMapEvents({
    click: (event) => onMapClick?.(event.latlng.lat, event.latlng.lng),
  })
  return null
}

function Recenter({ center }) {
  const map = useMap()
  useEffect(() => {
    if (center) map.setView([center.lat, center.lng])
  }, [map, center])
  return null
}

export default function DestinationMap({ destinations = [], center = null, onMapClick, height = "400px" }) {
  const initial = center || DEFAULT_MAP_CENTER
  const markers = (Array.isArray(destinations) ? destinations : [])
    .map((item) => ({ item, position: toLatLng(item) }))
    .filter((entry) => entry.position)

  return (
    <div
      className="overflow-hidden rounded-2xl border border-[var(--ny-border)] bg-gray-100 dark:bg-slate-800"
      style={{ height }}
    >
      <MapContainer
        center={[initial.lat, initial.lng]}
        zoom={11}
        scrollWheelZoom
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapEvents onMapClick={onMapClick} />
        <Recenter center={center} />

        {markers.map(({ item, position }, index) => (
          <Marker
            key={item?.id ?? `${position.lat}-${position.lng}-${index}`}
            position={[position.lat, position.lng]}
            icon={destinationIcon}
          >
            <Popup>
              <span>{item?.name || item?.title || "Destination"}</span>
            </Popup>
          </Marker>
        ))}

        {center && (
          <Marker position={[center.lat, center.lng]} icon={userIcon}>
            <Popup>Selected location</Popup>
          </Marker>
        )}
      </MapContainer>
    </div>
  )
}
