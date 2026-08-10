import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { FiUsers, FiUserX, FiUserCheck, FiAlertTriangle } from "react-icons/fi"
import adminPanelApi from "../../api/adminPanelApi"
import Loader from "../../components/common/Loader"
import EmptyState from "../../components/common/EmptyState"
import useToast from "../../hooks/useToast"
import useAuth from "../../hooks/useAuth"
import { USER_ROLES } from "../../utils/constants"

/**
 * UserManagement — DOES NOT WORK YET. There is no user-list or
 * role-change endpoint on the backend at all (checked every admin-
 * related file directly: admin_panel/urls.py only has hotel-assignments,
 * tasks, my-hotels, dashboard-summary). This page is built against the
 * exact REST contract documented in BACKEND_IMPROVEMENTS.md — it will
 * show a clear "backend endpoint doesn't exist yet" error until that's
 * added, rather than fail silently or show fake data.
 */
const UserManagement = () => {
  const { user: currentUser } = useAuth()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [backendMissing, setBackendMissing] = useState(false)
  const [updatingId, setUpdatingId] = useState(null)
  const { showToast } = useToast()

  const load = () => {
    setLoading(true)
    setBackendMissing(false)
    adminPanelApi
      .getUsers()
      .then(({ data }) => setUsers(data.results || data || []))
      .catch((err) => {
        if (err.response?.status === 404) {
          setBackendMissing(true)
        } else {
          showToast("Could not load users", "error")
        }
      })
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const handleRoleChange = async (userId, role) => {
    setUpdatingId(userId)
    try {
      await adminPanelApi.updateUserRole(userId, role)
      setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, role } : u)))
      showToast("Role updated", "success")
    } catch (err) {
      showToast(err.response?.data?.detail || "Could not update role", "error")
    } finally {
      setUpdatingId(null)
    }
  }

  const handleToggleActive = async (u) => {
    setUpdatingId(u.id)
    try {
      if (u.is_active) {
        await adminPanelApi.deactivateUser(u.id)
      } else {
        await adminPanelApi.activateUser(u.id)
      }
      setUsers((prev) => prev.map((x) => (x.id === u.id ? { ...x, is_active: !x.is_active } : x)))
      showToast(u.is_active ? "User deactivated" : "User activated", "success")
    } catch {
      showToast("Could not update user status", "error")
    } finally {
      setUpdatingId(null)
    }
  }

  if (loading) return <Loader />

  if (backendMissing) {
    return (
      <div className="container-app py-10">
        <h1 className="section-title flex items-center gap-2"><FiUsers className="text-himalaya-500" /> User Management</h1>
        <div className="card-base p-8 text-center border border-dashed border-saffron-200">
          <FiAlertTriangle className="mx-auto text-saffron-500 mb-3" size={32} />
          <h2 className="font-semibold mb-2">Backend endpoint not built yet</h2>
          <p className="text-sm text-gray-500 max-w-md mx-auto">
            This page is fully built and ready — it's calling <code className="bg-gray-100 px-1.5 py-0.5 rounded">GET /admin-panel/users/</code>,
            which returned a 404. See <code className="bg-gray-100 px-1.5 py-0.5 rounded">BACKEND_IMPROVEMENTS.md</code> for
            the exact Django code needed.
          </p>
        </div>
      </div>
    )
  }

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="container-app py-10 fade-in">
      <h1 className="section-title flex items-center gap-2"><FiUsers className="text-himalaya-500" /> User Management</h1>
      <p className="text-gray-500 text-sm mb-6">
        Assign roles (create sub-admins by promoting a user to an admin-tier role), or activate/deactivate accounts.
      </p>

      {users.length ? (
        <div className="card-base overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-gray-500">
              <tr>
                <th className="p-3">User</th>
                <th className="p-3">Role</th>
                <th className="p-3">Status</th>
                <th className="p-3"></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t border-gray-100">
                  <td className="p-3">
                    <p className="font-medium">{u.first_name} {u.last_name}</p>
                    <p className="text-xs text-gray-400">{u.email}</p>
                  </td>
                  <td className="p-3">
                    <select
                      className="input-field py-1.5 text-xs"
                      value={u.role}
                      disabled={u.id === currentUser?.id || updatingId === u.id}
                      onChange={(e) => handleRoleChange(u.id, e.target.value)}
                    >
                      {USER_ROLES.map((r) => (
                        <option key={r.value} value={r.value}>{r.label}</option>
                      ))}
                    </select>
                  </td>
                  <td className="p-3">
                    <span className={u.is_active ? "badge-risk-low" : "badge-risk-high"}>
                      {u.is_active ? "Active" : "Deactivated"}
                    </span>
                  </td>
                  <td className="p-3 text-right">
                    <button
                      onClick={() => handleToggleActive(u)}
                      disabled={u.id === currentUser?.id || updatingId === u.id}
                      className="text-gray-400 hover:text-nepalred-500 disabled:opacity-30"
                      title={u.is_active ? "Deactivate" : "Activate"}
                    >
                      {u.is_active ? <FiUserX size={16} /> : <FiUserCheck size={16} />}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState title="No users found" subtitle="" />
      )}
    </motion.div>
  )
}

export default UserManagement