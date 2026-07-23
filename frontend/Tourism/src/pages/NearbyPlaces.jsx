import { useEffect, useState } from "react"
import useGeolocation from "../hooks/useGeolocation"
import nearbyApi from "../api/nearbyApi"
import MapView from "../components/map/MapView"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import PageHeader from "../components/common/PageHeader"
import { FiMapPin } from "react-icons/fi"

const NearbyPlaces = () => {
  const { position } = useGeolocation()
  const [places, setPlaces] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!position) return
    nearbyApi
      .getNearbyPlaces({ lat: position.lat, lng: position.lng, radius: 5000 })
      .then(({ data }) => setPlaces(data.items || data || []))
      .catch(() => setPlaces([]))
      .finally(() => setLoading(false))
  }, [position])

  return (
    <div className="container-app py-10">
      <PageHeader title="Nearby Places" subtitle="Attractions, cafes, and points of interest close to your current location." icon={FiMapPin} theme="teal" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <MapView userLocation={position} nearbyAttractions={places} height="450px" />
        </div>
        <div>
          {loading ? (
            <Loader />
          ) : places.length ? (
            <div className="space-y-3">
              {places.map((p) => (
                <div key={p.id} className="card-base p-4 flex items-center gap-3">
                  <FiMapPin className="text-primary-500" />
                  <div>
                    <p className="font-medium text-sm">{p.name}</p>
                    <p className="text-xs text-gray-400">{p.distance ? `${p.distance} km away` : p.category}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="No nearby places found" subtitle="Enable location access to see attractions around you." />
          )}
        </div>
      </div>
    </div>
  )
}

export default NearbyPlaces