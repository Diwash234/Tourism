import { useCallback, useEffect, useState } from "react"
import { FiRefreshCw, FiShield, FiAlertTriangle, FiFileText, FiCheck, FiEyeOff, FiSearch } from "react-icons/fi"
import adminPanelApi from "../../api/adminPanelApi"
import useToast from "../../hooks/useToast"

const SEVERITY_STYLE = {
  critical: "bg-rose-600 text-white",
  high: "bg-rose-100 text-rose-700",
  moderate: "bg-amber-100 text-amber-800",
  medium: "bg-amber-100 text-amber-800",
  low: "bg-slate-100 text-slate-600",
}

/**
 * Safety operations console (Staff Ops spec §16).
 * One queue over alerts, active hazards and user data reports;
 * every action audited server-side under safety.<kind>.<action>.
 */
export default function SafetyOpsPanel() {
  const { showToast } = useToast()
  const [data, setData] = useState({ counts: {}, alerts: [], hazards: [], reports: [] })
  const [loading, setLoading] = useState(true)
  const [busyKey, setBusyKey] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data: d } = await adminPanelApi.safetyQueue()
      setData(d)
    } catch (error) {
      showToast(error.response?.data?.detail || "Safety queue unavailable", "error")
    } finally {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const t = setTimeout(() => load(), 0)
    return () => clearTimeout(t)
  }, [load])

  const act = async (kind, item, action) => {
    const key = `${kind}-${item.id}-${action}`
    setBusyKey(key)
    try {
      const note = action === "reject" ? window.prompt("Rejection note (required):") || "" : ""
      if (action === "reject" && !note) return
      const { data: res } = await adminPanelApi.safetyAction(kind, item.id, action, note)
      showToast(res.detail || "Done", "success")
      load()
    } catch (error) {
      showToast(error.response?.data?.detail || "Action denied", "error")
    } finally {
      setBusyKey(null)
    }
  }

  const badge = (sev) => (
    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${SEVERITY_STYLE[sev] || "bg-slate-100"}`}>{sev}</span>
  )

  const section = (icon, title, items, render) => (
    <section key={title} className="bg-white border rounded-2xl overflow-hidden">
      <div className="p-4 border-b flex items-center gap-2">
        <span className="text-[#1D5146]">{icon}</span>
        <b className="text-slate-900">{title}</b>
        <span className="text-xs text-slate-400">({items.length})</span>
      </div>
      <div className="divide-y">
        {items.map((it) => (
          <div key={it.id} className="p-4 flex flex-col lg:flex-row lg:items-center gap-2">
            <div className="min-w-0 flex-1">{render(it)}</div>
          </div>
        ))}
        {!items.length && <p className="p-6 text-center text-slate-400 text-sm">Nothing here right now.</p>}
      </div>
    </section>
  )

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          ["Active alerts", data.counts?.active_alerts ?? 0, "text-rose-700"],
          ["Unverified alerts", data.counts?.unverified_alerts ?? 0, "text-amber-700"],
          ["Active hazards", data.counts?.active_hazards ?? 0, "text-rose-700"],
          ["Open reports", data.counts?.open_reports ?? 0, "text-sky-700"],
        ].map(([label, value, cls]) => (
          <div key={label} className="bg-white border rounded-2xl p-4">
            <p className="text-xs text-slate-500 font-bold">{label}</p>
            <p className={`text-2xl font-black ${cls}`}>{value}</p>
          </div>
        ))}
      </div>

      <div className="flex justify-end">
        <button onClick={load} className="px-3 py-2 bg-white border rounded-xl text-xs font-bold flex items-center gap-2">
          <FiRefreshCw className={loading ? "animate-spin" : ""} /> Refresh
        </button>
      </div>

      {section(
        <FiAlertTriangle />,
        "Weather & Safety Alerts",
        data.alerts,
        (a) => (
          <>
            <div className="flex flex-wrap items-center gap-2">
              <b className="text-sm text-slate-900">{a.title}</b>
              {badge(a.severity)}
              {a.is_verified ? <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-bold">VERIFIED</span> : <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 font-bold">UNVERIFIED</span>}
              {!a.is_active && <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-400 font-bold">DEACTIVATED</span>}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">{a.location} · {a.type} · source: {a.source || "unspecified"}</p>
            <div className="flex flex-wrap gap-2 mt-2">
              {a.is_active && !a.is_verified && (
                <button onClick={() => act("alert", a, "verify")} disabled={busyKey === `alert-${a.id}-verify`} className="px-3 py-1.5 bg-emerald-700 text-white rounded-lg text-xs font-bold flex items-center gap-1"><FiCheck /> Verify</button>
              )}
              {a.is_active && (
                <button onClick={() => act("alert", a, "deactivate")} disabled={busyKey === `alert-${a.id}-deactivate`} className="px-3 py-1.5 bg-slate-600 text-white rounded-lg text-xs font-bold flex items-center gap-1"><FiEyeOff /> Deactivate</button>
              )}
            </div>
          </>
        ),
      )}

      {section(
        <FiShield />,
        "Active Hazards",
        data.hazards,
        (h) => (
          <>
            <div className="flex flex-wrap items-center gap-2">
              <b className="text-sm text-slate-900">{h.title}</b>
              {badge(h.severity)}
              {h.is_verified && <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-bold">VERIFIED</span>}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">{h.location} · {h.type} · source: {h.source || "unspecified"}</p>
            <div className="flex flex-wrap gap-2 mt-2">
              {!h.is_verified && (
                <button onClick={() => act("hazard", h, "verify")} disabled={busyKey === `hazard-${h.id}-verify`} className="px-3 py-1.5 bg-emerald-700 text-white rounded-lg text-xs font-bold flex items-center gap-1"><FiCheck /> Verify</button>
              )}
              <button onClick={() => act("hazard", h, "resolve")} disabled={busyKey === `hazard-${h.id}-resolve`} className="px-3 py-1.5 bg-slate-600 text-white rounded-lg text-xs font-bold flex items-center gap-1"><FiEyeOff /> Resolve</button>
            </div>
          </>
        ),
      )}

      {section(
        <FiFileText />,
        "User Data Reports",
        data.reports,
        (r) => (
          <>
            <div className="flex flex-wrap items-center gap-2">
              <b className="text-sm text-slate-900">#{r.id} {r.title}</b>
              {badge(r.severity)}
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-bold uppercase">{r.status.replaceAll("_", " ")}</span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">{r.location} · {r.type} · reported by {r.reporter}</p>
            <div className="flex flex-wrap gap-2 mt-2">
              {r.status === "new" && (
                <button onClick={() => act("report", r, "review")} disabled={busyKey === `report-${r.id}-review`} className="px-3 py-1.5 bg-sky-700 text-white rounded-lg text-xs font-bold flex items-center gap-1"><FiSearch /> Start Review</button>
              )}
              {r.status !== "fixed" && (
                <button onClick={() => act("report", r, "fix")} disabled={busyKey === `report-${r.id}-fix`} className="px-3 py-1.5 bg-emerald-700 text-white rounded-lg text-xs font-bold flex items-center gap-1"><FiCheck /> Mark Fixed</button>
              )}
              <button onClick={() => act("report", r, "reject")} disabled={busyKey === `report-${r.id}-reject`} className="px-3 py-1.5 bg-rose-700 text-white rounded-lg text-xs font-bold flex items-center gap-1"><FiEyeOff /> Reject</button>
            </div>
          </>
        ),
      )}
    </div>
  )
}
