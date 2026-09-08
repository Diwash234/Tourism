import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  useMap,
} from "react-leaflet"

import { useEffect, useState } from "react"

import configApi from "../../api/configApi"
import MapillaryImages from "./MapillaryImages"

import {
  MAP_TILE_URL,
  MAPILLARY_ACCESS_TOKEN,
  DEFAULT_MAP_CENTER,
} from "../../utils/constants"

import {
  userIcon,
  destinationIcon,
  hospitalIcon,
  policeIcon,
  attractionIcon,
} from "./icons"


/**
 * Convert different location formats into one consistent format.
 *
 * Supports:
 * {
 *   lat,
 *   lng,
 *   name
 * }
 *
 * or:
 * {
 *   latitude,
 *   longitude,
 *   Name
 * }
 */
const normalizeLocation = (place) => {
  if (!place) return null

  const latValue =
    place.lat ??
    place.latitude

  const lngValue =
    place.lng ??
    place.longitude

  const lat = Number(latValue)
  const lng = Number(lngValue)

  // Reject missing, NaN, or 0/0 coordinates
  if (
    !Number.isFinite(lat) ||
    !Number.isFinite(lng) ||
    lat === 0 ||
    lng === 0
  ) {
    return null
  }

  return {
    lat,
    lng,
    name:
      place.name ||
      place.Name ||
      place.title ||
      "Location",
  }
}


/**
 * Recenter map whenever center changes.
 */
const Recenter = ({ center }) => {
  const map = useMap()

  useEffect(() => {
    if (!center) return

    map.setView(
      [center.lat, center.lng],
      13
    )
  }, [center, map])

  return null
}


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

  /**
   * Satellite/map toggle
   * Restored from your first version.
   */
  const [satellite, setSatellite] = useState(false)


  /**
   * Mapillary token.
   *
   * First try the frontend constant.
   * Then try fetching the public token from backend config.
   */
  const [mapillaryToken, setMapillaryToken] = useState(
    MAPILLARY_ACCESS_TOKEN || ""
  )


  /**
   * Load Mapillary token from backend.
   */
  useEffect(() => {
    let ignore = false

    configApi
      .getPublicConfig()
      .then(({ data }) => {
        if (
          !ignore &&
          data?.mapillary_access_token
        ) {
          setMapillaryToken(
            data.mapillary_access_token
          )
        }
      })
      .catch(() => {
        if (!ignore) {
          setMapillaryToken(
            MAPILLARY_ACCESS_TOKEN || ""
          )
        }
      })

    return () => {
      ignore = true
    }
  }, [])


  /**
   * Normalize user and destination.
   */
  const user =
    normalizeLocation(userLocation)

  const dest =
    normalizeLocation(destination)


  /**
   * Determine map center.
   *
   * Priority:
   * 1. Explicit center
   * 2. User location
   * 3. Default Nepal center
   */
  const mapCenter =
    normalizeLocation(center) ||
    user ||
    DEFAULT_MAP_CENTER


  /**
   * Normalize route coordinates.
   *
   * Supports:
   *
   * [[lat, lng], [lat, lng]]
   *
   * OR:
   *
   * [
   *   { lat, lng },
   *   { latitude, longitude }
   * ]
   */
  const fixedRoute = route
    .map((point) => {
      if (Array.isArray(point)) {
        const lat = Number(point[0])
        const lng = Number(point[1])

        if (
          !Number.isFinite(lat) ||
          !Number.isFinite(lng)
        ) {
          return null
        }

        return [lat, lng]
      }

      if (!point) {
        return null
      }

      const lat = Number(
        point.lat ??
        point.latitude
      )

      const lng = Number(
        point.lng ??
        point.longitude
      )

      if (
        !Number.isFinite(lat) ||
        !Number.isFinite(lng)
      ) {
        return null
      }

      return [lat, lng]
    })
    .filter(Boolean)


  return (
    <div
      style={{ height }}
      className="relative rounded-xl overflow-hidden shadow-card"
    >

      {/* =========================================
          MAP CONTROLS
      ========================================== */}

      <button
        type="button"
        onClick={() =>
          setSatellite((current) => !current)
        }
        className="
          absolute
          top-3
          right-3
          z-[1000]
          bg-white
          shadow-md
          text-xs
          font-semibold
          px-3
          py-1.5
          rounded-full
          hover:bg-gray-50
        "
      >
        {satellite
          ? "Map View"
          : "Satellite View"}
      </button>


      {/* Mapillary status */}

      {mapillaryToken && (
        <div
          className="
            absolute
            top-14
            right-3
            z-[1000]
            rounded-lg
            bg-white/90
            px-3
            py-1
            text-[10px]
            font-semibold
            text-gray-700
            shadow-sm
          "
        >
          Mapillary enabled
        </div>
      )}


      {/* =========================================
          LEAFLET MAP
      ========================================== */}

      <MapContainer
        center={[
          mapCenter.lat,
          mapCenter.lng,
        ]}
        zoom={13}
        scrollWheelZoom={true}
        style={{
          height: "100%",
          width: "100%",
        }}
      >

        {/* =======================================
            BASE MAP
        ======================================== */}

        {satellite ? (
          <TileLayer
            attribution="Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics"
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          />
        ) : (
          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url={MAP_TILE_URL}
          />
        )}


        {/* =======================================
            RECENTER
        ======================================== */}

        <Recenter center={mapCenter} />


        {/* =======================================
            USER LOCATION
        ======================================== */}

        {user && (
          <Marker
            position={[
              user.lat,
              user.lng,
            ]}
            icon={userIcon}
          >
            <Popup>
              <div className="font-medium">
                You are here
              </div>
            </Popup>
          </Marker>
        )}


        {/* =======================================
            DESTINATION
        ======================================== */}

        {dest && (
          <Marker
            position={[
              dest.lat,
              dest.lng,
            ]}
            icon={destinationIcon}
          >

            <Popup>
              <div className="min-w-[220px]">

                <p className="font-semibold text-sm mb-2">
                  {dest.name}
                </p>


                {/* =================================
                    MAPILLARY STREET IMAGES
                ================================= */}

                {mapillaryToken ? (
                  <MapillaryImages
                    latitude={dest.lat}
                    longitude={dest.lng}
                    limit={3}
                    accessToken={mapillaryToken}
                  />
                ) : (
                  <p className="text-xs text-gray-500">
                    Mapillary images unavailable.
                  </p>
                )}

              </div>
            </Popup>

          </Marker>
        )}


        {/* =======================================
            NEARBY ATTRACTIONS
        ======================================== */}

        {nearbyAttractions.map(
          (p, index) => {
            const place =
              normalizeLocation(p)

            if (!place) {
              return null
            }

            return (
              <Marker
                key={`attr-${index}`}
                position={[
                  place.lat,
                  place.lng,
                ]}
                icon={attractionIcon}
              >
                <Popup>
                  <div className="font-medium">
                    {place.name}
                  </div>
                </Popup>
              </Marker>
            )
          }
        )}


        {/* =======================================
            HOSPITALS
        ======================================== */}

        {hospitals.map(
          (p, index) => {
            const place =
              normalizeLocation(p)

            if (!place) {
              return null
            }

            return (
              <Marker
                key={`hospital-${index}`}
                position={[
                  place.lat,
                  place.lng,
                ]}
                icon={hospitalIcon}
              >
                <Popup>
                  <div className="font-medium">
                    🏥 {place.name}
                  </div>
                </Popup>
              </Marker>
            )
          }
        )}


        {/* =======================================
            POLICE STATIONS
        ======================================== */}

        {policeStations.map(
          (p, index) => {
            const place =
              normalizeLocation(p)

            if (!place) {
              return null
            }

            return (
              <Marker
                key={`police-${index}`}
                position={[
                  place.lat,
                  place.lng,
                ]}
                icon={policeIcon}
              >
                <Popup>
                  <div className="font-medium">
                    🚓 {place.name}
                  </div>
                </Popup>
              </Marker>
            )
          }
        )}


        {/* =======================================
            ROUTE / DIRECTIONS
        ======================================== */}

        {fixedRoute.length > 1 && (
          <Polyline
            positions={fixedRoute}
            color="red"
            weight={5}
            opacity={0.8}
          />
        )}

      </MapContainer>

    </div>
  )
}


export default MapView