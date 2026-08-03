import { useState, useEffect } from "react"
import { useParams } from "react-router-dom"
import { FiMapPin, FiClock } from "react-icons/fi"
import safetyApi from "../../api/safetyApi"
import MapView from "../../components/map/MapView"
import Loader from "../../components/common/Loader"

// How often this page re-fetches the latest position. Polling, matching
// the backend's design (see safety/views.py) -- not a WebSocket.
const POLL_INTERVAL_MS = 15000

/**
 * SharedTripView — what a TrustedContact opens from the link the trip
 * owner copied/sent them. No login needed; the unguessable token in the
 * URL is the only credential. Route this at /safety/shared/:token
 * (matches FamilySafety.jsx's copyShareLink() URL construction).
 */
const SharedTripView = () => {
  const { token } = useParams()
  const [trip, setTrip] = useState(null)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    const fetchTrip = () => {
      safetyApi
        .getSharedTrip(token)
        .then(({ data }) => {
          if (!cancelled) {
            setTrip(data)
            setError("")
          }
        })
        .catch(() => {
          if (!cancelled) setError("This trip is no longer being shared, or the link is invalid.")
        })
        .finally(() => {
          if (!cancelled) setLoading(false)
        })
    }

    fetchTrip()
    const interval = setInterval(fetchTrip, POLL_INTERVAL_MS)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [token])

  if (loading) return <Loader />

  if (error) {
    return (
      <div className="container-app py-16 text-center">
        <p className="text-gray-500">{error}</p>
      </div>
    )
  }

  const ping = trip?.latest_ping

  return (
    <div className="container-app py-10 max-w-2xl">
      <h1 className="section-title flex items-center gap-2">
        <FiMapPin className="text-himalaya-500" />
        {trip.label || "Shared Trip"}
      </h1>

      {ping ? (
        <>
          <p className="text-sm text-gray-500 mb-4 flex items-center gap-1">
            <FiClock size={14} /> Last updated: {new Date(ping.recorded_at).toLocaleTimeString()}
            <span className="inline-block h-2 w-2 rounded-full bg-forest-500 ml-2 animate-pulse" />
          </p>
          <div className="rounded-xl2 overflow-hidden shadow-premium">
            <MapView
              center={{ lat: ping.latitude, lng: ping.longitude }}
              userLocation={{ lat: ping.latitude, lng: ping.longitude }}
              height="450px"
            />
          </div>
        </>
      ) : (
        <p className="text-gray-400 text-sm">
          Sharing has started, but no location has been recorded yet — check back in a moment.
        </p>
      )}

      <p className="text-xs text-gray-400 mt-4">
        This page refreshes automatically every {POLL_INTERVAL_MS / 1000} seconds. This link was
        shared with you by the trip owner and can be revoked by them at any time.
      </p>
    </div>
  )
}

export default SharedTripView