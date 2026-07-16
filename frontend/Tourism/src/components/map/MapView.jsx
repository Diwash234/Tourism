import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from "react-leaflet"
import { useEffect } from "react"
import { MAP_TILE_URL, DEFAULT_MAP_CENTER } from "../../utils/constants"
import {
  userIcon,
  destinationIcon,
  hospitalIcon,
  policeIcon,
  attractionIcon,
} from "./icons"

const Recenter = ({ center }) => {
  const map = useMap()
  useEffect(() => {
    if (center) map.setView(center, map.getZoom())
  }, [center, map])
  return null
}

/**
 * Generic map view.
 * props:
 *  - center: {lat, lng}
 *  - userLocation: {lat, lng}
 *  - destination: {lat, lng, name}
 *  - nearbyAttractions: [{lat, lng, name}]
 *  - hospitals: [{lat, lng, name}]
 *  - policeStations: [{lat, lng, name}]
 *  - route: [[lat,lng], ...]
 *  - height
 */
const MapView = ({
  center,
  userLocation,
  destination,
  nearbyAttractions = [],
  hospitals = [],
  policeStations = [],
  route = [],
  height = "420px",
}) => {
  const mapCenter = center || userLocation || DEFAULT_MAP_CENTER

  return (
    <div style={{ height }} className="rounded-xl2 overflow-hidden shadow-card">
      <MapContainer
        center={[mapCenter.lat, mapCenter.lng]}
        zoom={13}
        scrollWheelZoom
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url={MAP_TILE_URL}
        />
        <Recenter center={mapCenter ? [mapCenter.lat, mapCenter.lng] : null} />

        {userLocation && (
          <Marker position={[userLocation.lat, userLocation.lng]} icon={userIcon}>
            <Popup>You are here</Popup>
          </Marker>
        )}

        {destination && (
          <Marker position={[destination.lat, destination.lng]} icon={destinationIcon}>
            <Popup>{destination.name}</Popup>
          </Marker>
        )}

        {nearbyAttractions.map((place, idx) => (
          <Marker key={`attr-${idx}`} position={[place.lat, place.lng]} icon={attractionIcon}>
            <Popup>{place.name}</Popup>
          </Marker>
        ))}

        {hospitals.map((place, idx) => (
          <Marker key={`hosp-${idx}`} position={[place.lat, place.lng]} icon={hospitalIcon}>
            <Popup>🏥 {place.name}</Popup>
          </Marker>
        ))}

        {policeStations.map((place, idx) => (
          <Marker key={`pol-${idx}`} position={[place.lat, place.lng]} icon={policeIcon}>
            <Popup>🚓 {place.name}</Popup>
          </Marker>
        ))}

        {route.length > 1 && <Polyline positions={route} color="#FF5A5F" weight={5} />}
      </MapContainer>
    </div>
  )
}

export default MapView