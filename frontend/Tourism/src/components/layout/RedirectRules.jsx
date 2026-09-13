import { useEffect } from "react"
import { Navigate, useLocation } from "react-router-dom"
import usePublicConfig from "../../hooks/usePublicConfig"

/**
 * RedirectRules — applies admin-managed URL redirects (brief §14).
 *
 * Rules come from the public config (`redirects`), which is served from the
 * database, so an admin adding a redirect in the Redirects & URLs panel takes
 * effect on the live site immediately with no rebuild. Internal targets use
 * a router replacement (history stays clean); external https:// targets are
 * handed to the browser. The backend rejects loops when rules are saved, so
 * chained rules always terminate.
 */
const normalize = (path) => {
  const value = String(path || "").trim()
  if (!value.startsWith("/")) return value
  return value.length > 1 ? value.replace(/\/+$/, "") : value
}

export default function RedirectRules() {
  const location = useLocation()
  const { redirects } = usePublicConfig()

  const current = normalize(location.pathname)
  const match = (redirects || []).find((rule) => normalize(rule.old_path) === current)
  const external = match && /^https?:\/\//.test(match.new_path)

  useEffect(() => {
    if (external) window.location.replace(match.new_path)
  }, [external, match?.new_path])

  if (!match) return null
  if (external) return null // browser navigation is already in flight
  return <Navigate to={match.new_path} replace />
}
