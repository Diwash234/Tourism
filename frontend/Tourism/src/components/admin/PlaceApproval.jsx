import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { FiCheck, FiX, FiMapPin, FiUser, FiImage, FiZoomIn } from "react-icons/fi"
import adminPanelApi from "../../api/adminPanelApi"
import Loader from "../../components/common/Loader"
import EmptyState from "../../components/common/EmptyState"
import useToast from "../../hooks/useToast"

/**
 * PlaceApprovals — real, working feature. Confirmed by reading
 * tourist/views.py directly: DestinationViewSet.approve() is a genuine
 * admin-only endpoint (POST /destinations/{slug}/approve/) that writes
 * an audit log and emails the submitter. Staff accounts see ALL
 * destinations (including pending) via the normal list endpoint's own
 * get_queryset() — there's no server-side ?status=pending filter yet
 * (see BACKEND_IMPROVEMENTS.md), so pending items are filtered here.
 *
 * ADDED: full-size clickable image preview before approving/rejecting
 * -- was a small 128x96 thumbnail with no way to actually inspect the
 * photo before making a moderation decision. Also fixed a real bug
 * server-side (serializers.py) so this reliably shows exactly what
 * the tourist submitted, never an auto-fetched stock photo standing
 * in for it (that auto-fetch is now gated to approved destinations
 * only, so an unreviewed pending submission never gets one).
 */
const PlaceApprovals = () => {
  const [destinations, setDestinations] = useState([])
  const [loading, setLoading] = useState(true)
  const [reviewNotes, setReviewNotes] = useState({}) // { [slug]: note }
  const [actingOn, setActingOn] = useState(null)
  const [lightboxUrl, setLightboxUrl] = useState(null)
  const { showToast } = useToast()

  const load = () => {
    setLoading(true)
    adminPanelApi
      .getPendingDestinations()
      .then(({ data }) => {
        const list = data.results || data || []
        setDestinations(list.filter((d) => d.status === "pending"))
      })
      .catch(() => showToast("Could not load pending places — you may not have admin access.", "error"))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const handleDecision = async (slug, decision) => {
    setActingOn(slug)
    try {
      await adminPanelApi.approveDestination(slug, decision, reviewNotes[slug] || "")
      setDestinations((prev) => prev.filter((d) => d.slug !== slug))
      showToast(decision === "approved" ? "Place approved" : "Place rejected", "success")
    } catch (err) {
      showToast(err.response?.data?.detail || "Action failed", "error")
    } finally {
      setActingOn(null)
    }
  }

  if (loading) return <Loader />

  return (
    <div className="container-app py-10 fade-in">
      <h1 className="section-title">Place Approvals</h1>
      <p className="text-gray-500 text-sm mb-6">
        Review tourist-submitted places before they go live. Approving or rejecting notifies the submitter automatically.
      </p>

      {destinations.length ? (
        <AnimatePresence>
          <div className="space-y-4">
            {destinations.map((d) => (
              <motion.div
                key={d.slug}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="card-base p-5"
              >
                <div className="flex flex-col sm:flex-row gap-4 justify-between">
                  <div className="min-w-0 flex-1">
                    <h3 className="font-bold text-lg flex items-center gap-2">
                      <FiMapPin className="text-himalaya-500 shrink-0" /> {d.name}
                    </h3>
                    <p className="text-sm text-gray-500 mt-1">{d.short_description || d.description}</p>
                    <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-gray-400">
                      <span className="flex items-center gap-1"><FiUser size={12} /> {d.city}, {d.country}</span>
                      {d.category_name && <span className="badge-risk-moderate">{d.category_name}</span>}
                    </div>
                  </div>

                  {/* ADDED: proper-sized, clickable preview instead of a
                      tiny 128x96 thumbnail -- an admin needs to actually
                      see the submitted photo clearly before approving
                      or rejecting it, not squint at a postage stamp. */}
                  {d.cover_image_url ? (
                    <button
                      type="button"
                      onClick={() => setLightboxUrl(d.cover_image_url)}
                      className="relative w-full sm:w-48 h-36 shrink-0 rounded-xl overflow-hidden group"
                    >
                      <img src={d.cover_image_url} alt={d.name} className="w-full h-full object-cover" />
                      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors flex items-center justify-center">
                        <FiZoomIn className="text-white opacity-0 group-hover:opacity-100 transition-opacity" size={22} />
                      </div>
                    </button>
                  ) : (
                    <div className="w-full sm:w-48 h-36 shrink-0 rounded-xl bg-gray-50 border border-dashed border-gray-200 flex flex-col items-center justify-center text-gray-400 gap-1">
                      <FiImage size={20} />
                      <span className="text-xs">No photo submitted</span>
                    </div>
                  )}
                </div>

                <input
                  placeholder="Review note (optional, sent to submitter)"
                  className="input-field mt-3 text-sm"
                  value={reviewNotes[d.slug] || ""}
                  onChange={(e) => setReviewNotes((prev) => ({ ...prev, [d.slug]: e.target.value }))}
                />

                <div className="flex gap-3 mt-3">
                  <button
                    onClick={() => handleDecision(d.slug, "approved")}
                    disabled={actingOn === d.slug}
                    className="flex-1 flex items-center justify-center gap-2 bg-forest-500 hover:bg-forest-600 text-white font-semibold py-2 rounded-xl transition-colors disabled:opacity-50"
                  >
                    <FiCheck /> Approve
                  </button>
                  <button
                    onClick={() => handleDecision(d.slug, "rejected")}
                    disabled={actingOn === d.slug}
                    className="flex-1 flex items-center justify-center gap-2 bg-nepalred-500 hover:bg-nepalred-600 text-white font-semibold py-2 rounded-xl transition-colors disabled:opacity-50"
                  >
                    <FiX /> Reject
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        </AnimatePresence>
      ) : (
        <EmptyState title="Nothing pending" subtitle="All caught up — no submissions waiting for review." />
      )}

      {/* ADDED: full-size lightbox for inspecting a submitted photo
          before making a decision. */}
      <AnimatePresence>
        {lightboxUrl && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setLightboxUrl(null)}
            className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-6 cursor-zoom-out"
          >
            <img
              src={lightboxUrl}
              alt="Full preview"
              className="max-w-full max-h-full rounded-lg object-contain"
              onClick={(e) => e.stopPropagation()}
            />
            <button
              onClick={() => setLightboxUrl(null)}
              className="absolute top-5 right-5 text-white bg-black/40 rounded-full p-2 hover:bg-black/60"
            >
              <FiX size={20} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default PlaceApprovals