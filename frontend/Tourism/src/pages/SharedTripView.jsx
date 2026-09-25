import { useState, useEffect } from "react"
import PageHeader from "../components/common/PageHeader"
import { useParams } from "react-router-dom"
import { FiMapPin, FiClock } from "react-icons/fi"
import safetyApi from "../api/safetyApi"
import MapView from "../components/map/MapView"
import Loader from "../components/common/Loader"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import EmptyState from "../components/common/EmptyState"

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
      <div className="ny-page container-app section-space">
        <EmptyState title="Shared trip unavailable" subtitle={error} />
      </div>
    )
  }

  if (!trip) return <div className="ny-page container-app section-space"><EmptyState title="Shared trip unavailable" subtitle="The shared trip record is empty or has expired." /></div>

  const ping = trip?.latest_ping

  return (
    <div className="ny-page container-app max-w-4xl space-y-6 py-6 sm:py-8">
      <CMSPageIntro pageKey="shared-trip" />
      <PageHeader title={<>{trip.label || "Shared Trip"}</>} icon={ FiMapPin } />

      {ping ? (
        <>
          <p className="text-sm text-gray-500 mb-4 flex items-center gap-1">
            <FiClock size={14} /> Last updated: {new Date(ping.recorded_at).toLocaleTimeString()}
            <span className="inline-block h-2 w-2 rounded-full bg-forest-500 ml-2 opacity-70" />
          </p>
          <div className="overflow-hidden rounded-[var(--ny-radius-lg)] shadow-[var(--ny-shadow-elevated)]">
            <MapView
              center={{ lat: ping.latitude, lng: ping.longitude }}
              userLocation={{ lat: ping.latitude, lng: ping.longitude }}
              height="450px"
               userLocationLabel="Trip owner's latest recorded position"
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