import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  useMap,
  useMapEvents,
} from "react-leaflet"

import { useEffect, useState } from "react"

import configApi from "../../api/configApi"
import MapillaryImages from "./MapillaryImages"
import {
  MAPILLARY_ACCESS_TOKEN,
  DEFAULT_MAP_CENTER,
} from "../../utils/constants"

const TILE_PROVIDERS = {
  detailed: {
    name: "Detailed Road Map",
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attr: "&copy; OpenStreetMap contributors",
  },
  standard: {
    name: "Standard Light",
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attr: "&copy; OpenStreetMap contributors",
  },
  satellite: {
    name: "Satellite",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr: "Tiles &copy; Esri &mdash; Source: Esri, USGS",
  },
}

import {
  userIcon,
  destinationIcon,
  hospitalIcon,
  policeIcon,
  attractionIcon,
} from "./icons"


const normalizeLocation = (place) => {

  if (!place) return null

  const lat = Number(place.lat) || Number(place.latitude)
  const lng = Number(place.lng) || Number(place.longitude)

  // Prevent invalid coordinates like [0,0]
  if (!lat || !lng || Number.isNaN(lat) || Number.isNaN(lng)) {
    return null
  }

  return {
    lat,
    lng,
    name:
      place.name ||
      place.Name ||
      "Location"
  }
}


const Recenter = ({ center }) => {
  const map = useMap()
  useEffect(() => {
    if (center) {
      map.setView([center.lat, center.lng], 13)
    }
  }, [center, map])
  return null
}

const MapMeasureEvents = ({ active, onPoint }) => {
  useMapEvents({
    click(e) {
      if (active) {
        onPoint([e.latlng.lat, e.latlng.lng])
      }
    },
  })
  return null
}

const haversineKm = (lat1, lon1, lat2, lon2) => {
  const r = 6371.0
  const dlat = ((lat2 - lat1) * Math.PI) / 180.0
  const dlon = ((lon2 - lon1) * Math.PI) / 180.0
  const a =
    Math.sin(dlat / 2.0) ** 2 +
    Math.cos((lat1 * Math.PI) / 180.0) *
      Math.cos((lat2 * Math.PI) / 180.0) *
      Math.sin(dlon / 2.0) ** 2
  return r * 2.0 * Math.atan2(Math.sqrt(a), Math.sqrt(1.0 - a))
}


const MapView = ({
  center,
  userLocation,
  destination,
  nearbyAttractions = [],
  hospitals = [],
  policeStations = [],
  route = [],
  height = "420px"
}) => {
  const [mapStyle, setMapStyle] = useState("detailed")
  const [measureMode, setMeasureMode] = useState(false)
  const [measurePoints, setMeasurePoints] = useState([])
  const [layers] = useState({
    route: true,
    destination: true,
    attractions: true,
    hospitals: true,
    police: true,
    mapillary: true,
  })


  const [mapillaryToken, setMapillaryToken] = useState(
    MAPILLARY_ACCESS_TOKEN || ""
  )


  useEffect(() => {

    let ignore = false

    configApi
      .getPublicConfig()
      .then(({ data }) => {

        if (!ignore && data?.mapillary_access_token) {
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



  const user =
    normalizeLocation(userLocation)


  const dest =
    normalizeLocation(destination)



  const mapCenter =
    normalizeLocation(center)
    ||
    user
    ||
    DEFAULT_MAP_CENTER



  const fixedRoute =
    route.map(point => {

      if (Array.isArray(point)) {
        return point
      }

      return [
        Number(point.lat || point.latitude),
        Number(point.lng || point.longitude)
      ]

    })



  const activeTile = TILE_PROVIDERS[mapStyle] || TILE_PROVIDERS.detailed

  const totalMeasuredKm = measurePoints.reduce((acc, curr, idx) => {
    if (idx === 0) return 0
    const prev = measurePoints[idx - 1]
    return acc + haversineKm(prev[0], prev[1], curr[0], curr[1])
  }, 0)

  return (
    <div
      style={{ height }}
      className="rounded-xl overflow-hidden shadow-card relative"
    >
      {/* Map Style Selector & Ruler Tool */}
      <div className="absolute top-3 left-3 z-[1000] bg-white/95 backdrop-blur border border-slate-200 rounded-xl p-1.5 shadow-md flex items-center gap-1.5 text-[11px] font-bold">
        {Object.entries(TILE_PROVIDERS).map(([key, provider]) => (
          <button
            key={key}
            type="button"
            onClick={() => setMapStyle(key)}
            className={`px-2.5 py-1 rounded-lg transition-all ${
              mapStyle === key ? "bg-slate-900 text-white shadow" : "text-slate-700 hover:bg-slate-100"
            }`}
          >
            {provider.name}
          </button>
        ))}
        <div className="h-4 w-px bg-slate-200 mx-1" />
        <button
          type="button"
          onClick={() => {
            setMeasureMode(!measureMode)
            if (measureMode) setMeasurePoints([])
          }}
          className={`px-2.5 py-1 rounded-lg transition-all ${
            measureMode ? "bg-amber-500 text-slate-950 font-black shadow" : "text-slate-700 hover:bg-slate-100"
          }`}
        >
          📏 {measureMode ? "Cancel Ruler" : "Measure Distance"}
        </button>
      </div>

      {measureMode && (
        <div className="absolute top-14 left-3 z-[1000] bg-slate-950/90 text-white border border-amber-400/50 rounded-xl p-2.5 text-xs shadow-xl space-y-1">
          <p className="font-bold text-amber-300">Click points on the map to measure geodesic distance</p>
          <p className="text-[11px] text-slate-200">
            Measured: <b className="text-white text-sm">{totalMeasuredKm.toFixed(2)} km</b> ({ (totalMeasuredKm * 0.621371).toFixed(2) } mi)
          </p>
          {measurePoints.length > 0 && (
            <button
              type="button"
              onClick={() => setMeasurePoints([])}
              className="text-[10px] text-amber-300 underline font-bold"
            >
              Clear points ({measurePoints.length})
            </button>
          )}
        </div>
      )}

      {/* Mapillary Badge */}
      {mapillaryToken && layers.mapillary && (
        <div className="absolute right-3 top-3 z-[1000] rounded-lg bg-white/90 px-3 py-1 text-[10px] font-semibold text-gray-700 shadow-sm">
          Mapillary enabled
        </div>
      )}

      <MapContainer
        center={[mapCenter.lat, mapCenter.lng]}
        zoom={13}
        scrollWheelZoom={true}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          key={mapStyle}
          attribution={activeTile.attr}
          url={activeTile.url}
        />

        <MapMeasureEvents active={measureMode} onPoint={(pt) => setMeasurePoints((prev) => [...prev, pt])} />

        {measurePoints.length > 1 && (
          <Polyline
            positions={measurePoints}
            color="#f59e0b"
            weight={4}
            dashArray="6, 6"
          />
        )}

        <Recenter center={mapCenter} />



        {
          user && (

            <Marker

              position={[
                user.lat,
                user.lng
              ]}

              icon={userIcon}

            >

              <Popup>
                You are here
              </Popup>

            </Marker>

          )
        }




        {
          dest && (

            <Marker

              position={[
                dest.lat,
                dest.lng
              ]}

              icon={destinationIcon}

            >

              <Popup>
                <div className="min-w-[160px]">
                  <p className="font-semibold text-sm mb-2">{dest.name}</p>
                  {/* Mapillary street imagery (uses VITE_MAPILLARY_ACCESS_TOKEN
                      from env / backend public config) */}
                  <MapillaryImages latitude={dest.lat} longitude={dest.lng} limit={3} />
                </div>
              </Popup>

            </Marker>

          )
        }




        {
          nearbyAttractions.map((p, index) => {

            const place =
              normalizeLocation(p)


            if (!place || !place.lat || !place.lng)
              return null


            return (

              <Marker

                key={"attr" + index}

                position={[
                  place.lat,
                  place.lng
                ]}

                icon={attractionIcon}

              >

                <Popup>
                  {place.name}
                </Popup>

              </Marker>

            )

          })
        }




        {
          hospitals.map((p, index) => {

            const place =
              normalizeLocation(p)


            if (!place || !place.lat || !place.lng)
              return null


            return (

              <Marker

                key={"hospital" + index}

                position={[
                  place.lat,
                  place.lng
                ]}

                icon={hospitalIcon}

              >

                <Popup>
                  🏥 {place.name}
                </Popup>

              </Marker>

            )

          })
        }




        {
          policeStations.map((p, index) => {

            const place =
              normalizeLocation(p)


            if (!place || !place.lat || !place.lng)
              return null


            return (

              <Marker

                key={"police" + index}

                position={[
                  place.lat,
                  place.lng
                ]}

                icon={policeIcon}

              >

                <Popup>
                  🚓 {place.name}
                </Popup>

              </Marker>

            )

          })
        }




        {fixedRoute.length > 1 && layers.route && (
          <>
            <Polyline
              positions={fixedRoute}
              color="#0f172a"
              weight={8}
              opacity={0.3}
              lineCap="round"
              lineJoin="round"
            />
            <Polyline
              positions={fixedRoute}
              color="#2563eb"
              weight={5}
              opacity={0.9}
              lineCap="round"
              lineJoin="round"
            />
          </>
        )}


      </MapContainer>


    </div>

  )

}


export default MapView