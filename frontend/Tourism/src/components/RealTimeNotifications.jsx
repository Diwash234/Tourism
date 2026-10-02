import { useState, useEffect, useCallback } from 'react'
import { FiBell, FiX, FiCheck, FiTrash2 } from 'react-icons/fi'
import useAuth from '../hooks/useAuth'

const RealTimeNotifications = () => {
  const { user } = useAuth()
  const [notifications, setNotifications] = useState([])
  const [isOpen, setIsOpen] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)

  const fetchNotifications = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/notifications/', {
        headers: { Authorization: `Bearer ${localStorage.getItem('access')}` }
      })
      if (response.ok) {
        const data = await response.json()
        setNotifications(data.results || [])
        setUnreadCount((data.results || []).filter(n => !n.is_read).length)
      }
    } catch (err) {
      console.error('Failed to fetch notifications:', err)
    }
  }, [])

  useEffect(() => {
    if (!user) return undefined
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => fetchNotifications(), 0)
    const interval = setInterval(fetchNotifications, 30000)
    return () => {
      clearTimeout(t)
      clearInterval(interval)
    }
  }, [user, fetchNotifications])

  const markAsRead = async (id) => {
    try {
      await fetch(`/api/v1/notifications/${id}/`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ is_read: true })
      })
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n))
      setUnreadCount(prev => Math.max(0, prev - 1))
    } catch (err) {
      console.error('Failed to mark as read:', err)
    }
  }

  const markAllAsRead = async () => {
    try {
      await fetch('/api/v1/notifications/mark_all_read/', {
        method: 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('access')}` }
      })
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
      setUnreadCount(0)
    } catch (err) {
      console.error('Failed to mark all as read:', err)
    }
  }

  const deleteNotification = async (id) => {
    try {
      await fetch(`/api/v1/notifications/${id}/`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${localStorage.getItem('access')}` }
      })
      setNotifications(prev => prev.filter(n => n.id !== id))
    } catch (err) {
      console.error('Failed to delete notification:', err)
    }
  }

  if (!user) return null

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        aria-label="Notifications"
      >
        <FiBell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-900 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 z-50">
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold">Notifications</h3>
            <div className="flex gap-2">
              <button onClick={markAllAsRead} className="text-xs text-emerald-600 hover:text-emerald-700">
                Mark all read
              </button>
              <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-gray-600">
                <FiX className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <FiBell className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No notifications</p>
              </div>
            ) : (
              notifications.map(notification => (
                <div
                  key={notification.id}
                  className={`p-4 border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 ${
                    !notification.is_read ? 'bg-emerald-50/50 dark:bg-emerald-900/10' : ''
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-medium text-sm">{notification.title}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {notification.message}
                      </p>
                      <p className="text-xs text-gray-400 mt-2">
                        {new Date(notification.created_at).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex gap-1 ml-2">
                      {!notification.is_read && (
                        <button
                          onClick={() => markAsRead(notification.id)}
                          className="p-1 text-emerald-600 hover:bg-emerald-100 rounded"
                          title="Mark as read"
                        >
                          <FiCheck className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => deleteNotification(notification.id)}
                        className="p-1 text-red-500 hover:bg-red-100 rounded"
                        title="Delete"
                      >
                        <FiTrash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default RealTimeNotifications
