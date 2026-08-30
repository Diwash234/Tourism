import { useState, useEffect, useRef, useCallback } from "react"
import { motion } from "framer-motion"
import {
  FiShare2, FiAlertTriangle, FiCopy, FiStopCircle, FiUserPlus,
  FiUsers, FiMapPin, FiClock, FiShield, FiCheck, FiX, FiLink2,
} from "react-icons/fi"
import safetyApi, { familyApi } from "../api/safetyApi"
import useGeolocation from "../hooks/useGeolocation"
import useToast from "../hooks/useToast"
import { useI18n } from "../i18n"

// How often to send a live position update while a trip is being shared.
const PING_INTERVAL_MS = 30000
// How often to refresh the family members' live status.
const MEMBER_POLL_MS = 30000

const FamilySafety = () => {
  const { position } = useGeolocation()
  const { showToast } = useToast()
  const { t } = useI18n()
  const [activeTrip, setActiveTrip] = useState(null)
  const [label, setLabel] = useState("")
  const [sosLoading, setSosLoading] = useState(false)

  // family linking
  const [links, setLinks] = useState([])
  const [members, setMembers] = useState([])
  const [linkEmail, setLinkEmail] = useState("")
  const [linkRelation, setLinkRelation] = useState("")
  const [linking, setLinking] = useState(false)
  const [loadingLinks, setLoadingLinks] = useState(true)

  const pingIntervalRef = useRef(null)

  const loadLinks = useCallback(async () => {
    try {
      const { data } = await familyApi.getLinks()
      setLinks(Array.isArray(data) ? data : data.results || [])
    } catch {
      /* not logged in or offline */
    } finally {
      setLoadingLinks(false)
    }
  }, [])

  const loadMembers = useCallback(async () => {
    try {
      const { data } = await familyApi.getFamilyMembers()
      setMembers(Array.isArray(data) ? data : data.results || [])
    } catch {
      /* ignore */
    }
  }, [])

  useEffect(() => {
    loadLinks()
    loadMembers()
    const timer = setInterval(loadMembers, MEMBER_POLL_MS)
    return () => {
      clearInterval(timer)
      clearInterval(pingIntervalRef.current)
    }
  }, [loadLinks, loadMembers])

  const startSharing = async () => {
    if (!position) {
      showToast("Waiting for GPS location — allow location access.", "error")
      return
    }
    try {
      const expires_at = new Date(Date.now() + 1000 * 60 * 60 * 12).toISOString() // 12h default
      const { data } = await safetyApi.startTrip({ label, expires_at })
      setActiveTrip(data)
      showToast("Live location sharing started — your family is notified.", "success")
      // notify family members immediately with the first ping
      safetyApi.sendPing(data.id, { latitude: position.lat, longitude: position.lng }).catch(() => {})

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
    if (!window.confirm("Trigger an SOS alert? Your trusted contacts AND linked family members are notified immediately.")) return
    setSosLoading(true)
    try {
      await safetyApi.triggerSos({
        latitude: position?.lat,
        longitude: position?.lng,
        trip: activeTrip?.id,
        message: "SOS triggered from the app.",
      })
      showToast("SOS sent — trusted contacts & family have been notified.", "success")
    } catch {
      showToast("Could not send SOS. Try calling emergency services directly.", "error")
    } finally {
      setSosLoading(false)
    }
  }

  const sendLinkRequest = async (e) => {
    e.preventDefault()
    if (!linkEmail.trim()) {
      showToast("Enter the family member's email or username.", "error")
      return
    }
    setLinking(true)
    try {
      await familyApi.sendLinkRequest({
        username_or_email: linkEmail.trim(),
        relationship: linkRelation.trim(),
      })
      setLinkEmail("")
      setLinkRelation("")
      showToast("Family link request sent — they will get a notification.", "success")
      loadLinks()
    } catch (err) {
      const detail = err?.response?.data?.detail
      showToast(detail ? String(detail) : "Could not send request.", "error")
    } finally {
      setLinking(false)
    }
  }

  const acceptLink = async (id) => {
    try {
      await familyApi.acceptLink(id)
      showToast("Family link accepted!", "success")
      loadLinks()
      loadMembers()
    } catch {
      showToast("Could not accept.", "error")
    }
  }

  const declineLink = async (id) => {
    try {
      await familyApi.declineLink(id)
      loadLinks()
    } catch {
      /* ignore */
    }
  }

  const removeLink = async (id) => {
    if (!window.confirm("Remove this family link?")) return
    try {
      await familyApi.removeLink(id)
      loadLinks()
      loadMembers()
    } catch {
      /* ignore */
    }
  }

  const received = links.filter((l) => l.direction === "received")
  const sent = links.filter((l) => l.direction === "sent")
  const pendingReceived = received.filter((l) => l.status === "pending")
  const accepted = links.filter((l) => l.status === "accepted")

  const timeAgo = (iso) => {
    if (!iso) return "—"
    const s = (Date.now() - new Date(iso).getTime()) / 1000
    if (s < 60) return `${Math.max(0, Math.floor(s))}s ago`
    if (s < 3600) return `${Math.floor(s / 60)}m ago`
    return `${Math.floor(s / 3600)}h ago`
  }

  return (
    <div className="container-app py-10 max-w-5xl theme-amber-alt">
      <h1 className="section-title flex items-center gap-2">
        <FiUsers className="text-forest-500" /> {t("family.title")}
      </h1>
      <p className="text-gray-500 text-sm mb-6">
        Link your family members' accounts — they see your live location, trip history, and get
        notified instantly if you trigger an SOS. And you see theirs.
      </p>

      {/* SOS -- always visible */}
      <button
        onClick={triggerSos}
        disabled={sosLoading}
        className="w-full bg-nepalred-500 hover:bg-nepalred-600 text-white font-bold py-4 rounded-xl2 flex items-center justify-center gap-2 mb-8 shadow-lg transition-colors"
      >
        <FiAlertTriangle size={20} />
        {sosLoading ? "Sending..." : `${t("family.trigger_sos")} 🚨`}
      </button>

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        {/* --- Live sharing card (kept from before) --- */}
        <div className="card-base p-5">
          <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
            <FiMapPin className="text-forest-500" /> {t("family.live_location")}
          </h3>
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
                {t("family.start_sharing")}
              </button>
              <p className="text-xs text-gray-400 mt-2">
                Shares for 12 hours. Your linked family members and trusted contacts can view it.
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
                <FiStopCircle size={14} /> {t("family.stop_sharing")}
              </button>
            </motion.div>
          )}
        </div>

        {/* --- Link a family member --- */}
        <div className="card-base p-5">
          <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
            <FiUserPlus className="text-forest-500" /> {t("family.link_member")}
          </h3>
          <form onSubmit={sendLinkRequest} className="space-y-2">
            <input
              className="input-field"
              placeholder="Email or username of the family member"
              value={linkEmail}
              onChange={(e) => setLinkEmail(e.target.value)}
            />
            <input
              className="input-field"
              placeholder="Relationship (e.g. Parent, Spouse, Sibling)"
              value={linkRelation}
              onChange={(e) => setLinkRelation(e.target.value)}
            />
            <button type="submit" disabled={linking} className="btn-primary w-full">
              <FiLink2 size={14} /> {linking ? "Sending..." : "Send Family Link Request"}
            </button>
          </form>

          {pendingReceived.length > 0 && (
            <div className="mt-4 border-t border-gray-100 pt-3 space-y-2">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                {pendingReceived.length} pending request{pendingReceived.length > 1 ? "s" : ""}
              </p>
              {pendingReceived.map((l) => (
                <div key={l.id} className="flex items-center justify-between gap-2 bg-amber-50 rounded-xl px-3 py-2">
                  <div className="min-w-0">
                    <p className="text-sm font-medium truncate">{l.requester_name}</p>
                    <p className="text-[11px] text-gray-500 truncate">{l.relationship || "wants to link as family"}</p>
                  </div>
                  <div className="flex gap-1.5 shrink-0">
                    <button
                      onClick={() => acceptLink(l.id)}
                      className="flex items-center gap-1 text-xs bg-forest-600 hover:bg-forest-700 text-white rounded-lg px-2.5 py-1.5"
                    >
                      <FiCheck size={12} /> {t("family.accept")}
                    </button>
                    <button
                      onClick={() => declineLink(l.id)}
                      className="flex items-center gap-1 text-xs border border-gray-200 rounded-lg px-2.5 py-1.5 hover:bg-gray-50"
                    >
                      <FiX size={12} /> {t("family.decline")}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* --- My Family: live status --- */}
      <h3 className="font-semibold text-base mb-3 flex items-center gap-2">
        <FiShield className="text-forest-500" /> {t("family.my_family")}
        <span className="text-xs font-normal text-gray-400">({accepted.length})</span>
      </h3>

      {accepted.length === 0 && (
        <div className="card-base p-8 text-center text-gray-400 text-sm">
          {t("family.no_members")} — use the form above to send your first link request.
        </div>
      )}

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {accepted.map((l) => {
          const m = members.find((x) => x.link_id === l.id)
          const live = m?.is_live
          return (
            <div key={l.id} className={`card-base p-4 relative ${live ? "ring-2 ring-forest-400" : ""}`}>
              {live && (
                <span className="absolute top-3 right-3 flex items-center gap-1 text-[10px] font-bold text-forest-700 bg-forest-50 rounded-full px-2 py-0.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-forest-500 animate-pulse" /> LIVE
                </span>
              )}
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-forest-500 to-forest-700 text-white flex items-center justify-center font-bold text-sm">
                  {(l.member_name || "?").charAt(0).toUpperCase()}
                </div>
                <div className="min-w-0">
                  <p className="font-semibold text-sm truncate">{l.member_name}</p>
                  <p className="text-[11px] text-gray-400 truncate">{l.relationship || "Family"}</p>
                </div>
              </div>

              {live && m?.live_trip ? (
                <div className="bg-forest-50 rounded-xl p-3 text-xs space-y-1.5">
                  <p className="font-medium text-forest-800 flex items-center gap-1.5">
                    <FiMapPin size={12} /> {m.live_trip.label || "Live trip"}
                  </p>
                  {m.latest_ping && (
                    <p className="text-gray-600 font-mono">
                      {Number(m.latest_ping.latitude).toFixed(5)}, {Number(m.latest_ping.longitude).toFixed(5)}
                      <span className="text-gray-400 ml-1">({timeAgo(m.latest_ping.recorded_at)})</span>
                    </p>
                  )}
                </div>
              ) : (
                <p className="text-xs text-gray-400 flex items-center gap-1.5">
                  <FiClock size={12} /> Not sharing location right now
                </p>
              )}

              {m?.active_sos?.length > 0 && (
                <p className="mt-2 text-[11px] font-bold text-nepalred-600 bg-nepalred-50 rounded-lg px-2 py-1.5">
                  🚨 ACTIVE SOS — {m.active_sos.length} alert{m.active_sos.length > 1 ? "s" : ""}!
                </p>
              )}

              <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between">
                <span className="text-[11px] text-gray-400">
                  {m?.history?.length || 0} trip{(m?.history?.length || 0) === 1 ? "" : "s"} · {t("family.trip_history")}
                </span>
                <button
                  onClick={() => removeLink(l.id)}
                  className="text-[11px] text-nepalred-500 hover:underline"
                >
                  Unlink
                </button>
              </div>
            </div>
          )
        })}
      </div>

      {/* --- Sent requests --- */}
      {sent.filter((l) => l.status === "pending").length > 0 && (
        <div className="card-base p-4 mb-4">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            Sent requests waiting for acceptance
          </p>
          {sent.filter((l) => l.status === "pending").map((l) => (
            <div key={l.id} className="flex items-center justify-between py-1.5 text-sm">
              <span>{l.member_name} {l.relationship ? `(${l.relationship})` : ""}</span>
              <span className="text-xs text-amber-600 bg-amber-50 rounded-full px-2.5 py-1">
                {t("family.pending")}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default FamilySafety
