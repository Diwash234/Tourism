import { useState, useEffect, useCallback, useRef } from "react"
import { FiShare2, FiUsers, FiMail, FiUserPlus, FiCopy, FiCheck, FiRefreshCw, FiTrash2, FiLink } from "react-icons/fi"
import axiosClient from "../api/axiosClient"
import useToast from "../hooks/useToast"

const POLL_INTERVAL = 10 * 1000 // 10 seconds

/**
 * Trip collaboration component for sharing trips, managing collaborators,
 * and real-time updates via polling.
 */
const TripCollaboration = ({ tripId, shareToken: initialShareToken }) => {
  const showToast = useToast()
  const [collaborators, setCollaborators] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [shareToken, setShareToken] = useState(initialShareToken || null)
  const [inviteEmail, setInviteEmail] = useState("")
  const [inviting, setInviting] = useState(false)
  const [copied, setCopied] = useState(false)
  const [removing, setRemoving] = useState(null)
  const intervalRef = useRef(null)

  const fetchCollaborators = useCallback(async () => {
    try {
      const { data } = await axiosClient.get(`/trips/${tripId}/collaborators/`)
      setCollaborators(data?.results || data || [])
      setError(null)
    } catch (err) {
      setError(
        err?.response?.data?.message || "Unable to load collaborators. Please try again later."
      )
    } finally {
      setLoading(false)
    }
  }, [tripId])

  useEffect(() => {
    if (!tripId) return undefined
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => fetchCollaborators(), 0)
    intervalRef.current = setInterval(fetchCollaborators, POLL_INTERVAL)
    return () => {
      clearTimeout(t)
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [tripId, fetchCollaborators])

  const generateShareLink = async () => {
    try {
      const { data } = await axiosClient.post(`/trips/${tripId}/generate-share-link/`)
      setShareToken(data?.share_token || data?.token)
      showToast("Share link generated successfully.", "success")
    } catch (err) {
      showToast(
        err?.response?.data?.message || "Failed to generate share link.",
        "error"
      )
    }
  }

  const copyShareLink = () => {
    if (!shareToken) return
    const url = `${window.location.origin}/plans/shared/${shareToken}`
    navigator.clipboard.writeText(url).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
      showToast("Share link copied to clipboard.", "success")
    })
  }

  const inviteCollaborator = async (e) => {
    e.preventDefault()
    if (!inviteEmail.trim()) return
    setInviting(true)
    try {
      await axiosClient.post(`/trips/${tripId}/collaborators/`, {
        email: inviteEmail.trim(),
      })
      setInviteEmail("")
      showToast(`Invitation sent to ${inviteEmail.trim()}.`, "success")
      fetchCollaborators()
    } catch (err) {
      showToast(
        err?.response?.data?.message || "Failed to send invitation.",
        "error"
      )
    } finally {
      setInviting(false)
    }
  }

  const removeCollaborator = async (collabId) => {
    if (!window.confirm("Remove this collaborator?")) return
    setRemoving(collabId)
    try {
      await axiosClient.delete(`/trips/${tripId}/collaborators/${collabId}/`)
      setCollaborators((prev) => prev.filter((c) => c.id !== collabId))
      showToast("Collaborator removed.", "success")
    } catch (err) {
      showToast(
        err?.response?.data?.message || "Failed to remove collaborator.",
        "error"
      )
    } finally {
      setRemoving(null)
    }
  }

  if (!tripId) {
    return (
      <div className="ny-card p-5">
        <p className="text-sm text-ny-text-muted">No trip selected for collaboration.</p>
      </div>
    )
  }

  return (
    <div className="ny-card p-5">
      <h3 className="text-lg font-bold text-ny-text flex items-center gap-2 mb-1">
        <FiUsers size={18} className="text-ny-green" />
        Trip Collaboration
      </h3>
      <p className="text-sm text-ny-text-secondary mb-4">
        Share your trip and plan together in real time.
      </p>

      {/* Share link section */}
      <div className="p-4 rounded-xl bg-ny-soft-green/50 border border-ny-border mb-4">
        <div className="flex items-center gap-2 mb-2">
          <FiShare2 size={14} className="text-ny-green" />
          <span className="text-sm font-semibold text-ny-text">Share this trip</span>
        </div>
        {shareToken ? (
          <div className="flex items-center gap-2">
            <div className="flex-1 flex items-center gap-2 px-3 py-2 rounded-lg bg-white border border-ny-border text-sm text-ny-text-secondary truncate">
              <FiLink size={12} className="flex-shrink-0" />
              <span className="truncate">/plans/shared/{shareToken}</span>
            </div>
            <button
              onClick={copyShareLink}
              className="ny-btn ny-btn-primary ny-btn-sm flex-shrink-0"
              type="button"
            >
              {copied ? <FiCheck size={14} /> : <FiCopy size={14} />}
              {copied ? "Copied" : "Copy"}
            </button>
          </div>
        ) : (
          <button
            onClick={generateShareLink}
            className="ny-btn ny-btn-secondary ny-btn-sm"
            type="button"
          >
            <FiShare2 size={14} /> Generate share link
          </button>
        )}
      </div>

      {/* Invite by email */}
      <form onSubmit={inviteCollaborator} className="flex items-center gap-2 mb-4">
        <div className="relative flex-1">
          <FiMail size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-ny-text-muted" />
          <input
            type="email"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            placeholder="Invite by email..."
            className="input-field pl-9 py-2 text-sm"
            aria-label="Invite collaborator by email"
          />
        </div>
        <button
          type="submit"
          disabled={inviting || !inviteEmail.trim()}
          className="ny-btn ny-btn-primary ny-btn-sm flex-shrink-0"
        >
          <FiUserPlus size={14} /> {inviting ? "Sending..." : "Invite"}
        </button>
      </form>

      {/* Collaborators list */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold text-ny-text">
          Collaborators ({collaborators.length})
        </span>
        <button
          onClick={fetchCollaborators}
          className="ny-btn ny-btn-ghost ny-btn-sm"
          type="button"
          aria-label="Refresh collaborators"
        >
          <FiRefreshCw size={12} />
        </button>
      </div>

      {loading ? (
        <div className="space-y-2" role="status" aria-label="Loading collaborators">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 p-2">
              <div className="ny-skeleton h-8 w-8 rounded-full" />
              <div className="flex-1">
                <div className="ny-skeleton h-4 w-1/3" />
              </div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="text-sm text-ny-danger">{error}</div>
      ) : collaborators.length === 0 ? (
        <div className="ny-empty py-6">
          <span className="ny-empty-icon"><FiUsers size={24} /></span>
          <h3>No collaborators yet</h3>
          <p>Invite someone to start planning together.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {collaborators.map((collab) => (
            <div
              key={collab.id}
              className="flex items-center gap-3 p-2 rounded-lg hover:bg-ny-soft-green/50 transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-ny-green flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                {collab.name?.charAt(0)?.toUpperCase() || collab.email?.charAt(0)?.toUpperCase() || "?"}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-ny-text truncate">
                  {collab.name || collab.email}
                </p>
                <p className="text-xs text-ny-text-muted truncate">{collab.email}</p>
              </div>
              <span className="text-xs text-ny-text-muted capitalize">{collab.role || "viewer"}</span>
              <button
                onClick={() => removeCollaborator(collab.id)}
                disabled={removing === collab.id}
                className="text-ny-text-muted hover:text-ny-danger transition-colors"
                aria-label={`Remove ${collab.name || collab.email}`}
              >
                <FiTrash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default TripCollaboration
