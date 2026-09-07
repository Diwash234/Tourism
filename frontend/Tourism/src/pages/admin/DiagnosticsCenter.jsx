/**
 * Diagnostics Center - new admin page that ties together the audit
 * + system_health backend apps. Gives you one place to see:
 *   - Live system health (DB, disk, ML, external APIs, error rate)
 *   - A "Run diagnostics now" button that writes a HealthSample
 *   - Open errors (backend exceptions + frontend JS errors) with the
 *     ability to acknowledge/resolve them
 *   - Recent audit log (who did what, when)
 *
 * No feature here can crash the page: every sub-panel is wrapped in
 * its own ErrorBoundary.
 */
import { useEffect, useState, useCallback } from "react"
import {
  FiActivity, FiAlertCircle, FiCheckCircle, FiClock, FiRefreshCw,
  FiShield, FiList, FiWifi, FiDatabase, FiHardDrive, FiCpu, FiImage,
  FiServer, FiGlobe, FiCheckSquare,
} from "react-icons/fi"
import adminApi from "../../api/adminApi"
import ErrorBoundary from "../../components/common/ErrorBoundary"

const severityColor = {
  debug: "bg-stone-100 text-stone-700",
  info: "bg-sky-50 text-sky-700",
  warning: "bg-amber-50 text-amber-800",
  error: "bg-rose-50 text-rose-700",
  critical: "bg-rose-100 text-rose-900",
}
const sourceLabel = {
  backend: "Backend", frontend: "Frontend", celery: "Worker",
  cron: "Cron", external: "External",
}

const healthIcon = (ok) =>
  ok === true ? <FiCheckCircle className="text-emerald-600" />
  : ok === false ? <FiAlertCircle className="text-rose-600" />
  : <FiClock className="text-amber-500" />

function CheckRow({ label, data }) {
  if (!data) return null
  const ok = data.ok
  const lat = data.latency_ms != null ? `${data.latency_ms.toFixed(1)}ms` : null
  const detail =
    data.status != null ? `status ${data.status}`
    : data.disk_used_pct != null ? `${data.disk_used_pct.toFixed(1)}% used`
    : data.memory_used_pct != null && data.memory_used_pct != null ? `${data.memory_used_pct.toFixed(0)}% memory`
    : data.cpu_pct != null && data.cpu_pct != null ? `${data.cpu_pct.toFixed(0)}% CPU`
    : data.errors_per_minute != null ? `${data.errors_per_minute.toFixed(2)}/min`
    : data.error ? data.error
    : data.note || ""
  return (
    <div className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-stone-50 transition-colors">
      <div className="flex items-center gap-3 min-w-0">
        <span className="w-5 flex items-center justify-center">{healthIcon(ok)}</span>
        <span className="text-sm font-medium text-stone-800 truncate">{label}</span>
      </div>
      <span className="text-xs text-stone-500 truncate ml-3">{detail || (lat ? lat : "")}</span>
    </div>
  )
}

function HealthPanel() {
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(false)
  const [sample, setSample] = useState(null)
  const [err, setErr] = useState(null)

  const refresh = useCallback(async () => {
    setLoading(true); setErr(null)
    try {
      const [full, latest] = await Promise.all([
        adminApi.runHealthCheck(),
        adminApi.getLatestHealthSample().catch(() => ({ data: null })),
      ])
      setHealth(full.data)
      setSample(latest.data)
    } catch (e) {
      setErr(e?.response?.data?.detail || e.message || "Failed to fetch health")
    } finally { setLoading(false) }
  }, [])

  const runDiag = async () => {
    setLoading(true); setErr(null)
    try {
      const r = await adminApi.writeHealthSample()
      setSample(r.data.sample)
      const full = await adminApi.runHealthCheck()
      setHealth(full.data)
    } catch (e) {
      setErr(e?.response?.data?.detail || e.message)
    } finally { setLoading(false) }
  }

  useEffect(() => { refresh() }, [refresh])

  const overallOk = health?.ok
  const checks = health?.checks || {}

  return (
    <div className="card-base p-6">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${overallOk ? "bg-emerald-50 text-emerald-600" : "bg-rose-50 text-rose-600"}`}>
            <FiActivity size={22} />
          </div>
          <div>
            <h3 className="text-lg font-bold text-stone-900">Live system health</h3>
            <p className="text-xs text-stone-500">
              {health ? `Checked at ${new Date(health.checked_at).toLocaleTimeString()}` : "Loading…"}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button onClick={refresh} disabled={loading} className="btn-outline text-sm py-1.5 inline-flex items-center gap-2">
            <FiRefreshCw className={loading ? "animate-spin" : ""} /> Refresh
          </button>
          <button onClick={runDiag} disabled={loading} className="btn-primary text-sm py-1.5 inline-flex items-center gap-2">
            <FiActivity /> Run diagnostics now
          </button>
        </div>
      </div>

      {err && (
        <div className="mb-4 p-3 rounded-lg bg-rose-50 text-rose-700 text-sm">{err}</div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4">
        <CheckRow label="Database" data={checks.database} icon={<FiDatabase />} />
        <CheckRow label="Media storage" data={checks.media_storage} icon={<FiHardDrive />} />
        <CheckRow label="Disk" data={checks.disk} icon={<FiHardDrive />} />
        <CheckRow label="Memory" data={checks.memory} icon={<FiCpu />} />
        <CheckRow label="CPU" data={checks.cpu} icon={<FiCpu />} />
        <CheckRow label="ML service (port 8001)" data={checks.ml_service} icon={<FiServer />} />
        <CheckRow label="Overpass API" data={checks.overpass_api} icon={<FiGlobe />} />
        <CheckRow label="Wikimedia API" data={checks.wikimedia_api} icon={<FiImage />} />
        <CheckRow label="Error rate (5 min)" data={checks.error_rate} icon={<FiWifi />} />
      </div>

      {sample && (
        <div className="mt-5 p-3 rounded-xl bg-stone-50 border border-stone-200 text-xs text-stone-600">
          <b>Latest saved snapshot:</b> id={sample.id} ·{" "}
          <span className={sample.overall === "ok" ? "text-emerald-700" : "text-amber-700 font-semibold"}>
            {sample.overall?.toUpperCase()}
          </span>{" "}
          · DB {sample.db_ok ? "ok" : "FAIL"} · ML {sample.ml_ok == null ? "—" : sample.ml_ok ? "ok" : "down"} ·{" "}
          Overpass {sample.overpass_ok == null ? "—" : sample.overpass_ok ? "ok" : "blocked"} ·{" "}
          errors/min {sample.error_rate_5min ?? 0}
        </div>
      )}

      <p className="text-xs text-stone-500 mt-4">
        Tip: run <code className="text-stone-700 bg-stone-100 px-1 rounded">python manage.py health_snapshot</code>{" "}
        from a cron job every 5–15 minutes to build a time-series of system vitals.
      </p>
    </div>
  )
}

function ErrorsPanel() {
  const [errors, setErrors] = useState([])
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState({})
  const [filter, setFilter] = useState("open")

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const params = { ordering: "-last_seen", page_size: 50 }
      if (filter === "open") params.resolved = "false"
      if (filter === "resolved") params.resolved = "true"
      const r = await adminApi.getErrors(params)
      setErrors(r.data?.results || r.data || [])
    } finally { setLoading(false) }
  }, [filter])

  useEffect(() => { refresh() }, [refresh])

  const resolve = async (id) => {
    await adminApi.acknowledgeError(id, { resolved: true, resolution_note: "Marked resolved from admin UI" })
    refresh()
  }

  return (
    <div className="card-base p-6">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-rose-50 text-rose-600">
            <FiAlertCircle size={22} />
          </div>
          <div>
            <h3 className="text-lg font-bold text-stone-900">Error log</h3>
            <p className="text-xs text-stone-500">Backend exceptions + frontend JS crashes reported in real time</p>
          </div>
        </div>
        <div className="flex gap-2">
          {["open", "all", "resolved"].map(k => (
            <button key={k} onClick={() => setFilter(k)}
              className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition ${filter === k ? "bg-primary-600 text-white border-primary-600" : "bg-white border-stone-200 text-stone-600 hover:border-primary-300"}`}>
              {k[0].toUpperCase() + k.slice(1)}
            </button>
          ))}
          <button onClick={refresh} disabled={loading} className="btn-outline text-xs py-1.5 px-3 inline-flex items-center gap-1">
            <FiRefreshCw className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      <div className="divide-y divide-stone-100">
        {errors.length === 0 && !loading && (
          <div className="py-10 text-center text-sm text-stone-500">
            <FiCheckCircle size={28} className="mx-auto mb-2 text-emerald-500" />
            No errors in this view. 🎉
          </div>
        )}
        {errors.map((e) => (
          <div key={e.id} className="py-3">
            <div className="flex items-start justify-between gap-3 flex-wrap">
              <div className="flex items-start gap-3 min-w-0 flex-1">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${severityColor[e.severity] || severityColor.error}`}>
                  {e.severity}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-bold text-stone-900">{e.error_type}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-stone-100 text-stone-600">
                      {sourceLabel[e.source] || e.source}
                    </span>
                    {e.resolved && <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700">resolved</span>}
                  </div>
                  <p className="text-sm text-stone-600 truncate">{e.error_message}</p>
                  <div className="flex items-center gap-3 mt-1 text-[11px] text-stone-500 flex-wrap">
                    <span className="inline-flex items-center gap-1"><FiClock /> {new Date(e.last_seen).toLocaleString()}</span>
                    <span>×{e.occurrences}</span>
                    {e.endpoint && <span className="font-mono">{e.method || "GET"} {e.endpoint}</span>}
                    {e.component && <span>component: <b>{e.component}</b></span>}
                    {e.user_email && <span>user: {e.user_email}</span>}
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                {e.traceback && (
                  <button onClick={() => setSelected(s => ({ ...s, [e.id]: !s[e.id] }))}
                    className="text-xs px-2 py-1 rounded-md border border-stone-200 hover:bg-stone-50">
                    {selected[e.id] ? "Hide trace" : "Trace"}
                  </button>
                )}
                {!e.resolved && (
                  <button onClick={() => resolve(e.id)}
                    className="text-xs px-2 py-1 rounded-md bg-primary-600 text-white hover:bg-primary-700 inline-flex items-center gap-1">
                    <FiCheckSquare /> Resolve
                  </button>
                )}
              </div>
            </div>
            {selected[e.id] && e.traceback && (
              <pre className="mt-2 text-[11px] bg-stone-900 text-stone-100 p-3 rounded-lg overflow-x-auto max-h-64">
                {e.traceback}
              </pre>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function AuditPanel() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(false)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const r = await adminApi.getAuditLogs({ ordering: "-timestamp", page_size: 30 })
      setLogs(r.data?.results || r.data || [])
    } finally { setLoading(false) }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  return (
    <div className="card-base p-6">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-primary-50 text-primary-700">
            <FiList size={22} />
          </div>
          <div>
            <h3 className="text-lg font-bold text-stone-900">Recent activity (audit log)</h3>
            <p className="text-xs text-stone-500">Every state-changing API request is recorded here</p>
          </div>
        </div>
        <button onClick={refresh} disabled={loading} className="btn-outline text-xs py-1.5 px-3 inline-flex items-center gap-1">
          <FiRefreshCw className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-stone-500 uppercase tracking-wide border-b border-stone-200">
              <th className="py-2 pr-3">When</th>
              <th className="py-2 pr-3">Severity</th>
              <th className="py-2 pr-3">Category</th>
              <th className="py-2 pr-3">Action</th>
              <th className="py-2 pr-3">User</th>
              <th className="py-2 pr-3">Endpoint</th>
              <th className="py-2 pr-3 text-right">Status</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 && !loading && (
              <tr><td colSpan={7} className="py-8 text-center text-stone-500">No audit entries yet.</td></tr>
            )}
            {logs.map(l => (
              <tr key={l.id} className="border-b border-stone-100">
                <td className="py-2 pr-3 text-xs text-stone-500 whitespace-nowrap">
                  {new Date(l.timestamp).toLocaleString()}
                </td>
                <td className="py-2 pr-3">
                  <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${severityColor[l.severity] || severityColor.info}`}>{l.severity}</span>
                </td>
                <td className="py-2 pr-3 text-xs text-stone-600">{l.category}</td>
                <td className="py-2 pr-3 text-sm font-medium text-stone-800">{l.action}</td>
                <td className="py-2 pr-3 text-xs text-stone-500">{l.user_email || "—"}</td>
                <td className="py-2 pr-3 text-xs font-mono text-stone-500 truncate max-w-[220px]">{l.endpoint || "—"}</td>
                <td className="py-2 pr-3 text-right">
                  {l.status_code ? (
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${l.status_code >= 500 ? "bg-rose-50 text-rose-700" : l.status_code >= 400 ? "bg-amber-50 text-amber-700" : "bg-emerald-50 text-emerald-700"}`}>
                      {l.status_code}
                    </span>
                  ) : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function DiagnosticsCenter() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-2xl bg-primary-50 text-primary-700 flex items-center justify-center">
          <FiShield size={26} />
        </div>
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-stone-900">Diagnostics Center</h1>
          <p className="text-sm text-stone-500">Find mistakes fast: live health, every error, every action — all in one place.</p>
        </div>
      </div>

      <ErrorBoundary name="HealthPanel">
        <HealthPanel />
      </ErrorBoundary>
      <ErrorBoundary name="ErrorsPanel">
        <ErrorsPanel />
      </ErrorBoundary>
      <ErrorBoundary name="AuditPanel">
        <AuditPanel />
      </ErrorBoundary>
    </div>
  )
}
