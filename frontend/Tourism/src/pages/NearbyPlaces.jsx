// CONFIRMED WORKING as-is — no changes needed. GET /nearby/places now
// exists on the backend (combines your Destination table + live OSM
// points), returning a plain array with `name`/`distance`/`category`
// fields matching exactly what this page reads.

import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { motion } from "framer-motion"
import useGeolocation from "../hooks/useGeolocation"
import nearbyApi from "../api/nearbyApi"
import MapView from "../components/map/MapView"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import { FiMapPin } from "react-icons/fi"

const NearbyPlaces = () => {
  const { position } = useGeolocation()
  const [places, setPlaces] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!position) {
      setLoading(false)
      return
    }

    setLoading(true)
    nearbyApi
      .getNearbyPlaces({
        lat: position.lat,
        lng: position.lng,
        radius: 30000,
      })
      .then(({ data }) => {
        const list = data.items || data.results || data || []
        setPlaces(Array.isArray(list) ? list : [])
      })
      .catch((error) => {
        console.log(error)
        setPlaces([])
      })
      .finally(() => setLoading(false))
  }, [position])

  return (
    <div className="container-app py-10 fade-in theme-forest">
      <h1 className="section-title flex items-center gap-2">
        <FiMapPin className="text-himalaya-500" />
        Nearby Places
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-xl2 overflow-hidden shadow-premium">
          <MapView
            userLocation={position}
            nearbyAttractions={places}
            height="450px"
          />
        </div>

        <div>
          {loading ? (
            <Loader />
          ) : places.length ? (
            <div className="space-y-3">
              {places.map((p, i) => (
                <motion.div
                  key={p.id}
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: Math.min(i * 0.04, 0.4) }}
                  className="card-base p-4 flex items-center gap-3"
                >
                  <FiMapPin className="text-himalaya-500" />

                  <div>
                    {p.slug ? (
                      <Link to={`/destinations/${p.slug}`} className="font-medium text-sm text-emerald-800 hover:underline">
                        {p.name}
                      </Link>
                    ) : (
                      <p className="font-medium text-sm">{p.name}</p>
                    )}

                    <p className="text-xs text-gray-400">
                      {[p.distance != null ? `${p.distance} km` : p.distance_km != null ? `${p.distance_km} km` : null, p.district || p.city, p.category].filter(Boolean).join(" · ")}
                    </p>
                    {p.latitude != null && p.longitude != null && (
                      <p className="text-[11px] font-mono text-emerald-800">{Number(p.latitude).toFixed(4)}°, {Number(p.longitude).toFixed(4)}°</p>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No nearby places found"
              subtitle="Enable location access to see attractions around you."
            />
          )}
        </div>
      </div>
    </div>
  )
}

export default NearbyPlaces