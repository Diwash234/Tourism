import { useEffect, useState } from "react"
import { FiHome, FiClipboard, FiClock, FiAlertTriangle } from "react-icons/fi"
import adminPanelApi from "../../api/adminPanelApi"
import Loader from "../../components/common/Loader"
import useAuth from "../../hooks/useAuth"

const StatCard = ({ icon: Icon, label, value, accent }) => (
  <div className="card-base p-5 flex items-center justify-between">
    <div>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-3xl font-bold mt-1">{value}</p>
    </div>
    <Icon size={28} className={accent || "text-primary-500"} />
  </div>
)

const AdminDashboard = () => {
  const { user } = useAuth()
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    adminPanelApi
      .getDashboardSummary()
      .then(({ data }) => setSummary(data))
      .catch(() => setSummary(null))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Loader />
  if (!summary) return <p className="text-gray-500">Could not load dashboard. Are you an admin?</p>

  return (
    <div className="container-app py-10">
      <h1 className="text-2xl font-bold mb-1">
        {summary.is_super_admin ? "Super Admin Dashboard" : "Admin Dashboard"}
      </h1>
      <p className="text-gray-500 text-sm mb-6">
        {summary.is_super_admin
          ? "Platform-wide overview across all hotels and staff."
          : `Welcome back, ${user?.first_name || user?.email}. Here's what's assigned to you.`}
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard icon={FiHome} label={summary.is_super_admin ? "Total Hotels" : "My Hotels"} value={summary.assigned_hotel_count} />
        <StatCard icon={FiClipboard} label="Pending Tasks" value={summary.pending_tasks} accent="text-yellow-600" />
        <StatCard icon={FiClock} label="In Progress" value={summary.in_progress_tasks} accent="text-blue-500" />
        <StatCard icon={FiAlertTriangle} label="Overdue" value={summary.overdue_tasks} accent="text-red-500" />
      </div>
    </div>
  )
}

export default AdminDashboard