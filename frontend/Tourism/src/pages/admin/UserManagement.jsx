import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { FiUsers, FiUserX, FiUserCheck, FiEye, FiHeart, FiClock, FiDollarSign, FiStar, FiHome } from "react-icons/fi"
import adminPanelApi from "../../api/adminPanelApi"
import Loader from "../../components/common/Loader"
import EmptyState from "../../components/common/EmptyState"
import useToast from "../../hooks/useToast"
import useAuth from "../../hooks/useAuth"
import { USER_ROLES } from "../../utils/constants"

/**
 * UserManagement — user list/role management, plus a "View Account"
 * panel showing everything a user has done across the site: bookings,
 * reviews, favorites, budget entries, visit history. Confirmed against
 * the real backend that these were previously invisible to admins
 * entirely -- Favorite/VisitHistory/Budget viewsets hard-scoped to
 * request.user with no staff override at all; fixed there to accept
 * ?user=<id> for staff, which is what powers this panel.
 */
const UserManagement = () => {
  const { user: currentUser } = useAuth()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [updatingId, setUpdatingId] = useState(null)
  const { showToast } = useToast()

  // ADDED -- "View Account" panel state.
  const [viewingUser, setViewingUser] = useState(null)
  const [accountData, setAccountData] = useState(null)
  const [loadingAccount, setLoadingAccount] = useState(false)

  const load = () => {
    setLoading(true)
    adminPanelApi
      .getUsers()
      .then(({ data }) => setUsers(data.results || data || []))
      .catch(() => showToast("Could not load users", "error"))
      .finally(() => setLoading(false))
  }

  // eslint-disable-next-line react-hooks/set-state-in-effect -- initial fetch kicks off loading state once on mount
  useEffect(load, [])

  const openAccount = (u) => {
    setViewingUser(u)
    setLoadingAccount(true)
    Promise.all([
      adminPanelApi.getUserBookings(u.id).catch(() => ({ data: { results: [] } })),
      adminPanelApi.getUserReviews(u.id).catch(() => ({ data: { results: [] } })),
      adminPanelApi.getUserFavorites(u.id).catch(() => ({ data: { results: [] } })),
      adminPanelApi.getUserBudgets(u.id).catch(() => ({ data: { results: [] } })),
      adminPanelApi.getUserVisitHistory(u.id).catch(() => ({ data: { results: [] } })),
    ])
      .then(([bookings, reviews, favorites, budgets, history]) => {
        setAccountData({
          bookings: bookings.data.results || bookings.data || [],
          reviews: reviews.data.results || reviews.data || [],
          favorites: favorites.data.results || favorites.data || [],
          budgets: budgets.data.results || budgets.data || [],
          history: history.data.results || history.data || [],
        })
      })
      .finally(() => setLoadingAccount(false))
  }

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
                      onClick={() => openAccount(u)}
                      className="text-gray-400 hover:text-himalaya-500 mr-3"
                      title="View account activity"
                    >
                      <FiEye size={16} />
                    </button>
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

      {/* ADDED -- account activity panel: everything a user has done
          across the site, in one place, that an admin previously had
          no way to see at all. */}
      <AnimatePresence>
        {viewingUser && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setViewingUser(null)}
            className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4"
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-lg font-semibold">{viewingUser.first_name} {viewingUser.last_name}</h2>
                  <p className="text-sm text-gray-400">{viewingUser.email}</p>
                </div>
                <button onClick={() => setViewingUser(null)} className="text-gray-400 hover:text-gray-600">✕</button>
              </div>

              {loadingAccount ? (
                <Loader />
              ) : (
                <div className="space-y-6">
                  <section>
                    <h3 className="text-sm font-semibold flex items-center gap-2 mb-2">
                      <FiHome className="text-himalaya-500" /> Bookings ({accountData?.bookings.length || 0})
                    </h3>
                    {accountData?.bookings.length ? (
                      <ul className="text-sm space-y-1">
                        {accountData.bookings.map((b) => (
                          <li key={b.id} className="flex justify-between text-gray-600">
                            <span>{b.hotel_name || `Hotel #${b.hotel}`}</span>
                            <span className="text-xs text-gray-400">{b.status}</span>
                          </li>
                        ))}
                      </ul>
                    ) : <p className="text-xs text-gray-400">No bookings.</p>}
                  </section>

                  <section>
                    <h3 className="text-sm font-semibold flex items-center gap-2 mb-2">
                      <FiStar className="text-himalaya-500" /> Reviews ({accountData?.reviews.length || 0})
                    </h3>
                    {accountData?.reviews.length ? (
                      <ul className="text-sm space-y-1">
                        {accountData.reviews.map((r) => (
                          <li key={r.id} className="text-gray-600">
                            <span className="font-medium">{r.destination_name || `Destination #${r.destination}`}:</span>{" "}
                            {r.comment}
                          </li>
                        ))}
                      </ul>
                    ) : <p className="text-xs text-gray-400">No reviews.</p>}
                  </section>

                  <section>
                    <h3 className="text-sm font-semibold flex items-center gap-2 mb-2">
                      <FiHeart className="text-himalaya-500" /> Favorites ({accountData?.favorites.length || 0})
                    </h3>
                    {accountData?.favorites.length ? (
                      <ul className="text-sm space-y-1 text-gray-600">
                        {accountData.favorites.map((f) => (
                          <li key={f.id}>{f.destination_detail?.name || `Destination #${f.destination}`}</li>
                        ))}
                      </ul>
                    ) : <p className="text-xs text-gray-400">No favorites.</p>}
                  </section>

                  <section>
                    <h3 className="text-sm font-semibold flex items-center gap-2 mb-2">
                      <FiDollarSign className="text-himalaya-500" /> Budget Entries ({accountData?.budgets.length || 0})
                    </h3>
                    {accountData?.budgets.length ? (
                      <ul className="text-sm space-y-1 text-gray-600">
                        {accountData.budgets.map((b) => (
                          <li key={b.id} className="flex justify-between">
                            <span>{b.destination_name || `Destination #${b.destination}`}</span>
                            <span>NPR {b.amount}</span>
                          </li>
                        ))}
                      </ul>
                    ) : <p className="text-xs text-gray-400">No budget entries.</p>}
                  </section>

                  <section>
                    <h3 className="text-sm font-semibold flex items-center gap-2 mb-2">
                      <FiClock className="text-himalaya-500" /> Visit History ({accountData?.history.length || 0})
                    </h3>
                    {accountData?.history.length ? (
                      <ul className="text-sm space-y-1 text-gray-600">
                        {accountData.history.map((h) => (
                          <li key={h.id}>{h.destination_name || `Destination #${h.destination}`}</li>
                        ))}
                      </ul>
                    ) : <p className="text-xs text-gray-400">No visit history.</p>}
                  </section>
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default UserManagement