import { useEffect, useState } from "react"
import {
  FiActivity, FiAlertTriangle, FiBarChart2, FiCheckCircle, FiClock,
  FiInfo, FiMapPin, FiShield, FiZap,
} from "react-icons/fi"
import riskApi from "../../api/riskApi"

/**
 * PlaceHistoryPanel — the safety HISTORY of one destination.
 *
 * The destination page previously showed three numbers from the embedded
 * risk_analysis row (index, category, label). This renders the full risk
 * assessment instead, which is the part that actually carries evidence:
 * per-hazard recorded counts, the provenance of the baseline they came from,
 * live advisories, verified news and altitude/route warnings.
 *
 * Honesty rules this panel follows:
 *  - The overall level is a MODEL INDICATOR built from historical counts. It is
 *    never presented as an official warning, and the API says so explicitly.
 *  - "No active advisory" means nothing is recorded right now. It does NOT mean
 *    the place is safe, so it is never rendered as a green "all clear".
 *  - Every historical count is attributed to the baseline row it came from,
 *    including the case where that is a different place in the same district.
 */

const LEVEL_STYLE = {
  low: "bg-emerald-50 text-emerald-800 border-emerald-200",
  moderate: "bg-amber-50 text-amber-800 border-amber-200",
  high: "bg-orange-50 text-orange-800 border-orange-200",
  critical: "bg-red-50 text-red-800 border-red-200",
}

const MAX_BAR = 20 // counts above this render as a full bar

function LevelBadge({ level }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-bold uppercase ${
        LEVEL_STYLE[level] || "border-slate-200 bg-slate-50 text-slate-600"
      }`}
    >
      {level || "Unavailable"}
    </span>
  )
}

function Row({ label, value, hint }) {
  return (
    <div className="flex items-baseline justify-between gap-3 py-1">
      <span className="text-sm text-[var(--ny-text-secondary)]">{label}</span>
      <span className="text-sm font-bold text-[var(--ny-text)]">
        {value}
        {hint ? <span className="ml-1 text-xs font-normal text-[var(--ny-text-muted)]">{hint}</span> : null}
      </span>
    </div>
  )
}

function HistoryBars({ breakdown }) {
  if (!Array.isArray(breakdown) || !breakdown.length) return null
  return (
    <ul className="mt-3 space-y-2.5">
      {breakdown.map((item) => {
        const pct = Math.min(100, Math.round((Number(item.incident_count || 0) / MAX_BAR) * 100))
        return (
          <li key={item.hazard_type}>
            <div className="flex items-baseline justify-between gap-2 text-sm">
              <span className="font-semibold text-[var(--ny-text)]">{item.label || item.hazard_type}</span>
              <span className="text-[var(--ny-text-muted)]">
                {item.incident_count} recorded
                {Number(item.seasonal_factor) > 1 ? " · in season now" : ""}
              </span>
            </div>
            <div
              className="mt-1 h-2 w-full overflow-hidden rounded-full bg-[var(--ny-soft-green)]"
              role="img"
              aria-label={`${item.label || item.hazard_type}: ${item.incident_count} recorded`}
            >
              <div className="h-full rounded-full bg-[var(--ny-green)]" style={{ width: `${pct}%` }} />
            </div>
          </li>
        )
      })}
    </ul>
  )
}

export default function PlaceHistoryPanel({ destinationRef, className = "" }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!destinationRef) return undefined
    let alive = true
    setLoading(true)
    setError("")
    riskApi
      .assessDestination(destinationRef)
      .then(({ data: payload }) => { if (alive) setData(payload) })
      .catch(() => { if (alive) setError("The safety history for this place could not be loaded.") })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [destinationRef])

  if (loading) {
    return (
      <section className={`card-base rounded-[var(--ny-radius-lg)] border border-[var(--ny-border)] bg-[var(--ny-white)] p-5 ${className}`} aria-busy="true">
        <p className="text-sm text-[var(--ny-text-muted)]">Loading the recorded safety history…</p>
      </section>
    )
  }

  if (error || !data) {
    return (
      <section className={`card-base rounded-[var(--ny-radius-lg)] border border-[var(--ny-border)] bg-[var(--ny-white)] p-5 ${className}`}>
        <p className="flex items-center gap-2 text-sm text-[var(--ny-text-secondary)]">
          <FiInfo aria-hidden="true" /> {error || "No safety history is recorded for this place yet."}
        </p>
      </section>
    )
  }

  const overall = data.overall || {}
  const historical = data.historical || {}
  const current = data.current_conditions || {}
  const traveller = data.traveler_evidence || {}
  const baseline = historical.baseline_match || null
  const news = Array.isArray(data.verified_news) ? data.verified_news : []
  const warnings = Array.isArray(data.navigation_risk?.specific_warnings)
    ? data.navigation_risk.specific_warnings
    : []
  // Admin-curated risk factors (accident history, travel safety,
  // weather exposure, emergency coverage). Null until a staff
  // member reviews the place, so it renders as "not reviewed yet".
  const safety = data.safety_profile || null

  // "Nothing on record" must never look like "safe".
  const noLiveFeed = Number(current.active_count || 0) === 0

  return (
    <section
      className={`overflow-hidden rounded-[var(--ny-radius-lg)] border border-[var(--ny-border)] bg-[var(--ny-white)] ${className}`}
      aria-labelledby="place-history-h"
      data-testid="place-history"
    >
      {/* header */}
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-[var(--ny-border)] bg-[var(--ny-soft-green)] px-5 py-4">
        <div className="flex items-start gap-3">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-[var(--ny-radius-md)] bg-[var(--ny-green-dark)] text-white" aria-hidden="true">
            <FiShield size={19} />
          </span>
          <div>
            <h2 id="place-history-h" className="m-0 flex items-center gap-2 text-base font-bold text-[var(--ny-text)]">
              <FiClock aria-hidden="true" /> History &amp; safety record
            </h2>
            <p className="m-0 mt-0.5 text-xs text-[var(--ny-text-muted)]">
              Built from recorded evidence, not a live judgement about today.
            </p>
          </div>
        </div>
        <LevelBadge level={overall.level} />
      </div>

      <div className="space-y-5 p-5">
        {/* model indicator */}
        <div>
          <Row label="Recorded risk indicator" value={`${overall.score ?? "—"} / 100`} />
          {overall.explanation ? (
            <p className="mt-1 text-xs leading-5 text-[var(--ny-text-muted)]">{overall.explanation}</p>
          ) : null}
          {overall.is_official_warning === false ? (
            <p className="mt-1 text-xs text-[var(--ny-text-muted)]">
              This is a model indicator, <b>not</b> an official government warning.
            </p>
          ) : null}
        </div>

        {/* historical counts */}
        <div>
          <h3 className="m-0 flex items-center gap-2 text-sm font-bold text-[var(--ny-text)]">
            <FiBarChart2 aria-hidden="true" /> Recorded hazards for this place
          </h3>
          {baseline ? (
            <p className="mt-1 flex items-start gap-1.5 text-xs leading-5 text-[var(--ny-text-muted)]">
              <FiMapPin className="mt-0.5 shrink-0" aria-hidden="true" />
              <span>
                Counts come from <b>{baseline.destination}</b>
                {Number(baseline.distance_km) > 0 ? `, the nearest place on record (${Number(baseline.distance_km).toFixed(1)} km away)` : ""}
                {baseline.method ? ` — matched by ${baseline.method}` : ""}.
              </span>
            </p>
          ) : null}
          <HistoryBars breakdown={historical.breakdown} />
        </div>

        {/* curated safety profile — admin-reviewed factors */}
        <div>
          <h3 className="m-0 flex items-center gap-2 text-sm font-bold text-[var(--ny-text)]">
            <FiCheckCircle aria-hidden="true" /> Reviewed safety profile
          </h3>
          {safety ? (
            <div className="mt-2 space-y-3">
              {safety.safety_summary ? (
                <p className="m-0 text-xs leading-5 text-[var(--ny-text-secondary)]">
                  {safety.safety_summary}
                </p>
              ) : null}

              {/* Travel safety */}
              <div className="rounded-[var(--ny-radius-md)] border border-[var(--ny-border)] px-3 py-2">
                <p className="m-0 text-xs font-bold uppercase tracking-wider text-[var(--ny-text-muted)]">
                  How safe for travelling
                </p>
                <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                  <span className={`rounded-full border px-2.5 py-1 text-xs font-bold ${
                    safety.travel_safety_rating === "very_safe" || safety.travel_safety_rating === "safe"
                      ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                      : safety.travel_safety_rating === "risky" || safety.travel_safety_rating === "unsafe"
                        ? "bg-red-50 text-red-800 border-red-200"
                        : "bg-amber-50 text-amber-800 border-amber-200"
                  }`}>
                    {(safety.travel_safety_rating || "moderate").replace(/_/g, " ")}
                  </span>
                  {safety.travel_safety_score != null ? (
                    <span className="text-xs text-[var(--ny-text-muted)]">
                      {Number(safety.travel_safety_score).toFixed(0)} / 100
                    </span>
                  ) : null}
                  {safety.accident_trend ? (
                    <span className="text-xs text-[var(--ny-text-muted)]">
                      accidents {safety.accident_trend.replace(/_/g, " ")}
                    </span>
                  ) : null}
                </div>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {[
                    ["Solo travel", safety.solo_travel_safety],
                    ["At night", safety.night_safety],
                    ["Family", safety.family_safety],
                    ["Solo female", safety.female_traveler_safety],
                    ["Roads", safety.road_quality],
                    ["Trails marked", safety.trail_marking],
                    ["Mobile network", safety.mobile_network_coverage],
                  ].map(([label, value]) => (
                    <span key={label} className="rounded-md bg-[var(--ny-soft-green)] px-2 py-1 text-[11px] text-[var(--ny-text-secondary)]">
                      {label}: <b>{String(value || "—").replace(/_/g, " ")}</b>
                    </span>
                  ))}
                </div>
              </div>

              {/* Weather exposure */}
              <div className="rounded-[var(--ny-radius-md)] border border-[var(--ny-border)] px-3 py-2">
                <p className="m-0 text-xs font-bold uppercase tracking-wider text-[var(--ny-text-muted)]">
                  Weather &amp; seasonal exposure
                </p>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {[
                    ["Monsoon", safety.monsoon_risk],
                    ["Winter snow", safety.winter_snow_risk],
                    ["Summer heat", safety.summer_heat_risk],
                    ["Lightning", safety.lightning_risk],
                    ["High altitude", safety.high_altitude_risk],
                    ["UV exposure", safety.uv_exposure],
                  ].map(([label, value]) => (
                    <span key={label} className="rounded-md bg-sky-50 px-2 py-1 text-[11px] text-sky-900 border border-sky-200">
                      {label}: <b>{String(value || "—").replace(/_/g, " ")}</b>
                    </span>
                  ))}
                </div>
              </div>

              {/* Emergency & life safety */}
              <div className="rounded-[var(--ny-radius-md)] border border-[var(--ny-border)] px-3 py-2">
                <p className="m-0 text-xs font-bold uppercase tracking-wider text-[var(--ny-text-muted)]">
                  Emergency &amp; life safety
                </p>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {[
                    ["Hospitals", safety.hospital_coverage],
                    ["Police", safety.police_presence],
                    ["Rescue", safety.rescue_availability],
                    ["Medical facility", safety.medical_facility_level],
                  ].map(([label, value]) => (
                    <span key={label} className="rounded-md bg-violet-50 px-2 py-1 text-[11px] text-violet-900 border border-violet-200">
                      {label}: <b>{String(value || "—").replace(/_/g, " ")}</b>
                    </span>
                  ))}
                </div>
                {safety.emergency_response_minutes != null ? (
                  <p className="m-0 mt-1.5 text-xs text-[var(--ny-text-muted)]">
                    Typical emergency response: <b>{safety.emergency_response_minutes} min</b>
                  </p>
                ) : null}
              </div>

              {/* Accident history */}
              {(safety.accidents_last_year != null || safety.accidents_last_5y != null) && (
                <p className="m-0 text-xs text-[var(--ny-text-muted)]">
                  Recorded accidents: <b>{safety.accidents_last_year ?? "—"}</b> last year
                  {safety.fatal_accidents_last_year != null ? ` (${safety.fatal_accidents_last_year} fatal)` : ""}
                  {safety.accidents_last_5y != null ? ` · ${safety.accidents_last_5y} over 5 years` : ""}
                  {safety.last_major_incident_date ? ` · last major: ${new Date(safety.last_major_incident_date).toLocaleDateString()}` : ""}
                </p>
              )}

              {/* Risk causes */}
              {Array.isArray(safety.risk_causes) && safety.risk_causes.length > 0 && (
                <div>
                  <p className="m-0 text-xs font-bold uppercase tracking-wider text-[var(--ny-text-muted)] mb-1.5">
                    Main risk causes
                  </p>
                  <ul className="m-0 space-y-1">
                    {safety.risk_causes.slice(0, 8).map((cause, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-[var(--ny-text-secondary)]">
                        <FiAlertTriangle className="mt-0.5 shrink-0 text-[var(--ny-warm-gold)]" aria-hidden="true" />
                        <span>
                          <b>{cause.cause || cause.label || cause}</b>
                          {cause.severity ? ` · ${cause.severity}` : ""}
                          {cause.frequency ? ` · ${cause.frequency}` : ""}
                          {cause.note ? ` — ${cause.note}` : ""}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {safety.last_reviewed ? (
                <p className="m-0 text-[11px] text-[var(--ny-text-muted)]">
                  Reviewed by staff {new Date(safety.last_reviewed).toLocaleDateString()}
                </p>
              ) : null}
            </div>
          ) : (
            <p className="mt-1 flex items-start gap-2 rounded-[var(--ny-radius-md)] border border-[var(--ny-border)] bg-[var(--ny-soft-gold)] px-3 py-2 text-xs leading-5 text-[var(--ny-text-secondary)]">
              <FiInfo className="mt-0.5 shrink-0 text-[var(--ny-warm-gold)]" aria-hidden="true" />
              <span>
                This place has not been reviewed by staff yet, so the curated
                safety factors (travel safety, weather exposure, emergency
                coverage) are not published. The recorded hazard counts and
                model indicator above are the available evidence.
              </span>
            </p>
          )}
        </div>

        {/* live advisories */}
        <div>
          <h3 className="m-0 flex items-center gap-2 text-sm font-bold text-[var(--ny-text)]">
            <FiZap aria-hidden="true" /> Advisories right now
          </h3>
          {noLiveFeed ? (
            <p className="mt-2 flex items-start gap-2 rounded-[var(--ny-radius-md)] border border-[var(--ny-border)] bg-[var(--ny-soft-gold)] px-3 py-2 text-xs leading-5 text-[var(--ny-text-secondary)]">
              <FiAlertTriangle className="mt-0.5 shrink-0 text-[var(--ny-warm-gold)]" aria-hidden="true" />
              <span>
                No advisory is recorded for this place at the moment. That means
                nothing has been filed — not that conditions are confirmed good.
                Check the official travel advice before you travel.
              </span>
            </p>
          ) : (
            <ul className="mt-2 space-y-2">
              {(current.items || []).map((item, index) => (
                <li key={item.id || index} className="rounded-[var(--ny-radius-md)] border border-[var(--ny-border)] px-3 py-2">
                  <p className="m-0 text-sm font-semibold text-[var(--ny-text)]">{item.title}</p>
                  <p className="m-0 mt-0.5 text-xs text-[var(--ny-text-muted)]">
                    {item.severity} · {item.source_name}
                    {item.expires_at ? ` · until ${new Date(item.expires_at).toLocaleDateString()}` : ""}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* verified news */}
        <div>
          <h3 className="m-0 flex items-center gap-2 text-sm font-bold text-[var(--ny-text)]">
            <FiActivity aria-hidden="true" /> Verified news reports
          </h3>
          {news.length ? (
            <ul className="mt-2 space-y-2">
              {news.map((item, index) => (
                <li key={item.id || index} className="rounded-[var(--ny-radius-md)] border border-[var(--ny-border)] px-3 py-2">
                  <p className="m-0 text-sm font-semibold text-[var(--ny-text)]">{item.title}</p>
                  {item.summary ? <p className="m-0 mt-0.5 text-xs leading-5 text-[var(--ny-text-secondary)]">{item.summary}</p> : null}
                  <p className="m-0 mt-1 text-xs text-[var(--ny-text-muted)]">
                    {item.source_name}
                    {item.published_at ? ` · ${new Date(item.published_at).toLocaleDateString()}` : ""}
                  </p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-1 text-xs text-[var(--ny-text-muted)]">
              No news report has been verified for this place.
            </p>
          )}
        </div>

        {/* altitude / route warnings */}
        {warnings.length ? (
          <div>
            <h3 className="m-0 flex items-center gap-2 text-sm font-bold text-[var(--ny-text)]">
              <FiAlertTriangle aria-hidden="true" /> Worth knowing before you set off
            </h3>
            <ul className="mt-2 space-y-1.5">
              {warnings.map((warning, index) => (
                <li key={index} className="flex items-start gap-2 text-sm text-[var(--ny-text-secondary)]">
                  <FiCheckCircle className="mt-0.5 shrink-0 text-[var(--ny-gold)]" aria-hidden="true" />
                  <span>{warning}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {/* traveller reports */}
        <div className="border-t border-[var(--ny-border)] pt-3">
          <Row label="Traveller reports" value={traveller.report_count ?? 0} />
          {traveller.average_safety_rating != null ? (
            <Row label="Average safety rating" value={`${traveller.average_safety_rating} / 10`} />
          ) : null}
          {Number(traveller.report_count || 0) === 0 ? (
            <p className="mt-1 text-xs text-[var(--ny-text-muted)]">
              No traveller has filed a safety report for this place yet.
            </p>
          ) : null}
        </div>

        {data.disclaimer ? (
          <p className="m-0 rounded-[var(--ny-radius-md)] bg-[var(--ny-soft-blue)] px-3 py-2 text-xs leading-5 text-[var(--ny-text-secondary)]">
            {data.disclaimer}
          </p>
        ) : null}
      </div>
    </section>
  )
}
