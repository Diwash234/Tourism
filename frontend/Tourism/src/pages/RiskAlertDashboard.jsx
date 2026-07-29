import { useEffect, useState } from "react";
import { motion } from "framer-motion";

import alertApi from "../api/alertApi";

import AlertCard from "../components/cards/AlertCard";
import RiskCard from "../components/cards/RiskCard";
import SafetyOverview from "../components/cards/SafetyOverview";
import Loader from "../components/common/Loader";
import EmptyState from "../components/common/EmptyState";
import Filter from "../components/common/Filter";
import BarChartCard from "../components/charts/BarChartCard";

const LEVEL_OPTIONS = [
  { label: "Low", value: "low" },
  { label: "Moderate", value: "moderate" },
  { label: "High", value: "high" },
];

const RiskAlertDashboard = () => {
  const [alerts, setAlerts] = useState([]);
  const [level, setLevel] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAlerts = async () => {
      setLoading(true);
      try {
        // FIXED: the backend's AlertFilter filters by `severity`, not
        // `level` — the old code sent `level` (silently ignored server
        // side), so the Filter dropdown looked functional but never
        // actually filtered anything. Sending both keeps this working
        // even if a future backend change adds a real `level` field too.
        const { data } = await alertApi.getAlerts({
          severity: level,
          level,
        });

        const alertlist = Array.isArray(data)
          ? data
          : data.results || data.items || data.alerts || [];

        setAlerts(Array.isArray(alertlist) ? alertlist : []);
      } catch (error) {
        console.log("Alert loading error:", error.response?.data || error.message);
        setAlerts([]);
      } finally {
        setLoading(false);
      }
    };

    loadAlerts();
  }, [level]);

  const counts = ["low", "moderate", "high"].map(
    (lvl) => alerts.filter((alert) => alert.severity?.toLowerCase() === lvl).length
  );
  const [lowCount, moderateCount, highCount] = counts;
  const total = alerts.length;

  // Same heuristic used on the Dashboard's SafetyOverview, kept
  // consistent so the "score" means the same thing everywhere it shows
  // up — see Dashboard.jsx's scoreFromAlerts for the twin implementation.
  const safetyScore = Math.max(40, 100 - (moderateCount * 8 + highCount * 15));

  return (
    <div className="container-app py-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="section-title mb-1">Risk Alert Dashboard</h1>
          <p className="text-gray-500 text-sm">
            Stay updated on safety conditions across destinations.
          </p>
        </div>

        <Filter label="Risk Level" options={LEVEL_OPTIONS} value={level} onChange={setLevel} />
      </div>

      {/* Overall safety snapshot */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <SafetyOverview
          score={safetyScore}
          weatherStatus={highCount > 0 ? "Check alerts" : "Good"}
          earthquakeRisk={alerts.some((a) => /earthquake|seismic/i.test(a.title || a.category || "")) ? "Moderate" : "Low"}
          hospitalsNearby="See Navigation page"
          policeNearby="See Navigation page"
        />
      </motion.div>

      {/* Risk level breakdown, using RiskCard per level */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <RiskCard
          title="Low Risk Alerts"
          level="LOW"
          value={total ? Math.round((lowCount / total) * 100) : 0}
          description={`${lowCount} of ${total} active alert${total === 1 ? "" : "s"}`}
        />
        <RiskCard
          title="Moderate Risk Alerts"
          level="MODERATE"
          value={total ? Math.round((moderateCount / total) * 100) : 0}
          description={`${moderateCount} of ${total} active alert${total === 1 ? "" : "s"}`}
        />
        <RiskCard
          title="High Risk Alerts"
          level="HIGH"
          value={total ? Math.round((highCount / total) * 100) : 0}
          description={`${highCount} of ${total} active alert${total === 1 ? "" : "s"}`}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <BarChartCard
            title="Alerts by Risk Level"
            labels={["Low", "Moderate", "High"]}
            data={counts}
            label="Alerts"
          />
        </div>

        <div className="lg:col-span-2">
          {loading ? (
            <Loader />
          ) : alerts.length ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {alerts.map((alert) => (
                <AlertCard key={alert.id} alert={alert} />
              ))}
            </div>
          ) : (
            <EmptyState title="No active alerts" subtitle="All destinations currently look safe." />
          )}
        </div>
      </div>
    </div>
  );
};

export default RiskAlertDashboard;