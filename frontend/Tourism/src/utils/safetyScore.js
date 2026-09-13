// Shared safety-score derivation used by Dashboard and RiskAlertDashboard.
// The score is computed ONLY from fetched alert data — there is no hardcoded
// baseline. With zero alerts the score is a genuine 100; each alert applies a
// penalty by severity (high 15, moderate 8, other 4), floored at 40 so a
// heavily-alerted region still renders a readable bar.
export function scoreFromAlerts(alerts = []) {
  const penalty = alerts.reduce((sum, a) => {
    const level = (a.level || a.severity || "").toLowerCase()
    return sum + (level === "high" ? 15 : level === "moderate" ? 8 : 4)
  }, 0)
  return Math.max(40, 100 - penalty)
}

export default scoreFromAlerts
