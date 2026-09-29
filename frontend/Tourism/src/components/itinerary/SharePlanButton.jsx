import { useState } from "react"
import { FiShare2, FiCopy, FiLink2, FiXCircle } from "react-icons/fi"
import exploreApi from "../../api/exploreApi"

// Owner-only share control for a saved travel plan. Creating a link makes a
// read-only public copy (no name, email or private notes); "Stop sharing"
// revokes the token so the old link stops working immediately.

const absolute = (path) => `${window.location.origin}${path}`

export default function SharePlanButton({ planId, initialToken = null, compact = false, onChange }) {
  const [token, setToken] = useState(initialToken)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState("")
  const link = token ? absolute(`/plans/shared/${token}`) : ""

  const copy = async (url) => {
    try {
      await navigator.clipboard.writeText(url)
      setMessage("Link copied.")
    } catch {
      setMessage("Copy the link below.")
    }
  }

  const share = async () => {
    setBusy(true); setMessage("")
    try {
      const { data } = await exploreApi.sharePlan(planId)
      setToken(data.token)
      onChange?.(data.token)
      await copy(absolute(data.path))
    } catch (err) {
      setMessage(err?.response?.status === 401 ? "Sign in to share this plan." : "Could not create a share link.")
    } finally { setBusy(false) }
  }

  const stop = async () => {
    setBusy(true); setMessage("")
    try {
      await exploreApi.unsharePlan(planId)
      setToken(null)
      onChange?.(null)
      setMessage("Sharing stopped. The old link no longer works.")
    } catch {
      setMessage("Could not stop sharing.")
    } finally { setBusy(false) }
  }

  return (
    <div className="space-y-2">
      {!token ? (
        <button type="button" onClick={share} disabled={busy}
          className={`inline-flex items-center gap-2 rounded-lg border border-emerald-300 bg-white font-semibold text-emerald-800 hover:bg-emerald-50 ${compact ? "px-2.5 py-1 text-xs" : "px-3 py-2 text-sm"}`}>
          <FiShare2 aria-hidden="true" /> {busy ? "Creating link…" : "Share"}
        </button>
      ) : (
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-800"><FiLink2 aria-hidden="true" /> Shared</span>
          <button type="button" onClick={() => copy(link)} className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-800 underline"><FiCopy aria-hidden="true" /> Copy link</button>
          <button type="button" onClick={stop} disabled={busy} className="inline-flex items-center gap-1 text-xs font-semibold text-rose-700 underline"><FiXCircle aria-hidden="true" /> Stop sharing</button>
        </div>
      )}
      {token && !compact && (
        <input readOnly value={link} aria-label="Share link" onFocus={(e) => e.currentTarget.select()}
          className="input-field w-full py-1.5 text-xs" />
      )}
      {message && <p role="status" className="text-xs text-[var(--ny-text-secondary)]">{message}</p>}
    </div>
  )
}
