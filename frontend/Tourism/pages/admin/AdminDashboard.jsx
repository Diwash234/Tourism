import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { FiUsers, FiMapPin, FiAlertTriangle, FiDollarSign, FiImage, FiCheckSquare, FiHome, FiClipboard, FiArrowRight } from "react-icons/fi"
import adminPanelApi from "../../api/adminPanelApi"
import Loader from "../../components/common/Loader"
import LineChartCard from "../../components/charts/LineChartCard"
import BarChartCard from "../../components/charts/BarChartCard"

// Same bug as BudgetCard: `bg-${accent}-50` is invisible to Tailwind's
// JIT content scanner because it's built at runtime, so the color never
// actually got generated into the CSS. Static map fixes it.
const STAT_ACCENTS = {
  primary: "bg-primary-50 text-primary-500",
  secondary: "bg-secondary-500/10 text-secondary-600",
  himalaya: "bg-himalaya-50 text-himalaya-500",
  forest: "bg-forest-50 text-forest-500",
  saffron: "bg-saffron-50 text-saffron-600",
  nepalred: "bg-nepalred-50 text-nepalred-500",
}

const StatCard = ({ icon: Icon, label, value, accent = "primary" }) => (
  <div className="card-base p-5 flex items-center gap-4">
    <div className={`p-3 rounded-xl ${STAT_ACCENTS[accent] || STAT_ACCENTS.primary}`}>
      <Icon size={22} />
    </div>
    <div>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  </div>
)

const ManagementCard = ({ icon: Icon, title, description, to, accent = "primary" }) => (
  <Link
    to={to}
    className="card-base p-5 flex items-start gap-4 hover:shadow-card transition-shadow group"
  >
    <div className={`p-3 rounded-xl shrink-0 ${STAT_ACCENTS[accent] || STAT_ACCENTS.primary}`}>
      <Icon size={20} />
    </div>
    <div className="flex-1 min-w-0">
      <h4 className="font-semibold flex items-center gap-1.5">
        {title}
        <FiArrowRight size={14} className="opacity-0 group-hover:opacity-100 transition-opacity" />
      </h4>
      <p className="text-sm text-gray-500 mt-0.5">{description}</p>
    </div>
  </Link>
)

const AdminDashboard = () => {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    adminPanelApi
      .getDashboardStats()
      .then(({ data }) => setStats(data))
      .catch(() => setStats(null))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Loader fullScreen={false} />

  const monthlyLabels = stats?.monthlyVisitors?.map((m) => m.month) || ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
  const monthlyData = stats?.monthlyVisitors?.map((m) => m.count) || [120, 190, 300, 250, 400, 380]
  const categoryLabels = stats?.destinationsByCategory?.map((c) => c.category) || ["Mountains", "Lakes", "Heritage", "Adventure"]
  const categoryData = stats?.destinationsByCategory?.map((c) => c.count) || [12, 8, 15, 6]

  return (
    <div className="container-app py-10 space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Admin Dashboard</h1>
        <p className="text-gray-500 text-sm">Platform-wide overview and management.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard icon={FiUsers} label="Total Users" value={stats?.totalUsers ?? "--"} accent="primary" />
        <StatCard icon={FiMapPin} label="Destinations" value={stats?.totalDestinations ?? "--"} accent="secondary" />
        <StatCard icon={FiAlertTriangle} label="Active Alerts" value={stats?.activeAlerts ?? "--"} accent="primary" />
        <StatCard icon={FiDollarSign} label="Avg. Budget" value={`$${stats?.avgBudget ?? "--"}`} accent="secondary" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LineChartCard title="Monthly Visitors" labels={monthlyLabels} data={monthlyData} label="Visitors" />
        <BarChartCard title="Destinations by Category" labels={categoryLabels} data={categoryData} label="Count" />
      </div>

      {/* FIXED: this used to be a static paragraph of instructions
          pointing at endpoints that don't even exist (/admin/users,
          /admin/destinations, /admin/alerts -- the app's own admin
          routes live at /panel/* since /admin had to be freed up for
          Django's real admin panel, see App.jsx/vite.config.js). It
          said "extend this dashboard... as the backend endpoints are
          finalized" -- but every one of these pages already exists
          and works; this dashboard just never linked to any of them. */}
      <div>
        <h3 className="font-semibold mb-4">Quick Management</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <ManagementCard
            icon={FiImage}
            title="Destination Media"
            description="Add real photos, review galleries, check history."
            to="/panel/media"
            accent="himalaya"
          />
          <ManagementCard
            icon={FiCheckSquare}
            title="Place Approvals"
            description="Review tourist-submitted destinations."
            to="/panel/place-approvals"
            accent="forest"
          />
          <ManagementCard
            icon={FiUsers}
            title="User Management"
            description="View and manage user accounts and roles."
            to="/panel/users"
            accent="primary"
          />
          <ManagementCard
            icon={FiHome}
            title="Hotel Assignments"
            description="Assign hotels to admins for management."
            to="/panel/hotel-assignments"
            accent="secondary"
          />
          <ManagementCard
            icon={FiClipboard}
            title="Admin Tasks"
            description="Track and assign internal admin tasks."
            to="/panel/tasks"
            accent="saffron"
          />
        </div>
      </div>

      <div className="card-base p-5 bg-gray-50 border border-gray-100">
        <p className="text-sm text-gray-500">
          Need something not listed above — raw editing of bookings, reviews, translations, or any other model?
          Django's full admin panel covers every model automatically:{" "}
          <a
            href="/admin/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-himalaya-600 font-medium hover:underline"
          >
            open Django Admin
          </a>
          {" "}(separate login, not the pages above).
        </p>
      </div>
    </div>
  )
}

export default AdminDashboard