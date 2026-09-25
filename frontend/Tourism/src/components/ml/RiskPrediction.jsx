import { useState } from "react"
import { Link } from "react-router-dom"
import { FiAlertCircle, FiShield } from "react-icons/fi"

/**
 * Optional trip-context form. A risk score is intentionally not calculated
 * here: this component has no live hazard feed or authoritative dataset.
 * Callers should pass real risk data from the safety API when available.
 */
export default function RiskPrediction({ placeName = "" }) {
  const [altitude, setAltitude] = useState("")
  const [season, setSeason] = useState("")

  return (
    <section className="ny-card space-y-4 p-5" aria-labelledby="trip-context-title">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-[var(--ny-radius-md)] bg-[var(--ny-soft-gold)] text-[var(--ny-warning)]"><FiShield size={20} aria-hidden="true" /></span>
        <div><h2 id="trip-context-title" className="text-lg font-bold">Trip context</h2><p className="text-sm text-[var(--ny-text-secondary)]">Record the conditions you want to check for {placeName || "your destination"}. No score is shown without a live safety feed.</p></div>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <div><label className="text-sm font-semibold" htmlFor="trip-altitude">Planned altitude (m)</label><input id="trip-altitude" type="number" className="input-field mt-1" value={altitude} onChange={(event) => setAltitude(event.target.value)} placeholder="Not recorded" /></div>
        <div><label className="text-sm font-semibold" htmlFor="trip-season">Season</label><select id="trip-season" className="input-field mt-1" value={season} onChange={(event) => setSeason(event.target.value)}><option value="">Not recorded</option><option value="spring">Spring</option><option value="summer">Summer</option><option value="monsoon">Monsoon</option><option value="autumn">Autumn</option><option value="winter">Winter</option></select></div>
      </div>
      <div className="flex items-start gap-2 rounded-[var(--ny-radius-md)] border border-[var(--ny-border)] bg-[var(--ny-soft-gold)] p-3 text-sm text-[var(--ny-text-secondary)]"><FiAlertCircle size={17} className="mt-0.5 shrink-0 text-[var(--ny-warning)]" aria-hidden="true" /><span>Conditions can change quickly. Confirm route, weather and emergency information with current local sources before travelling.</span></div>
      <Link to="/emergency" className="ny-btn ny-btn-secondary">Open emergency information</Link>
    </section>
  )
}
