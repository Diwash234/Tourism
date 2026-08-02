import { useEffect, useState } from "react"
import userApi from "../api/userApi"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import TravelTimeline from "../components/cards/TravelTimeline"
import { formatDate } from "../utils/helpers"

const Notifications = () => {
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    userApi
      .getNotifications()
      // FIXED (kept from before): backend returns `{ results: [...] }`
      // (paginated); `.items` doesn't exist.
      .then(({ data }) =>
        setNotifications(data.results || data.items || data || [])
      )
      .catch(() => setNotifications([]))
      .finally(() => setLoading(false))
  }, [])

  const markRead = async (id) => {
    try {
      await userApi.markNotificationRead(id)

      setNotifications((prev) =>
        prev.map((n) =>
          n.id === id ? { ...n, is_read: true } : n
        )
      )
    } catch {
      /* noop */
    }
  }

  if (loading) return <Loader />

  // Map backend Notification model into TravelTimeline format.
  const timelineItems = notifications.map((n) => ({
    id: n.id,
    type: n.related_alert ? "alert" : "notification",
    title: n.title,
    description: n.message,
    time: formatDate(n.created_at),
    dimmed: n.is_read,
    _raw: n,
  }))

  return (
    <div className="theme-amber-alt">
      <h1 className="section-title">
        Notifications
      </h1>

      {notifications.length ? (
        <TravelTimeline
          items={timelineItems}
          onItemClick={(item) => markRead(item.id)}
        />
      ) : (
        <EmptyState
          title="You are all caught up"
          subtitle="New notifications will appear here."
        />
      )}
    </div>
  )
}

export default Notifications