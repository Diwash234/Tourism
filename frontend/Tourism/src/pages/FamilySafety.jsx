import { useState, useEffect, useRef } from "react"
import { motion } from "framer-motion"
import { FiShare2, FiAlertTriangle, FiCopy, FiStopCircle } from "react-icons/fi"
import safetyApi from "../api/safetyApi"
import useGeolocation from "../hooks/useGeolocation"
import useToast from "../hooks/useToast"

// How often to send a live position update while a trip is being shared.
// Polling, not push -- matches the backend's polling-based design (see
// safety/views.py's docstring for why).
const PING_INTERVAL_MS = 30000

const FamilySafety = () => {
  const { position } = useGeolocation()
  const { showToast } = useToast()
  const [activeTrip, setActiveTrip] = useState(null)
  const [label, setLabel] = useState("")
  const [sosLoading, setSosLoading] = useState(false)
  const pingIntervalRef = useRef(null)

  useEffect(() => {
    return () => clearInterval(pingIntervalRef.current)
  }, [])

  const startSharing = async () => {
    if (!position) {
      showToast("Waiting for GPS location — allow location access.", "error")
      return
    }
    try {
      const expires_at = new Date(Date.now() + 1000 * 60 * 60 * 12).toISOString() // 12h default
      const { data } = await safetyApi.startTrip({ label, expires_at })
      setActiveTrip(data)
      showToast("Live location sharing started.", "success")

      pingIntervalRef.current = setInterval(() => {
        if (position) {
          safetyApi.sendPing(data.id, { latitude: position.lat, longitude: position.lng }).catch(() => {})
        }
      }, PING_INTERVAL_MS)
    } catch (err) {
      showToast("Could not start sharing.", "error")
    }
  }

  const stopSharing = async () => {
    if (!activeTrip) return
    await safetyApi.endTrip(activeTrip.id)
    clearInterval(pingIntervalRef.current)
    setActiveTrip(null)
    showToast("Location sharing stopped.", "success")
  }

  const copyShareLink = () => {
    const url = `${window.location.origin}/safety/shared/${activeTrip.share_token}`
    navigator.clipboard.writeText(url)
    showToast("Share link copied.", "success")
  }

  const triggerSos = async () => {
    if (!window.confirm("Trigger an SOS alert? This notifies all your trusted contacts immediately.")) return
    setSosLoading(true)
    try {
      await safetyApi.triggerSos({
        latitude: position?.lat,
        longitude: position?.lng,
        trip: activeTrip?.id,
        message: "SOS triggered from the app.",
      })
      showToast("SOS sent — your trusted contacts have been notified.", "success")
    } catch {
      showToast("Could not send SOS. Try calling emergency services directly.", "error")
    } finally {
      setSosLoading(false)
    }
  }

  return (
    <div className="container-app py-10 max-w-2xl">
      <h1 className="section-title flex items-center gap-2">
        <FiShare2 className="text-himalaya-500" /> Family Safety
      </h1>
      <p className="text-gray-500 text-sm mb-6">
        Share your live location with trusted contacts during a trip, or trigger an SOS if
        something goes wrong.
      </p>

      {/* SOS -- always visible, always available regardless of trip sharing state */}
      <button
        onClick={triggerSos}
        disabled={sosLoading}
        className="w-full bg-nepalred-500 hover:bg-nepalred-600 text-white font-bold py-4 rounded-xl2 flex items-center justify-center gap-2 mb-8 shadow-lg transition-colors"
      >
        <FiAlertTriangle size={20} />
        {sosLoading ? "Sending..." : "Send SOS Alert"}
      </button>

      <div className="card-base p-5">
        {!activeTrip ? (
          <>
            <label className="text-xs font-medium text-gray-500">Trip label (optional)</label>
            <input
              className="input-field mt-1 mb-3"
              placeholder="e.g. Annapurna trek, Day 3"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
            />
            <button onClick={startSharing} className="btn-primary w-full">
              Start Sharing Live Location
            </button>
            <p className="text-xs text-gray-400 mt-2">
              Shares for 12 hours by default, or until you stop it manually. Only your saved
              trusted contacts can view it.
            </p>
          </>
        ) : (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
            <p className="text-sm">
              <span className="inline-block h-2 w-2 rounded-full bg-forest-500 mr-2 animate-pulse" />
              Sharing live location{activeTrip.label ? ` — ${activeTrip.label}` : ""}
            </p>
            <button
              onClick={copyShareLink}
              className="w-full flex items-center justify-center gap-2 border border-gray-200 rounded-xl py-2.5 text-sm font-medium hover:bg-gray-50"
            >
              <FiCopy size={14} /> Copy Share Link
            </button>
            <button
              onClick={stopSharing}
              className="w-full flex items-center justify-center gap-2 text-nepalred-500 border border-nepalred-100 rounded-xl py-2.5 text-sm font-medium hover:bg-nepalred-50"
            >
              <FiStopCircle size={14} /> Stop Sharing
            </button>
          </motion.div>
        )}
      </div>
    </div>
  )
}

export default FamilySafety