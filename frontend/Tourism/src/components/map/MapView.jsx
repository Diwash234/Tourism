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
  MAPILLARY_ACCESS_TOKEN,
  DEFAULT_MAP_CENTER,
} from "../../utils/constants"

const TILE_PROVIDERS = {
  detailed: {
    name: "Detailed Road Map",
    url: "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
    attr: "&copy; OpenStreetMap contributors &copy; CARTO",
  },
  standard: {
    name: "Standard Light",
    url: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    attr: "&copy; OpenStreetMap &copy; CARTO",
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
      map.setView(
        [center.lat, center.lng],
        13
      )
    }

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
  height = "420px"
}) => {
  const [mapStyle, setMapStyle] = useState("detailed")
  const [layers, setLayers] = useState({
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

  return (
    <div
      style={{ height }}
      className="rounded-xl overflow-hidden shadow-card relative"
    >
      {/* Map Style Selector */}
      <div className="absolute top-3 left-3 z-[1000] bg-white/95 backdrop-blur border border-slate-200 rounded-xl p-1.5 shadow-md flex gap-1 text-[11px] font-bold">
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
      </div>

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