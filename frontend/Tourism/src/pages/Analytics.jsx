import { useEffect, useState, useCallback, useMemo } from "react"
import { motion } from "framer-motion"
import {
  FiUsers, FiEye, FiTrendingUp, FiDownload, FiActivity,
  FiMapPin, FiSearch, FiBarChart2, FiClock, FiArrowUp, FiArrowDown,
} from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import useToast from "../hooks/useToast"
import { CHART_COLORS } from "../components/charts/ChartCard"
import { Bar, Line, Pie } from "react-chartjs-2"
import "../components/charts/ChartSetup"

// ─── Simulated analytics data generator ──────────────────────────────────────
// In production, replace with real API calls to analyticsService
const generatePageViews = (days) => {
  const data = []
  const labels = []
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    labels.push(d.toLocaleDateString("en-US", { month: "short", day: "numeric" }))
    data.push(Math.floor(Math.random() * 500) + 200)
  }
  return { labels, data }
}

const POPULAR_DESTINATIONS = [
  { name: "Pokhara", views: 12450, change: 12.5 },
  { name: "Kathmandu", views: 10200, change: 8.3 },
  { name: "Chitwan", views: 8900, change: -2.1 },
  { name: "Lumbini", views: 7600, change: 15.7 },
  { name: "Everest Base Camp", views: 6800, change: 22.4 },
  { name: "Annapurna Circuit", views: 5400, change: 5.2 },
  { name: "Bhaktapur", views: 4200, change: -1.8 },
  { name: "Nagarkot", views: 3800, change: 9.6 },
]

const SEARCH_QUERIES = [
  { query: "pokhara hotels", count: 3420 },
  { query: "kathmandu to pokhara", count: 2890 },
  { query: "everest base camp trek", count: 2340 },
  { query: "chitwan safari", count: 1980 },
  { query: "lumbini temple", count: 1650 },
  { query: "nagarkot sunrise", count: 1420 },
  { query: "annapurna trek", count: 1200 },
  { query: "bhaktapur durbar square", count: 980 },
]

const FUNNEL_STAGES = [
  { label: "Page Views", value: 45200, color: "#1B8A5A" },
  { label: "Destination Views", value: 28400, color: "#0B3D91" },
  { label: "Itinerary Adds", value: 8600, color: "#F59E0B" },
  { label: "Booking Started", value: 3200, color: "#DC143C" },
  { label: "Booking Completed", value: 1450, color: "#70B1AB" },
]

const ENGAGEMENT_METRICS = [
  { label: "Avg. Session Duration", value: "4m 32s", change: 12.3, positive: true },
  { label: "Bounce Rate", value: "34.2%", change: -5.1, positive: true },
  { label: "Pages per Session", value: "3.8", change: 8.7, positive: true },
  { label: "Return Visitors", value: "42.5%", change: 3.2, positive: true },
]

// ─── CSV Export Helper ───────────────────────────────────────────────────────
const exportToCSV = (filename, headers, rows) => {
  const csvContent = [
    headers.join(","),
    ...rows.map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(",")),
  ].join("\n")
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
  const link = document.createElement("a")
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}

// ─── Stat Card Component ─────────────────────────────────────────────────────
const StatCard = ({ icon: Icon, label, value, change, positive, color }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className="card-base p-5 flex items-start gap-4"
  >
    <div
      className="p-3 rounded-xl flex-shrink-0"
      style={{ backgroundColor: `${color}15`, color }}
    >
      <Icon size={22} />
    </div>
    <div className="min-w-0 flex-1">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
      {change !== undefined && (
        <p className={`text-xs mt-1 flex items-center gap-1 ${positive ? "text-emerald-600" : "text-red-500"}`}>
          {positive ? <FiArrowUp size={12} /> : <FiArrowDown size={12} />}
          {Math.abs(change)}% from last period
        </p>
      )}
    </div>
  </motion.div>
)

// ─── Main Analytics Page ─────────────────────────────────────────────────────
const Analytics = () => {
  const { showToast } = useToast()
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState("7d")
  const [activeUsers, setActiveUsers] = useState(0)
  const [pageViews, setPageViews] = useState({ labels: [], data: [] })
  const [realtimeUsers, setRealtimeUsers] = useState([])

  // Simulate real-time active users
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveUsers(Math.floor(Math.random() * 150) + 80)
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  // Simulate real-time user locations
  useEffect(() => {
    const cities = ["Kathmandu", "Pokhara", "Chitwan", "Lumbini", "Nagarkot", "Bhaktapur", "Everest", "Annapurna"]
    const interval = setInterval(() => {
      const count = Math.floor(Math.random() * 8) + 3
      const users = Array.from({ length: count }, (_, i) => ({
        id: Date.now() + i,
        city: cities[Math.floor(Math.random() * cities.length)],
        page: ["/destinations", "/hotels", "/itinerary", "/budget-estimator", "/search"][Math.floor(Math.random() * 5)],
        time: new Date().toLocaleTimeString(),
      }))
      setRealtimeUsers(users)
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  // Load page views data
  useEffect(() => {
    setLoading(true)
    const days = timeRange === "7d" ? 7 : 30
    const data = generatePageViews(days)
    setPageViews(data)
    setLoading(false)
  }, [timeRange])

  const handleExportCSV = useCallback(() => {
    const headers = ["Date", "Page Views"]
    const rows = pageViews.labels.map((label, i) => [label, pageViews.data[i]])
    exportToCSV(`analytics-pageviews-${timeRange}.csv`, headers, rows)
    showToast("Analytics data exported to CSV", "success")
  }, [pageViews, timeRange, showToast])

  const pageViewsChartData = useMemo(() => ({
    labels: pageViews.labels,
    datasets: [{
      label: "Page Views",
      data: pageViews.data,
      borderColor: CHART_COLORS[0],
      backgroundColor: "rgba(27,138,90,0.15)",
      tension: 0.4,
      fill: true,
    }],
  }), [pageViews])

  const funnelChartData = useMemo(() => ({
    labels: FUNNEL_STAGES.map((s) => s.label),
    datasets: [{
      data: FUNNEL_STAGES.map((s) => s.value),
      backgroundColor: FUNNEL_STAGES.map((s) => s.color),
    }],
  }), [])

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
  }

  if (loading) return <Loader fullScreen text="Loading analytics..." />

  return (
    <div className="ny-page mx-auto w-full max-w-7xl space-y-6">
      <PageHeader
        title="Analytics Dashboard"
        subtitle="Real-time insights into user engagement, popular destinations, and conversion metrics."
        icon={FiBarChart2}
        actions={
          <div className="flex items-center gap-2">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="input-field text-sm py-2"
            >
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
            </select>
            <button
              onClick={handleExportCSV}
              className="btn-primary flex items-center gap-2 text-sm"
            >
              <FiDownload size={16} /> Export CSV
            </button>
          </div>
        }
      />

      {/* Real-time Active Users Banner */}
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-gradient-to-r from-emerald-600 to-teal-600 rounded-2xl p-6 text-white shadow-lg"
      >
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-white/20 rounded-xl">
              <FiActivity size={28} />
            </div>
            <div>
              <p className="text-sm font-medium text-emerald-100">Active Users Right Now</p>
              <p className="text-4xl font-black">{activeUsers}</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {realtimeUsers.slice(0, 5).map((u) => (
              <span key={u.id} className="px-3 py-1 bg-white/20 rounded-full text-xs font-medium">
                {u.city}
              </span>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={FiUsers} label="Total Users" value="12,847" change={12.5} positive color="#1B8A5A" />
        <StatCard icon={FiEye} label="Page Views" value="45,200" change={8.3} positive color="#0B3D91" />
        <StatCard icon={FiTrendingUp} label="Conversion Rate" value="3.2%" change={-0.4} positive={false} color="#F59E0B" />
        <StatCard icon={FiClock} label="Avg. Session" value="4m 32s" change={12.3} positive color="#DC143C" />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Page Views Chart */}
        <div className="lg:col-span-2 card-base p-5">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <FiEye size={18} className="text-emerald-600" />
            Page Views ({timeRange === "7d" ? "Last 7 Days" : "Last 30 Days"})
          </h3>
          <div className="h-64">
            <Line data={pageViewsChartData} options={chartOptions} />
          </div>
        </div>

        {/* Conversion Funnel */}
        <div className="card-base p-5">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <FiTrendingUp size={18} className="text-emerald-600" />
            Conversion Funnel
          </h3>
          <div className="h-64">
            <Pie data={funnelChartData} options={{ responsive: true, maintainAspectRatio: false }} />
          </div>
        </div>
      </div>

      {/* Popular Destinations & Search Queries */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Popular Destinations */}
        <div className="card-base p-5">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <FiMapPin size={18} className="text-emerald-600" />
            Popular Destinations
          </h3>
          <div className="space-y-3">
            {POPULAR_DESTINATIONS.map((dest, i) => (
              <div key={dest.name} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-bold text-gray-400 w-5">#{i + 1}</span>
                  <span className="font-medium text-gray-800">{dest.name}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-600">{dest.views.toLocaleString()}</span>
                  <span className={`text-xs font-medium ${dest.change >= 0 ? "text-emerald-600" : "text-red-500"}`}>
                    {dest.change >= 0 ? "+" : ""}{dest.change}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Search Query Analytics */}
        <div className="card-base p-5">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <FiSearch size={18} className="text-emerald-600" />
            Top Search Queries
          </h3>
          <div className="space-y-3">
            {SEARCH_QUERIES.map((sq, i) => (
              <div key={sq.query} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-bold text-gray-400 w-5">#{i + 1}</span>
                  <span className="font-medium text-gray-800">{sq.query}</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-24 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 rounded-full"
                      style={{ width: `${(sq.count / SEARCH_QUERIES[0].count) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm text-gray-600 w-12 text-right">{sq.count.toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Engagement Metrics */}
      <div className="card-base p-5">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <FiActivity size={18} className="text-emerald-600" />
          User Engagement Metrics
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {ENGAGEMENT_METRICS.map((metric) => (
            <div key={metric.label} className="p-4 bg-gray-50 rounded-xl">
              <p className="text-xs text-gray-500 font-medium">{metric.label}</p>
              <p className="text-xl font-bold text-gray-900 mt-1">{metric.value}</p>
              <p className={`text-xs mt-1 ${metric.positive ? "text-emerald-600" : "text-red-500"}`}>
                {metric.positive ? "+" : ""}{metric.change}%
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Real-time Activity Feed */}
      <div className="card-base p-5">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <FiActivity size={18} className="text-emerald-600" />
          Live Activity Feed
        </h3>
        {realtimeUsers.length === 0 ? (
          <EmptyState title="No active users" subtitle="Waiting for real-time activity..." />
        ) : (
          <div className="space-y-2">
            {realtimeUsers.map((u) => (
              <div key={u.id} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                  <span className="text-sm font-medium text-gray-700">User in {u.city}</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-500">
                  <span>{u.page}</span>
                  <span>{u.time}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Analytics
