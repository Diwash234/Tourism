import { useState, useEffect, useCallback, useRef } from "react"
import {
  FiActivity,
  FiDatabase,
  FiHardDrive,
  FiImage,
  FiRefreshCw,
  FiCheckCircle,
  FiXCircle,
  FiClock,
  FiServer,
} from "react-icons/fi"
import axiosClient from "../api/axiosClient"

const REFRESH_INTERVAL = 30 * 1000 // 30 seconds

/**
 * System health check component showing database, cache, and static file status.
 * Auto-refreshes every 30 seconds.
 */
const HealthCheck = () => {
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastChecked, setLastChecked] = useState(null)
  const [refreshing, setRefreshing] = useState(false)
  const intervalRef = useRef(null)

  const fetchHealth = useCallback(async (isManual = false) => {
    if (isManual) setRefreshing(true)
    setError(null)
    try {
      const { data } = await axiosClient.get("/health/")
      setHealth(data)
      setLastChecked(new Date())
    } catch (err) {
      setError(
        err?.response?.data?.message || "Unable to check system health. Please try again later."
      )
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => fetchHealth(), 0)
    intervalRef.current = setInterval(() => fetchHealth(), REFRESH_INTERVAL)
    return () => {
      clearTimeout(t)
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [fetchHealth])

  const getStatusIcon = (status) => {
    if (status === "ok" || status === "healthy" || status === true) {
      return <FiCheckCircle size={16} className="text-green-600" />
    }
    if (status === "degraded") {
      return <FiClock size={16} className="text-amber-600" />
    }
    return <FiXCircle size={16} className="text-red-600" />
  }

  const getStatusColor = (status) => {
    if (status === "ok" || status === "healthy" || status === true) return "text-green-600"
    if (status === "degraded") return "text-amber-600"
    return "text-red-600"
  }

  const getOverallStatus = () => {
    if (!health) return "unknown"
    const checks = health.checks || {}
    const values = Object.values(checks)
    if (values.some((v) => v.status === "error" || v.status === false)) return "error"
    if (values.some((v) => v.status === "degraded")) return "degraded"
    if (values.every((v) => v.status === "ok" || v.status === "healthy" || v.status === true)) return "ok"
    return "unknown"
  }

  const overallStatus = getOverallStatus()

  const checks = [
    { key: "database", label: "Database", icon: FiDatabase },
    { key: "cache", label: "Cache", icon: FiServer },
    { key: "static_files", label: "Static Files", icon: FiImage },
    { key: "storage", label: "Storage", icon: FiHardDrive },
  ]

  if (loading && !health) {
    return (
      <div className="ny-card p-5" role="status" aria-label="Checking system health">
        <div className="ny-skeleton h-6 w-1/3 mb-4" />
        <div className="grid grid-cols-2 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="p-3 rounded-xl border border-ny-border">
              <div className="ny-skeleton h-5 w-1/2 mb-2" />
              <div className="ny-skeleton h-4 w-1/3" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error && !health) {
    return (
      <div className="ny-card p-5" role="alert">
        <div className="flex items-center gap-2 text-ny-danger mb-3">
          <FiXCircle size={18} />
          <span className="font-semibold text-sm">Health check failed</span>
        </div>
        <p className="text-sm text-ny-text-secondary mb-3">{error}</p>
        <button onClick={() => fetchHealth(true)} className="ny-btn ny-btn-secondary ny-btn-sm" type="button">
          <FiRefreshCw size={14} /> Retry
        </button>
      </div>
    )
  }

  return (
    <div className="ny-card p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-ny-text flex items-center gap-2">
          <FiActivity size={18} className="text-ny-green" />
          System Health
        </h3>
        <div className="flex items-center gap-2">
          {lastChecked && (
            <span className="text-xs text-ny-text-muted flex items-center gap-1">
              <FiClock size={10} />
              {lastChecked.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
            </span>
          )}
          <button
            onClick={() => fetchHealth(true)}
            disabled={refreshing}
            className="ny-btn ny-btn-ghost ny-btn-sm"
            type="button"
            aria-label="Refresh health check"
          >
            <FiRefreshCw size={14} className={refreshing ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {/* Overall status */}
      <div className={`flex items-center gap-2 p-3 rounded-xl mb-4 ${
        overallStatus === "ok" ? "bg-green-50 border border-green-200" :
        overallStatus === "degraded" ? "bg-amber-50 border border-amber-200" :
        "bg-red-50 border border-red-200"
      }`}>
        {getStatusIcon(overallStatus)}
        <span className={`text-sm font-semibold ${getStatusColor(overallStatus)}`}>
          {overallStatus === "ok" ? "All systems operational" :
           overallStatus === "degraded" ? "Some systems degraded" :
           "System issues detected"}
        </span>
      </div>

      {/* Individual checks */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {checks.map(({ key, label, icon: Icon }) => {
          const check = health?.checks?.[key] || {}
          const status = check.status || "unknown"
          return (
            <div key={key} className="p-3 rounded-xl border border-ny-border">
              <div className="flex items-center gap-2 mb-1">
                <Icon size={14} className="text-ny-text-muted" />
                <span className="text-sm font-semibold text-ny-text">{label}</span>
                <span className="ml-auto">{getStatusIcon(status)}</span>
              </div>
              <p className={`text-xs font-medium ${getStatusColor(status)}`}>
                {status === "ok" || status === "healthy" ? "Operational" :
                 status === "degraded" ? "Degraded" :
                 status === "error" ? "Error" : "Unknown"}
              </p>
              {check.response_time_ms && (
                <p className="text-xs text-ny-text-muted mt-0.5">
                  Response: {check.response_time_ms}ms
                </p>
              )}
              {check.detail && (
                <p className="text-xs text-ny-text-muted mt-0.5">{check.detail}</p>
              )}
            </div>
          )
        })}
      </div>

      {/* Detailed results */}
      {health?.checks && (
        <details className="mt-4">
          <summary className="text-sm font-semibold text-ny-text cursor-pointer hover:text-ny-green">
            Detailed check results
          </summary>
          <pre className="mt-2 p-3 rounded-xl bg-gray-50 text-xs text-ny-text-secondary overflow-x-auto">
            {JSON.stringify(health.checks, null, 2)}
          </pre>
        </details>
      )}
    </div>
  )
}

export default HealthCheck
