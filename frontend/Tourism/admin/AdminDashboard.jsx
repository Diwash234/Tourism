import { useEffect, useState } from "react"
import { FiUsers, FiMapPin, FiAlertTriangle, FiDollarSign } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import Loader from "../../components/common/Loader"
import LineChartCard from "../../components/charts/LineChartCard"
import BarChartCard from "../../components/charts/BarChartCard"

const StatCard = ({ icon: Icon, label, value, accent }) => (
  <div className="card-base p-5 flex items-center gap-4">
    <div className={`p-3 rounded-xl bg-${accent}-50 text-${accent}-500`}>
      <Icon size={22} />
    </div>
    <div>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  </div>
)

const AdminDashboard = () => {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    adminApi
      .getStats()
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

      <div className="card-base p-6">
        <h3 className="font-semibold mb-4">Quick Management</h3>
        <p className="text-sm text-gray-500">
          Manage users, destinations, and alerts via the admin API endpoints
          (<code>/admin/users</code>, <code>/admin/destinations</code>, <code>/admin/alerts</code>).
          Extend this dashboard with data tables and CRUD forms as the backend endpoints are finalized.
        </p>
      </div>
    </div>
  )
}

export default AdminDashboard