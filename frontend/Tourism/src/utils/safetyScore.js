// Shared alert-activity indicator used by Dashboard and RiskAlertDashboard.
// It is not a safety grade: the value is derived only from fetched alert
// records, and an empty response is unavailable rather than an invented
// “safe” percentage. Severity weights are intentionally conservative and
// should be replaced by a documented, calibrated model when one exists.
export function scoreFromAlerts(alerts = []) {
  if (!Array.isArray(alerts) || alerts.length === 0) return null
  const penalty = alerts.reduce((sum, a) => {
    const level = (a.level || a.severity || "").toLowerCase()
    return sum + (level === "critical" ? 30 : level === "high" ? 15 : level === "moderate" ? 8 : 4)
  }, 0)
  return Math.max(0, 100 - penalty)
}

export default scoreFromAlerts
