import { useEffect, useState, useCallback, useMemo } from "react"
import { motion } from "framer-motion"
import { Link } from "react-router-dom"
import {
  FiUsers, FiMapPin, FiAlertTriangle, FiDollarSign, FiCheck, FiX,
  FiEye, FiShield, FiActivity, FiImage, FiPlus, FiTrash2, FiEdit3,
  FiNavigation, FiPhoneCall, FiUserCheck, FiUserX, FiSearch, FiRefreshCw,
  FiClock, FiTrendingUp, FiLayers, FiFileText, FiCalendar, FiHome,
  FiCompass, FiInfo, FiChevronRight, FiExternalLink, FiPlay, FiHeart,
  FiStar, FiMessageSquare, FiSettings, FiBarChart2, FiPieChart,
} from "react-icons/fi"
import adminApi from "../api/adminApi"
import destinationApi from "../api/destinationApi"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import useToast from "../hooks/useToast"
import useAuth from "../hooks/useAuth"
import { CHART_COLORS } from "../components/charts/ChartCard"
import { Bar, Line, Pie } from "react-chartjs-2"
import "../components/charts/ChartSetup"

// ─── Stat Card Component ─────────────────────────────────────────────────────
const StatCard = ({ icon: Icon, label, value, change, positive, color, onClick }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className="card-base p-5 flex items-start gap-4 cursor-pointer hover:shadow-lg transition-shadow"
    onClick={onClick}
  >
    <div className="p-3 rounded-xl flex-shrink-0" style={{ backgroundColor: `${color}15`, color }}>
      <Icon size={22} />
    </div>
    <div className="min-w-0 flex-1">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
      {change !== undefined && (
        <p className={`text-xs mt-1 ${positive ? "text-emerald-600" : "text-red-500"}`}>
          {positive ? "+" : ""}{change}% from last month
        </p>
      )}
    </div>
  </motion.div>
)

// ─── Activity Feed Item ──────────────────────────────────────────────────────
const ActivityItem = ({ icon: Icon, text, time, color }) => (
  <div className="flex items-start gap-3 py-3 border-b border-gray-50 last:border-0">
    <div className="p-2 rounded-lg flex-shrink-0" style={{ backgroundColor: `${color}15`, color }}>
      <Icon size={16} />
    </div>
    <div className="min-w-0 flex-1">
      <p className="text-sm text-gray-700">{text}</p>
      <p className="text-xs text-gray-400 mt-0.5">{time}</p>
    </div>
  </div>
)

// ─── Quick Action Button ─────────────────────────────────────────────────────
const QuickAction = ({ icon: Icon, label, color, onClick }) => (
  <button
    onClick={onClick}
    className="flex items-center gap-3 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors text-left"
  >
    <div className="p-2 rounded-lg" style={{ backgroundColor: `${color}15`, color }}>
      <Icon size={18} />
    </div>
    <span className="text-sm font-medium text-gray-700">{label}</span>
  </button>
)

// ─── System Health Monitor ───────────────────────────────────────────────────
const SystemHealth = ({ health }) => {
  const services = [
    { name: "API Server", status: health?.api || "operational", uptime: "99.9%" },
    { name: "Database", status: health?.db || "operational", uptime: "99.8%" },
    { name: "CDN", status: health?.cdn || "operational", uptime: "100%" },
    { name: "Email Service", status: health?.email || "operational", uptime: "99.5%" },
  ]

  return (
    <div className="card-base p-5">
      <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <FiActivity size={18} className="text-emerald-600" />
        System Health
      </h3>
      <div className="space-y-3">
        {services.map((service) => (
          <div key={service.name} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${service.status === "operational" ? "bg-emerald-500" : "bg-red-500"}`} />
              <span className="text-sm text-gray-700">{service.name}</span>
            </div>
            <span className="text-xs text-gray-500">{service.uptime}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── User Management Table ───────────────────────────────────────────────────
const UserManagementTable = ({ users, onEdit, onDelete, onToggleStatus }) => {
  const [search, setSearch] = useState("")

  const filteredUsers = useMemo(() => {
    if (!search) return users
    const term = search.toLowerCase()
    return users.filter(
      (u) =>
        u.email?.toLowerCase().includes(term) ||
        u.full_name?.toLowerCase().includes(term) ||
        u.role?.toLowerCase().includes(term)
    )
  }, [users, search])

  return (
    <div className="card-base p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900 flex items-center gap-2">
          <FiUsers size={18} className="text-emerald-600" />
          User Management
        </h3>
        <input
          type="text"
          placeholder="Search users..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input-field text-sm py-2 w-48"
        />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left py-3 px-2 font-medium text-gray-500">User</th>
              <th className="text-left py-3 px-2 font-medium text-gray-500">Role</th>
              <th className="text-left py-3 px-2 font-medium text-gray-500">Status</th>
              <th className="text-left py-3 px-2 font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredUsers.slice(0, 10).map((user) => (
              <tr key={user.id} className="border-b border-gray-50 hover:bg-gray-50">
                <td className="py-3 px-2">
                  <div>
                    <p className="font-medium text-gray-900">{user.full_name || user.email}</p>
                    <p className="text-xs text-gray-500">{user.email}</p>
                  </div>
                </td>
                <td className="py-3 px-2">
                  <span className="px-2 py-1 bg-gray-100 rounded-full text-xs font-medium text-gray-700">
                    {user.role}
                  </span>
                </td>
                <td className="py-3 px-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    user.is_active ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"
                  }`}>
                    {user.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td className="py-3 px-2">
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => onEdit?.(user)}
                      className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
                      title="Edit"
                    >
                      <FiEdit3 size={14} className="text-gray-500" />
                    </button>
                    <button
                      onClick={() => onToggleStatus?.(user.id, user.is_active)}
                      className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
                      title={user.is_active ? "Deactivate" : "Activate"}
                    >
                      {user.is_active ? (
                        <FiUserX size={14} className="text-amber-500" />
                      ) : (
                        <FiUserCheck size={14} className="text-emerald-500" />
                      )}
                    </button>
                    <button
                      onClick={() => onDelete?.(user.id)}
                      className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
                      title="Delete"
                    >
                      <FiTrash2 size={14} className="text-red-500" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ─── Content Moderation Queue ────────────────────────────────────────────────
const ModerationQueue = ({ items, onApprove, onReject }) => {
  if (!items.length) {
    return (
      <div className="card-base p-5">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <FiShield size={18} className="text-emerald-600" />
          Moderation Queue
        </h3>
        <EmptyState title="Queue is clear" subtitle="No items pending review." icon={FiCheck} />
      </div>
    )
  }

  return (
    <div className="card-base p-5">
      <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <FiShield size={18} className="text-emerald-600" />
        Moderation Queue ({items.length})
      </h3>
      <div className="space-y-3">
        {items.slice(0, 5).map((item) => (
          <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
            <div>
              <p className="text-sm font-medium text-gray-900">{item.title || item.name}</p>
              <p className="text-xs text-gray-500">{item.type} • {item.submitted_by}</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => onApprove?.(item.id)}
                className="p-2 bg-emerald-100 text-emerald-700 rounded-lg hover:bg-emerald-200 transition-colors"
                title="Approve"
              >
                <FiCheck size={16} />
              </button>
              <button
                onClick={() => onReject?.(item.id)}
                className="p-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
                title="Reject"
              >
                <FiX size={16} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Main Admin Dashboard ────────────────────────────────────────────────────
const AdminDashboard = () => {
  const { user, can } = useAuth()
  const { showToast } = useToast()
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [pendingPlaces, setPendingPlaces] = useState([])
  const [pendingImages, setPendingImages] = useState([])
  const [emergencies, setEmergencies] = useState([])
  const [activities, setActivities] = useState([])
  const [systemHealth, setSystemHealth] = useState({})

  // Fetch all data
  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const requests = [
        can("dashboard", "view") ? adminApi.getStats() : null,
        can("users", "view") ? adminApi.getUsers() : null,
        can("destinations", "view") ? adminApi.getPendingPlaces() : null,
        can("images", "view") ? adminApi.getPendingImages() : null,
        can("safety", "view") ? adminApi.getEmergencies() : null,
      ]
      const [statsRes, usersRes, placesRes, imagesRes, emergRes] =
        await Promise.allSettled(requests.map((r) => r || Promise.resolve(null)))

      if (statsRes.status === "fulfilled" && statsRes.value) setStats(statsRes.value.data)
      if (usersRes.status === "fulfilled" && usersRes.value) setUsers(usersRes.value.data)
      if (placesRes.status === "fulfilled" && placesRes.value) setPendingPlaces(placesRes.value.data)
      if (imagesRes.status === "fulfilled" && imagesRes.value) setPendingImages(imagesRes.value.data)
      if (emergRes.status === "fulfilled" && emergRes.value) setEmergencies(emergRes.value.data)

      // Simulated activities
      setActivities([
        { icon: FiUserCheck, text: "New user registered: john@example.com", time: "2 min ago", color: "#1B8A5A" },
        { icon: FiMapPin, text: "New place submitted: Pokhara Viewpoint", time: "15 min ago", color: "#0B3D91" },
        { icon: FiImage, text: "5 images pending review", time: "1 hour ago", color: "#F59E0B" },
        { icon: FiAlertTriangle, text: "Emergency alert resolved", time: "2 hours ago", color: "#DC143C" },
        { icon: FiDollarSign, text: "New booking: NPR 25,000", time: "3 hours ago", color: "#70B1AB" },
      ])

      // Simulated system health
      setSystemHealth({ api: "operational", db: "operational", cdn: "operational", email: "operational" })
    } catch (err) {
      console.error("Dashboard fetch error:", err)
    } finally {
      setLoading(false)
    }
  }, [can])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Chart data
  const visitorChartData = useMemo(() => ({
    labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    datasets: [{
      label: "Visitors",
      data: [1200, 1900, 3000, 5000, 2300, 4500],
      borderColor: CHART_COLORS[0],
      backgroundColor: "rgba(27,138,90,0.15)",
      tension: 0.4,
      fill: true,
    }],
  }), [])

  const destinationChartData = useMemo(() => ({
    labels: ["Kathmandu", "Pokhara", "Chitwan", "Lumbini", "Others"],
    datasets: [{
      data: [35, 25, 15, 10, 15],
      backgroundColor: CHART_COLORS,
    }],
  }), [])

  if (loading) return <Loader fullScreen text="Loading dashboard..." />

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
            <p className="text-sm text-gray-500">Welcome back, {user?.email}</p>
          </div>
          <button onClick={fetchData} className="btn-secondary flex items-center gap-2">
            <FiRefreshCw size={16} /> Refresh
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard icon={FiUsers} label="Total Users" value={stats?.totalUsers || users.length} change={12.5} positive color="#1B8A5A" />
          <StatCard icon={FiMapPin} label="Destinations" value={stats?.totalDestinations || 0} change={8.3} positive color="#0B3D91" />
          <StatCard icon={FiEye} label="Page Views" value={stats?.totalDestinationViews || "—"} change={-2.1} positive={false} color="#F59E0B" />
          <StatCard icon={FiAlertTriangle} label="Active Alerts" value={emergencies.filter((e) => e.status === "active").length} color="#DC143C" />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 card-base p-5">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <FiTrendingUp size={18} className="text-emerald-600" />
              Visitor Trends
            </h3>
            <div className="h-64">
              <Line data={visitorChartData} options={{ responsive: true, maintainAspectRatio: false }} />
            </div>
          </div>
          <div className="card-base p-5">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <FiPieChart size={18} className="text-emerald-600" />
              Top Destinations
            </h3>
            <div className="h-64">
              <Pie data={destinationChartData} options={{ responsive: true, maintainAspectRatio: false }} />
            </div>
          </div>
        </div>

        {/* Quick Actions & Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card-base p-5">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <FiCompass size={18} className="text-emerald-600" />
              Quick Actions
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <QuickAction icon={FiMapPin} label="Review Places" color="#1B8A5A" onClick={() => showToast("Opening place reviews...", "info")} />
              <QuickAction icon={FiImage} label="Verify Photos" color="#0B3D91" onClick={() => showToast("Opening photo verification...", "info")} />
              <QuickAction icon={FiUsers} label="Manage Users" color="#F59E0B" onClick={() => showToast("Opening user management...", "info")} />
              <QuickAction icon={FiAlertTriangle} label="View Alerts" color="#DC143C" onClick={() => showToast("Opening alerts...", "info")} />
            </div>
          </div>

          <div className="card-base p-5">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <FiClock size={18} className="text-emerald-600" />
              Recent Activity
            </h3>
            <div className="space-y-1">
              {activities.map((activity, i) => (
                <ActivityItem key={i} {...activity} />
              ))}
            </div>
          </div>
        </div>

        {/* System Health & Moderation */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SystemHealth health={systemHealth} />
          <ModerationQueue
            items={[...pendingPlaces, ...pendingImages]}
            onApprove={(id) => showToast("Item approved", "success")}
            onReject={(id) => showToast("Item rejected", "info")}
          />
        </div>

        {/* User Management */}
        <UserManagementTable
          users={users}
          onEdit={(u) => showToast(`Editing ${u.email}`, "info")}
          onDelete={(id) => showToast("User deleted", "success")}
          onToggleStatus={(id, status) => showToast(`User ${status ? "deactivated" : "activated"}`, "info")}
        />
      </div>
    </div>
  )
}

export default AdminDashboard
