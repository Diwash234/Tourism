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


  const [mapillaryToken, setMapillaryToken] = useState(
    MAPILLARY_ACCESS_TOKEN || ""
  )
  const [viewMode, setViewMode] = useState("map")


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

  const previewCenter = mapCenter || dest || user || DEFAULT_MAP_CENTER
  const streetViewUrl = `https://www.mapillary.com/app/?lat=${previewCenter.lat}&lng=${previewCenter.lng}&z=17`
  const directionsUrl = user && dest
    ? `https://www.google.com/maps/dir/?api=1&origin=${user.lat},${user.lng}&destination=${dest.lat},${dest.lng}`
    : null

  const renderViewToggle = (id, label) => (
    <button
      key={id}
      type="button"
      onClick={() => setViewMode(id)}
      className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${viewMode === id
        ? "bg-himalaya-600 text-white shadow-sm"
        : "bg-white/90 text-gray-700 hover:bg-white"}`}
    >
      {label}
    </button>
  )


  return (

    <div
      style={{ height }}
      className="rounded-xl overflow-hidden shadow-card relative"
    >


      <div className="absolute left-3 top-3 z-[1000] flex flex-wrap gap-2">
        {renderViewToggle("map", "Map")}
        {renderViewToggle("satellite", "Satellite")}
        {renderViewToggle("street", "Street view")}
      </div>

      {(mapillaryToken || viewMode === "street") && (
        <div className="absolute right-3 top-3 z-[1000] rounded-lg bg-white/90 px-3 py-1 text-[10px] font-semibold text-gray-700 shadow-sm">
          {mapillaryToken ? "Mapillary enabled" : "Mapillary preview"}
        </div>
      )}

      {viewMode === "street" ? (
        <div className="flex h-full w-full flex-col bg-gray-50">
          <div className="flex items-center justify-between border-b border-gray-200 bg-white/90 px-4 py-3 text-sm text-gray-700">
            <div>
              <p className="font-semibold">Street view preview</p>
              <p className="text-xs text-gray-500">Mapillary imagery for {dest?.name || "this location"}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <a
                href={streetViewUrl}
                target="_blank"
                rel="noreferrer"
                className="rounded-full border border-himalaya-200 px-3 py-1.5 text-xs font-semibold text-himalaya-700 hover:bg-himalaya-50"
              >
                Open in Mapillary
              </a>
              {directionsUrl && (
                <a
                  href={directionsUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-full border border-gray-200 px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-100"
                >
                  Get directions
                </a>
              )}
            </div>
          </div>
          <iframe
            title="Mapillary street view"
            src={streetViewUrl}
            className="h-full w-full border-0"
            loading="lazy"
          />
        </div>
      ) : (
      <MapContainer

        center={[
          mapCenter.lat,
          mapCenter.lng
        ]}

        zoom={13}

        scrollWheelZoom={true}

        style={{
          height: "100%",
          width: "100%"
        }}

      >


        <TileLayer

          attribution={viewMode === "satellite"
            ? "Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics"
            : "&copy; OpenStreetMap contributors"
          }

          url={viewMode === "satellite"
            ? "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            : MAP_TILE_URL
          }

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
                {dest.name}
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




        {
          fixedRoute.length > 1 &&

          <Polyline

            positions={fixedRoute}

            color="red"

            weight={5}

          />

        }


      </MapContainer>
      )}


    </div>

  )

}


export default MapView