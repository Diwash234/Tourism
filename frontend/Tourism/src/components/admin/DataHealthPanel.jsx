import { useEffect, useState } from "react"
import {
  FiActivity, FiCheckCircle, FiAlertTriangle, FiRefreshCw, FiMapPin,
  FiTruck, FiDollarSign, FiFileText, FiShield, FiX
} from "react-icons/fi"
import axiosClient from "../../api/axiosClient"
import useToast from "../../hooks/useToast"

export default function DataHealthPanel() {
  const { showToast } = useToast()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadStats = () => {
    setLoading(true)
    axiosClient.get("/admin/data-health/")
      .then(({ data }) => setStats(data))
      .catch(() => showToast("Could not load data health stats.", "error"))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadStats()
  }, [])

  if (loading) {
    return <div className="p-8 text-center text-slate-400 font-bold">Loading Data Health & Quality Metrics...</div>
  }

  if (!stats) return null

  return (
    <div className="space-y-6 text-slate-100">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-950 p-6 rounded-3xl border border-slate-800 shadow-xl">
        <div>
          <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold uppercase tracking-wider">
            Data Quality & Anti-Hallucination Sentinel
          </span>
          <h2 className="text-2xl font-black text-white mt-1">Data Health & Provenance Dashboard</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Monitor verified GPS coordinates, route matrices, verified fares, and user-submitted data correction reports.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-[10px] text-slate-400 block uppercase font-bold">Data Quality Score</span>
            <span className="text-2xl font-black text-emerald-400">{stats.quality_score}%</span>
          </div>
          <button
            onClick={loadStats}
            className="p-3 bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-2xl text-white"
            title="Refresh Metrics"
          >
            <FiRefreshCw size={18} />
          </button>
        </div>
      </div>

      {/* Health Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: GPS Coordinates */}
        <div className="p-5 rounded-3xl bg-slate-950 border border-slate-800 space-y-2">
          <div className="flex justify-between items-center text-slate-400">
            <span className="text-xs font-bold uppercase">GPS Coordinates</span>
            <FiMapPin className="text-emerald-400" />
          </div>
          <p className="text-2xl font-black text-white">{stats.destinations?.verified_coordinates} / {stats.destinations?.total}</p>
          <div className="text-[11px] text-slate-400 space-y-0.5">
            <p>✓ Mapped: <span className="text-emerald-400 font-bold">{stats.destinations?.has_coordinates}</span></p>
            <p>⚠️ Missing coords: <span className="text-amber-400 font-bold">{stats.destinations?.missing_coordinates}</span></p>
          </div>
        </div>

        {/* Metric 2: Transit Routes */}
        <div className="p-5 rounded-3xl bg-slate-950 border border-slate-800 space-y-2">
          <div className="flex justify-between items-center text-slate-400">
            <span className="text-xs font-bold uppercase">Transit Routes</span>
            <FiTruck className="text-blue-400" />
          </div>
          <p className="text-2xl font-black text-white">{stats.transit_routes?.verified_routes} / {stats.transit_routes?.total}</p>
          <div className="text-[11px] text-slate-400 space-y-0.5">
            <p>✓ Verified: <span className="text-blue-400 font-bold">{stats.transit_routes?.verified_routes}</span></p>
            <p>⚠️ Missing fares: <span className="text-amber-400 font-bold">{stats.transit_routes?.missing_fares}</span></p>
          </div>
        </div>

        {/* Metric 3: User Error Reports */}
        <div className="p-5 rounded-3xl bg-slate-950 border border-slate-800 space-y-2">
          <div className="flex justify-between items-center text-slate-400">
            <span className="text-xs font-bold uppercase">User Reports</span>
            <FiAlertTriangle className="text-amber-400" />
          </div>
          <p className="text-2xl font-black text-white">{stats.data_reports?.open_reports}</p>
          <div className="text-[11px] text-slate-400 space-y-0.5">
            <p>🔴 Critical severity: <span className="text-rose-400 font-bold">{stats.data_reports?.critical_reports}</span></p>
            <p>Total reports filed: <span className="text-white font-bold">{stats.data_reports?.total_reports}</span></p>
          </div>
        </div>

        {/* Metric 4: Platform Rule */}
        <div className="p-5 rounded-3xl bg-emerald-950/40 border border-emerald-500/30 space-y-2 text-xs">
          <div className="flex justify-between items-center text-emerald-300 font-bold">
            <span>Zero Hallucination Guarantee</span>
            <FiShield size={18} />
          </div>
          <p className="text-[11px] text-emerald-200/90 leading-relaxed">
            All unrecorded distances, fares, or GPS coordinates explicitly display <i>"Not recorded"</i> across traveler views.
          </p>
        </div>
      </div>
    </div>
  )
}
