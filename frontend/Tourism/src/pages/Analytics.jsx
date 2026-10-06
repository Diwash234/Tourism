import { useCallback, useEffect, useState } from "react"
import { Link } from "react-router-dom"
import {
  FiUsers, FiEye, FiTrendingUp, FiDownload, FiActivity,
  FiMapPin, FiBarChart2, FiClock, FiAlertTriangle, FiShield, FiRefreshCw,
} from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import useToast from "../hooks/useToast"
import adminApi from "../api/adminApi"
import destinationApi from "../api/destinationApi"

/**
 * Admin analytics.
 *
 * This page used to render `Math.random()` as if it were measurement: page
 * views, "active users right now", the live activity feed, the destination
 * leaderboard, the search-query list, the conversion funnel and four
 * engagement metrics were all hardcoded or randomly generated, and the stat
 * cards showed fixed literals ("12,847" users, "45,200" page views). Nothing
 * on it came from the database, so an admin reading it would be reading
 * fiction.
 *
 * Everything here is now read from real endpoints:
 *   - /admin/stats        platform totals (users, destinations, views, visits)
 *   - /admin/user-tracking/  real per-user city, view counts, recent views,
 *                            and live safety signals (active SOS, live trips)
 *   - /destinations/?ordering=-views_count  real destination leaderboard
 *
 * Metrics the platform does not actually record (session duration, bounce
 * rate, pages per session, search queries) are shown as explicitly
 * unrecorded rather than filled with invented numbers. They need an analytics
 * event pipeline before they can be displayed truthfully.
 */

const NOT_RECORDED = [
  "Average session duration",
  "Bounce rate",
  "Pages per session",
  "Return-visitor rate",
  "Search queries",
]

const exportToCSV = (filename, headers, rows) => {
  const csvContent = [
    headers.join(","),
    ...rows.map((row) => row.map((cell) => `"${String(cell ?? "").replace(/"/g, '""')}"`).join(",")),
  ].join("\n")
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
  const link = document.createElement("a")
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}

const StatCard = ({ icon: Icon, label, value, hint, color }) => (
  <div className="card-base p-5 flex items-start gap-4">
    <div className="p-3 rounded-xl flex-shrink-0" style={{ backgroundColor: `${color}15`, color }}>
      <Icon size={22} />
    </div>
    <div className="min-w-0 flex-1">
      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">
        {value == null ? "—" : Number(value).toLocaleString()}
      </p>
      {hint && <p className="text-xs mt-1 text-gray-500 dark:text-gray-400">{hint}</p>}
    </div>
  </div>
)

const Analytics = () => {
  const { showToast } = useToast()
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState("")
  const [stats, setStats] = useState(null)
  const [tracking, setTracking] = useState([])
  const [topDestinations, setTopDestinations] = useState([])

  const load = useCallback(async ({ quiet = false } = {}) => {
    if (quiet) setRefreshing(true)
    else setLoading(true)
    setError("")
    try {
      const [statsRes, trackingRes, destRes] = await Promise.allSettled([
        adminApi.getStats(),
        adminApi.getUserTracking(),
        destinationApi.getDestinations({ ordering: "-views_count", page_size: 8 }),
      ])

      // Stats drive the headline numbers; if the capability gate rejects this
      // staff account we say so rather than showing zeros as if they were real.
      if (statsRes.status === "fulfilled") {
        setStats(statsRes.value.data)
      } else {
        setStats(null)
        setError(
          statsRes.reason?.response?.data?.detail ||
            statsRes.reason?.response?.data?.message ||
            "Platform statistics are not available for your account."
        )
      }

      setTracking(trackingRes.status === "fulfilled" && Array.isArray(trackingRes.value.data)
        ? trackingRes.value.data
        : [])

      const destData = destRes.status === "fulfilled" ? destRes.value.data : null
      setTopDestinations(Array.isArray(destData?.results) ? destData.results : [])
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    const t = setTimeout(() => load(), 0)
    return () => clearTimeout(t)
  }, [load])

  const handleExport = useCallback(() => {
    const headers = ["Destination", "Views", "Average rating", "District"]
    const rows = topDestinations.map((d) => [
      d.name, d.views_count ?? "", d.average_rating ?? "", d.district || "",
    ])
    const totals = stats
      ? [[
          "TOTALS", stats.totalDestinationViews ?? "", "",
          `users=${stats.totalUsers ?? ""} destinations=${stats.totalDestinations ?? ""} visits=${stats.totalVisitsLogged ?? ""}`,
        ]]
      : []
    exportToCSV("analytics-summary.csv", headers, [...rows, ...totals])
    showToast("Exported the figures currently shown on this page", "success")
  }, [topDestinations, stats, showToast])

  // Real safety signals: users who currently have an unresolved SOS or a live
  // shared trip. This is the only genuinely "live" signal the platform keeps.
  const activeEmergencies = tracking.filter((u) => u.has_medical_emergency)
  const liveTrips = tracking.filter((u) => u.is_navigating)

  // Real recent activity: actual destination views, newest first.
  const recentViews = tracking
    .flatMap((u) => (u.recent_history || []).map((h) => ({ ...h, user: u.full_name || u.email })))
    .filter((h) => h.viewed_at)
    .sort((a, b) => new Date(b.viewed_at) - new Date(a.viewed_at))
    .slice(0, 12)

  if (loading) return <Loader fullScreen text="Loading analytics..." />

  return (
    <div className="ny-page mx-auto w-full max-w-7xl space-y-6">
      <PageHeader
        title="Analytics Dashboard"
        subtitle="Platform totals and live safety signals, read directly from the database."
        icon={FiBarChart2}
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={() => load({ quiet: true })}
              disabled={refreshing}
              className="btn-outline flex items-center gap-2 text-sm"
            >
              <FiRefreshCw size={16} className={refreshing ? "animate-spin" : ""} />
              Refresh
            </button>
            <button onClick={handleExport} className="btn-primary flex items-center gap-2 text-sm">
              <FiDownload size={16} /> Export CSV
            </button>
          </div>
        }
      />

      {error && (
        <div role="alert" className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          <FiAlertTriangle className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Live safety signals — the only genuinely live data the platform keeps */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-600 rounded-2xl p-6 text-white shadow-lg">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-white/20 rounded-xl">
              <FiActivity size={28} />
            </div>
            <div>
              <p className="text-sm font-medium text-emerald-100">Live safety signals</p>
              <p className="text-4xl font-black">
                {activeEmergencies.length}
                <span className="text-base font-semibold text-emerald-100"> active SOS · </span>
                {liveTrips.length}
                <span className="text-base font-semibold text-emerald-100"> live trips</span>
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {activeEmergencies.slice(0, 5).map((u) => (
              <span key={`sos-${u.id}`} className="px-3 py-1 bg-white/20 rounded-full text-xs font-medium">
                SOS · {u.city}
              </span>
            ))}
            {activeEmergencies.length === 0 && liveTrips.length === 0 && (
              <span className="px-3 py-1 bg-white/20 rounded-full text-xs font-medium">
                No active SOS or live trips
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Real totals */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={FiUsers} label="Total Users" value={stats?.totalUsers} hint="All registered accounts" color="#1B8A5A" />
        <StatCard icon={FiEye} label="Destination Views" value={stats?.totalDestinationViews} hint="Cumulative, all destinations" color="#0B3D91" />
        <StatCard icon={FiMapPin} label="Destinations" value={stats?.totalDestinations} hint={`${stats?.approvedDestinations ?? 0} published`} color="#F59E0B" />
        <StatCard icon={FiClock} label="Visits Logged" value={stats?.totalVisitsLogged} hint="Visit-history records" color="#DC143C" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={FiShield} label="Active Alerts" value={stats?.activeAlerts} hint="Published safety alerts" color="#0B3D91" />
        <StatCard icon={FiAlertTriangle} label="Active Emergencies" value={stats?.activeEmergencies} hint="Unresolved SOS records" color="#DC143C" />
        <StatCard icon={FiTrendingUp} label="Risk Reports" value={stats?.totalRiskReports} hint="Traveller risk feedback" color="#1B8A5A" />
        <StatCard icon={FiTrendingUp} label="Expense Reports" value={stats?.totalExpenseReports} hint="Traveller spend feedback" color="#F59E0B" />
      </div>

      {/* Real destination leaderboard */}
      <div className="card-base p-5">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <FiMapPin size={18} className="text-emerald-600" />
          Most-viewed destinations
        </h3>
        {topDestinations.length === 0 ? (
          <EmptyState
            title="No destination data available"
            subtitle="Destination view counts could not be loaded for your account."
          />
        ) : (
          <div className="space-y-3">
            {topDestinations.map((dest, i) => {
              const max = topDestinations[0]?.views_count || 1
              return (
                <div key={dest.id} className="flex items-center justify-between gap-4 py-2 border-b border-gray-50 last:border-0">
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="text-xs font-bold text-gray-400 w-5">#{i + 1}</span>
                    <Link to={`/destinations/${dest.slug}`} className="font-medium text-gray-800 hover:underline truncate">
                      {dest.name}
                    </Link>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <div className="hidden sm:block w-32 h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 rounded-full"
                        style={{ width: `${Math.round(((dest.views_count || 0) / max) * 100)}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-600 w-16 text-right">
                      {(dest.views_count || 0).toLocaleString()}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Real recent activity */}
      <div className="card-base p-5">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <FiActivity size={18} className="text-emerald-600" />
          Recent destination views
        </h3>
        {recentViews.length === 0 ? (
          <EmptyState
            title="No recorded views"
            subtitle="No destination views have been logged yet."
          />
        ) : (
          <div className="space-y-2">
            {recentViews.map((view, i) => (
              <div key={`${view.user}-${view.viewed_at}-${i}`} className="flex items-center justify-between gap-4 py-2 px-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-2 h-2 bg-emerald-500 rounded-full shrink-0" />
                  <span className="text-sm font-medium text-gray-700 truncate">
                    {view.user || "Traveller"}
                    {view.destination__name ? ` viewed ${view.destination__name}` : " viewed a destination"}
                  </span>
                </div>
                <span className="text-xs text-gray-500 shrink-0">
                  {new Date(view.viewed_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Honest gap: what the platform does not measure */}
      <div className="card-base p-5 border border-dashed">
        <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
          <FiAlertTriangle size={18} className="text-amber-500" />
          Not currently recorded
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
          These are standard analytics metrics, but nothing in this codebase captures them. They are
          listed as unavailable instead of being filled with placeholder numbers — showing invented
          figures on an admin dashboard is worse than showing nothing. They need an analytics event
          pipeline before they can be displayed.
        </p>
        <ul className="flex flex-wrap gap-2">
          {NOT_RECORDED.map((metric) => (
            <li key={metric} className="px-2 py-1 bg-gray-100 text-gray-500 text-xs rounded-full line-through">
              {metric}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export default Analytics