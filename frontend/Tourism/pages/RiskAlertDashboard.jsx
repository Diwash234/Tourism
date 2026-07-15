import { useEffect, useState } from "react"
import alertApi from "../api/alertApi"
import AlertCard from "../components/cards/AlertCard"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import Filter from "../components/common/Filter"
import BarChartCard from "../components/charts/BarChartCard"

const LEVEL_OPTIONS = [
  { label: "Low", value: "low" },
  { label: "Moderate", value: "moderate" },
  { label: "High", value: "high" },
]

const RiskAlertDashboard = () => {
  const [alerts, setAlerts] = useState([])
  const [level, setLevel] = useState("")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    alertApi
      .getAlerts({ level })
      .then(({ data }) => setAlerts(data.items || data || []))
      .catch(() => setAlerts([]))
      .finally(() => setLoading(false))
  }, [level])

  const counts = ["low", "moderate", "high"].map(
    (lvl) => alerts.filter((a) => a.level?.toLowerCase() === lvl).length
  )

  return (
    <div className="container-app py-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="section-title mb-1">Risk Alert Dashboard</h1>
          <p className="text-gray-500 text-sm">Stay updated on safety conditions across destinations.</p>
        </div>
        <Filter label="Risk Level" options={LEVEL_OPTIONS} value={level} onChange={setLevel} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <BarChartCard title="Alerts by Risk Level" labels={["Low", "Moderate", "High"]} data={counts} label="Alerts" />
        </div>
        <div className="lg:col-span-2">
          {loading ? (
            <Loader />
          ) : alerts.length ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {alerts.map((a) => <AlertCard key={a.id} alert={a} />)}
            </div>
          ) : (
            <EmptyState title="No active alerts" subtitle="All destinations currently look safe." />
          )}
        </div>
      </div>
    </div>
  )
}

export default RiskAlertDashboard