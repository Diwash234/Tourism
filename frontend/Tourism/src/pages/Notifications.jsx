import { useEffect, useState } from "react"
import userApi from "../api/userApi"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import { FiBell } from "react-icons/fi"
import { formatDate } from "../utils/helpers"

const Notifications = () => {
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    userApi
      .getNotifications()
      .then(({ data }) => setNotifications(data.items || data || []))
      .catch(() => setNotifications([]))
      .finally(() => setLoading(false))
  }, [])

  const markRead = async (id) => {
    try {
      await userApi.markNotificationRead(id)
      setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)))
    } catch {
      /* noop */
    }
  }

  if (loading) return <Loader />

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Notifications</h1>
      {notifications.length ? (
        <div className="space-y-3">
          {notifications.map((n) => (
            <button
              key={n.id}
              onClick={() => markRead(n.id)}
              className={`w-full text-left card-base p-4 flex items-start gap-3 ${n.read ? "opacity-60" : ""}`}
            >
              <FiBell className="text-primary-500 mt-1" />
              <div>
                <p className="font-medium text-sm">{n.title}</p>
                <p className="text-sm text-gray-500">{n.message}</p>
                <p className="text-xs text-gray-400 mt-1">{formatDate(n.createdAt)}</p>
              </div>
            </button>
          ))}
        </div>
      ) : (
        <EmptyState title="You are all caught up" subtitle="New notifications will appear here." />
      )}
    </div>
  )
}

export default Notifications