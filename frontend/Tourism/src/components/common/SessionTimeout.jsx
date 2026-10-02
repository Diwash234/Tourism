import { useState, useEffect, useCallback, useRef } from "react"
import { FiClock, FiX } from "react-icons/fi"

const WARNING_BEFORE = 60 // seconds before timeout to show warning
const CHECK_INTERVAL = 5000 // check every 5 seconds

/**
 * Session timeout warning — shows a countdown when the user is about
 * to be logged out due to inactivity. Resets on user activity.
 */
export default function SessionTimeout({ onTimeout, timeoutMinutes = 30 }) {
  const [timeLeft, setTimeLeft] = useState(timeoutMinutes * 60)
  const [warning, setWarning] = useState(false)
  // Lazy initializer keeps render pure; the mount timestamp is copied into the
  // ref below (ref initializers cannot be lazy).
  const [lastActivityTime] = useState(() => Date.now())
  const lastActivity = useRef(lastActivityTime)

  const resetTimer = useCallback(() => {
    lastActivity.current = Date.now()
    setTimeLeft(timeoutMinutes * 60)
    setWarning(false)
  }, [timeoutMinutes])

  useEffect(() => {
    const events = ["mousedown", "keydown", "scroll", "touchstart"]
    const onActivity = () => { lastActivity.current = Date.now() }
    events.forEach(e => window.addEventListener(e, onActivity, { passive: true }))
    return () => events.forEach(e => window.removeEventListener(e, onActivity))
  }, [])

  useEffect(() => {
    const interval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - lastActivity.current) / 1000)
      const remaining = Math.max(0, timeoutMinutes * 60 - elapsed)
      setTimeLeft(remaining)
      if (remaining <= WARNING_BEFORE && remaining > 0) {
        setWarning(true)
      }
      if (remaining === 0) {
        onTimeout?.()
      }
    }, CHECK_INTERVAL)
    return () => clearInterval(interval)
  }, [timeoutMinutes, onTimeout])

  if (!warning) return null

  const minutes = Math.floor(timeLeft / 60)
  const seconds = timeLeft % 60

  return (
    <div className="fixed bottom-4 left-4 z-[90] flex items-center gap-3 rounded-xl border border-amber-200 dark:border-amber-900 bg-amber-50 dark:bg-amber-950/50 px-4 py-3 shadow-lg" role="alert">
      <FiClock size={18} className="text-amber-600 dark:text-amber-400 shrink-0" />
      <div>
        <p className="text-sm font-semibold text-amber-800 dark:text-amber-200">Session expiring soon</p>
        <p className="text-xs text-amber-600 dark:text-amber-400">
          You'll be logged out in {minutes}:{seconds.toString().padStart(2, "0")} due to inactivity
        </p>
      </div>
      <button
        type="button"
        onClick={resetTimer}
        className="ml-2 px-3 py-1.5 text-xs font-semibold rounded-lg bg-amber-600 text-white hover:bg-amber-700 transition-colors"
      >
        Stay logged in
      </button>
      <button
        type="button"
        onClick={() => setWarning(false)}
        className="p-1 rounded text-amber-500 hover:text-amber-700"
        aria-label="Dismiss"
      >
        <FiX size={14} />
      </button>
    </div>
  )
}
