import { useCallback, useEffect, useState } from "react"
import { FiBell, FiCheck, FiMail, FiRefreshCw, FiTrash2 } from "react-icons/fi"
import userApi from "../api/userApi"
import PageHeader from "../components/common/PageHeader"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import useToast from "../hooks/useToast"
import CMSPageIntro from "../components/cms/CMSPageIntro"

export default function Notifications() {
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState("")
  const { showToast } = useToast()

  const load = useCallback(() => {
    setLoading(true)
    setLoadError("")
    userApi.getNotifications()
      .then(({ data }) => setNotifications(data.results || data || []))
      .catch((err) => {
        setNotifications([])
        setLoadError(err?.response?.data?.detail || err?.message || "Could not load notifications.")
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  // Every mutation reports failure honestly — no silent optimistic updates.
  const toggle = async (item) => {
    try {
      const { data } = item.is_read
        ? await userApi.markNotificationUnread(item.id)
        : await userApi.markNotificationRead(item.id)
      setNotifications((rows) => rows.map((row) => (row.id === item.id ? data : row)))
    } catch (err) {
      showToast(err?.response?.data?.detail || "Could not update this notification.", "error")
    }
  }

  const remove = async (item) => {
    try {
      await userApi.deleteNotification(item.id)
      setNotifications((rows) => rows.filter((row) => row.id !== item.id))
    } catch (err) {
      showToast(err?.response?.data?.detail || "Could not delete this notification.", "error")
    }
  }

  const all = async (read) => {
    try {
      if (read) await userApi.markAllNotificationsRead()
      else await userApi.markAllNotificationsUnread()
      setNotifications((rows) => rows.map((row) => ({ ...row, is_read: read })))
    } catch (err) {
      showToast(err?.response?.data?.detail || "Could not update notifications.", "error")
    }
  }

  const unread = notifications.filter((item) => !item.is_read).length

  return (
    <div className="theme-amber-alt space-y-5">
      <CMSPageIntro pageKey="notifications" />
      <PageHeader
        title="Notifications"
        subtitle={`${unread} unread · delivery status is shown honestly for each channel.`}
        icon={FiBell}
        actions={
          <div className="flex flex-wrap gap-2">
            <button onClick={() => all(true)} className="bg-white text-amber-700 text-xs font-bold px-3.5 py-2 rounded-xl hover:bg-gray-100 flex items-center gap-1.5">
              <FiCheck /> Mark all read
            </button>
            <button onClick={() => all(false)} className="bg-white text-amber-700 text-xs font-bold px-3.5 py-2 rounded-xl hover:bg-gray-100 flex items-center gap-1.5">
              <FiMail /> Mark all unread
            </button>
            <button onClick={load} className="bg-white text-amber-700 p-2 rounded-xl hover:bg-gray-100" aria-label="Refresh notifications">
              <FiRefreshCw className={loading ? "animate-spin" : ""} />
            </button>
          </div>
        }
      />

      {loading ? (
        <Loader />
      ) : loadError ? (
        <div className="card-base p-6 text-center">
          <p className="text-sm text-rose-600 mb-3">{loadError}</p>
          <button onClick={load} className="px-4 py-2 bg-secondary-500 text-white rounded-xl text-sm font-bold">Retry</button>
        </div>
      ) : notifications.length ? (
        <div className="space-y-2">
          {notifications.map((item) => (
            <article key={item.id} className={`rounded-2xl border p-4 flex gap-3 ${item.is_read ? "bg-white border-gray-200" : "bg-amber-50 border-amber-300"}`}>
              <button onClick={() => toggle(item)} className="flex-1 text-left" aria-label={item.is_read ? "Mark unread" : "Mark read"}>
                <div className="flex flex-wrap gap-2 items-center">
                  <b className="text-gray-900">{item.title}</b>
                  <span className="text-[10px] uppercase rounded-full bg-gray-100 px-2 py-0.5">{item.category}</span>
                  <span className={`text-[10px] rounded-full px-2 py-0.5 ${item.delivery_status === "sent" ? "bg-emerald-100 text-emerald-700" : item.delivery_status === "failed" ? "bg-rose-100 text-rose-700" : "bg-sky-100 text-sky-700"}`}>
                    {item.channel} · {item.delivery_status}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">{item.message}</p>
                <p className="text-xs text-gray-400 mt-2">{new Date(item.created_at).toLocaleString()}</p>
              </button>
              <button onClick={() => remove(item)} className="self-start p-2 text-rose-600 hover:bg-rose-50 rounded-lg" aria-label="Delete notification">
                <FiTrash2 />
              </button>
            </article>
          ))}
        </div>
      ) : (
        <EmptyState title="You are all caught up" subtitle="New notifications will appear here." />
      )}
    </div>
  )
}
