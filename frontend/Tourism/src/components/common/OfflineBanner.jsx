import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { FiWifiOff } from "react-icons/fi"

// Shown while the browser reports no connection. Points to the pages that
// keep working offline (saved hotlines and entry requirements).
export default function OfflineBanner() {
  const [offline, setOffline] = useState(() => typeof navigator !== "undefined" && navigator.onLine === false)
  useEffect(() => {
    const on = () => setOffline(false)
    const off = () => setOffline(true)
    window.addEventListener("online", on)
    window.addEventListener("offline", off)
    return () => { window.removeEventListener("online", on); window.removeEventListener("offline", off) }
  }, [])
  if (!offline) return null
  return (
    <div role="status" aria-live="polite"
      className="fixed inset-x-0 top-16 z-[55] flex flex-wrap items-center justify-center gap-x-3 gap-y-1 border-b border-amber-300 bg-amber-100 px-4 py-2 text-center text-sm text-amber-950">
      <FiWifiOff aria-hidden="true" />
      <span>You're offline. Live data can't load right now.</span>
      <Link to="/emergency" className="font-semibold underline">Emergency numbers</Link>
      <Link to="/before-you-travel" className="font-semibold underline">Permits &amp; fees</Link>
    </div>
  )
}
