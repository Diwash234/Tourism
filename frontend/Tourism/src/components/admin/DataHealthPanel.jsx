import { useEffect, useState } from "react"
import {
  FiActivity, FiCheckCircle, FiAlertTriangle, FiRefreshCw, FiMapPin,
  FiTruck, FiDollarSign, FiFileText, FiShield, FiX, FiTrendingUp, FiSave
} from "react-icons/fi"
import axiosClient from "../../api/axiosClient"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

export default function DataHealthPanel() {
  const { showToast } = useToast()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  // Rate Adjustments state
  const [rates, setRates] = useState(null)
  const [savingRates, setSavingRates] = useState(false)
  const [syncingOfficial, setSyncingOfficial] = useState(false)

  const loadStats = () => {
    setLoading(true)
    axiosClient.get("/admin/data-health/")
      .then(({ data }) => setStats(data))
      .catch(() => showToast("Could not load data health stats.", "error"))
      .finally(() => setLoading(false))

    adminApi.getRateAdjustments()
      .then(({ data }) => setRates(data))
      .catch(() => setRates(null))
  }

  useEffect(() => {
    loadStats()
  }, [])

  const handleSaveRates = (e) => {
    e.preventDefault()
    if (!rates) return
    setSavingRates(true)
    adminApi.updateRateAdjustments(rates)
      .then(({ data }) => {
        showToast("Rate multipliers updated successfully!", "success")
        if (data?.settings) setRates(data.settings)
      })
      .catch(() => showToast("Failed to update rate multipliers.", "error"))
      .finally(() => setSavingRates(false))
  }

  const handleSyncOfficial = () => {
    setSyncingOfficial(true)
    adminApi.updateRateAdjustments({ fetch_official: true })
      .then(({ data }) => {
        showToast("Synced with official Nepal Rastra Bank CPI & MoCTCA fare index!", "success")
        if (data?.settings) setRates(data.settings)
      })
      .catch(() => showToast("Sync failed.", "error"))
      .finally(() => setSyncingOfficial(false))
  }

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

      {/* Official Government CPI & Rate Adjustments Studio */}
      {rates && (
        <form onSubmit={handleSaveRates} className="p-6 rounded-3xl bg-slate-950 border border-slate-800 space-y-4 shadow-xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div>
              <span className="px-3 py-0.5 rounded-full bg-amber-400/20 text-amber-300 text-[10px] font-black uppercase tracking-wider border border-amber-400/30">
                Official Government Rate & CPI Studio
              </span>
              <h3 className="text-lg font-black text-white mt-1">Travel Cost & Inflation Rate Multipliers</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Source: <b>{rates.last_synced_source || "MoCTCA / NRB Index"}</b> · Updated: {rates.last_updated ? new Date(rates.last_updated).toLocaleString() : "Recently"}
              </p>
            </div>

            <button
              type="button"
              onClick={handleSyncOfficial}
              disabled={syncingOfficial}
              className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs flex items-center gap-1.5 shadow"
            >
              <FiTrendingUp size={14} /> {syncingOfficial ? "Syncing..." : "Sync Government CPI & Fare Index"}
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div className="space-y-1">
              <label className="font-bold text-slate-300 block">Food Cost Index Multiplier</label>
              <input
                type="number"
                step="0.01"
                min="0.5"
                max="3.0"
                value={rates.food_multiplier || 1.0}
                onChange={(e) => setRates({ ...rates, food_multiplier: parseFloat(e.target.value) || 1.0 })}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-amber-400"
              />
              <span className="text-[10px] text-slate-400">Baseline 1.00 (+4% inflation = 1.04)</span>
            </div>

            <div className="space-y-1">
              <label className="font-bold text-slate-300 block">Transport Fare Index Multiplier</label>
              <input
                type="number"
                step="0.01"
                min="0.5"
                max="3.0"
                value={rates.transport_multiplier || 1.0}
                onChange={(e) => setRates({ ...rates, transport_multiplier: parseFloat(e.target.value) || 1.0 })}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-amber-400"
              />
              <span className="text-[10px] text-slate-400">Baseline 1.00 (+6% fuel adjustment = 1.06)</span>
            </div>

            <div className="space-y-1">
              <label className="font-bold text-slate-300 block">Accommodation Cost Multiplier</label>
              <input
                type="number"
                step="0.01"
                min="0.5"
                max="3.0"
                value={rates.accommodation_multiplier || 1.0}
                onChange={(e) => setRates({ ...rates, accommodation_multiplier: parseFloat(e.target.value) || 1.0 })}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-amber-400"
              />
              <span className="text-[10px] text-slate-400">Baseline 1.00 (+2% seasonal index = 1.02)</span>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={savingRates}
              className="px-5 py-2 rounded-xl bg-amber-400 hover:bg-amber-500 text-slate-950 font-black text-xs flex items-center gap-1.5 shadow"
            >
              <FiSave size={14} /> {savingRates ? "Saving..." : "Save Rate Multipliers"}
            </button>
          </div>
        </form>
      )}
    </div>
  )
}
