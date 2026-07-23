import { useEffect, useState } from "react"
import MapView from "../components/map/MapView"
import useGeolocation from "../hooks/useGeolocation"
import nearbyApi from "../api/nearbyApi"
import Loader from "../components/common/Loader"
import PageHeader from "../components/common/PageHeader"
import { FiNavigation, FiMapPin } from "react-icons/fi"

const Navigation = () => {
  const { position } = useGeolocation()
  const [destinationQuery, setDestinationQuery] = useState("")
  const [destination, setDestination] = useState(null)
  const [route, setRoute] = useState([])
  const [loading, setLoading] = useState(false)

  const handleGetRoute = async (e) => {
    e.preventDefault()
    if (!position || !destinationQuery) return
    setLoading(true)
    try {
      const { data } = await nearbyApi.getRoute({
        origin: position,
        destinationName: destinationQuery,
      })
      setDestination(data.destination)
      setRoute(data.route || [])
    } catch {
      setRoute([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container-app py-10">
      <PageHeader title="Navigation" subtitle="Get directions from your current location to any destination." icon={FiNavigation} theme="blue" />
      <form onSubmit={handleGetRoute} className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <FiMapPin className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            className="input-field pl-11"
            placeholder="Where are you headed?"
            value={destinationQuery}
            onChange={(e) => setDestinationQuery(e.target.value)}
          />
        </div>
        <button className="bg-blue-500 hover:bg-blue-600 text-white font-semibold px-5 py-2.5 rounded-xl transition" disabled={loading}>
          {loading ? "Locating route..." : "Get Directions"}
        </button>
      </form>

      <MapView
        userLocation={position}
        destination={destination}
        route={route}
        height="500px"
      />
    </div>
  )
}

export default Navigation