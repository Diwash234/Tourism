import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import PageHeader from "../components/common/PageHeader"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import { motion, AnimatePresence } from "framer-motion";
import {
  FiShield, FiPlus, FiX
} from "react-icons/fi";

import alertApi from "../api/alertApi";
import adminApi from "../api/adminApi";

import AlertCard from "../components/cards/AlertCard";
import SafetyOverview from "../components/cards/SafetyOverview";
import { scoreFromAlerts } from "../utils/safetyScore";
import Loader from "../components/common/Loader";
import EmptyState from "../components/common/EmptyState";
import Filter from "../components/common/Filter";
import BarChartCard from "../components/charts/BarChartCard";
import useToast from "../hooks/useToast";
import DestinationRiskPanel from "../components/risk/DestinationRiskPanel";
import useAuth from "../hooks/useAuth";

const LEVEL_OPTIONS = [
  { label: "Low", value: "low" },
  { label: "Moderate", value: "moderate" },
  { label: "High", value: "high" },
  { label: "Critical", value: "critical" },
];

const RiskAlertDashboard = () => {
  const { showToast } = useToast();
  const { isAuthenticated } = useAuth();
  const [alerts, setAlerts] = useState([]);
  const [level, setLevel] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  // Safety feedback modal
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackForm, setFeedbackForm] = useState({
    destination_name: "",
    became_sick: false,
    sickness_type: "",
    misleading_activities: false,
    misleading_details: "",
    accident_occurred: false,
    accident_details: "",
    hazard_witnessed: "None",
    transport_accessibility_rating: "",
    people_helpfulness_rating: "",
    greeting_behavior_rating: "",
    overall_safety_rating: "",
    comments: "",
  });

  const loadAlerts = async () => {
    setLoading(true);
    setLoadError("");
    try {
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
      setLoadError(error.response?.data?.detail || "We could not load safety alerts right now.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const t = setTimeout(loadAlerts, 0);
    return () => clearTimeout(t);
  }, [level]);

  const handleSubmitSafetyFeedback = async (e) => {
    e.preventDefault();
    if (!isAuthenticated) {
      showToast("Sign in to submit safety feedback.", "info");
      return;
    }
    if (!feedbackForm.destination_name) {
      return showToast("Please specify the destination name", "error");
    }
    const ratingFields = ["transport_accessibility_rating", "people_helpfulness_rating", "greeting_behavior_rating", "overall_safety_rating"];
    const normalizedRatings = Object.fromEntries(ratingFields.map((key) => [key, Number(feedbackForm[key])]));
    const ratingMaximums = { transport_accessibility_rating: 5, people_helpfulness_rating: 5, greeting_behavior_rating: 5, overall_safety_rating: 10 };
    if (ratingFields.some((key) => !Number.isFinite(normalizedRatings[key]) || normalizedRatings[key] < 1 || normalizedRatings[key] > ratingMaximums[key])) {
      return showToast("Complete each rating before submitting.", "error");
    }
    try {
      await adminApi.submitRiskFeedback({ ...feedbackForm, ...normalizedRatings });
      showToast("Safety feedback submitted for review.", "success");
      setShowFeedbackModal(false);
      setFeedbackForm({
        destination_name: "",
        became_sick: false,
        sickness_type: "",
        misleading_activities: false,
        misleading_details: "",
        accident_occurred: false,
        accident_details: "",
        hazard_witnessed: "None",
        transport_accessibility_rating: "",
        people_helpfulness_rating: "",
        greeting_behavior_rating: "",
        overall_safety_rating: "",
        comments: "",
      });
    } catch (err) {
      showToast("Could not submit safety feedback", "error");
    }
  };

  const counts = ["low", "moderate", "high", "critical"].map(
    (lvl) => alerts.filter((a) => (a.severity || "").toLowerCase() === lvl).length
  );
  const total = alerts.length;

  return (
    <div className="ny-page container-app space-y-6 py-6 sm:py-8">
      <CMSPageIntro pageKey="risk-alerts" />
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-4">
        <div>
          <span className="px-3.5 py-1 rounded-full bg-rose-100 text-rose-800 text-xs font-bold uppercase tracking-wider">
            Current safety alerts
          </span>
          <PageHeader title="Safety alerts" subtitle="Review hazard records returned for Nepal and share a firsthand safety observation when appropriate." icon={FiShield} />
          <p className="text-gray-500 text-sm mt-1">
            Current hazard advisories, weather context, and traveller safety assessments.
          </p>
        </div>

        {isAuthenticated ? (
          <button
            type="button"
            onClick={() => setShowFeedbackModal(true)}
            className="ny-btn ny-btn-primary shrink-0"
          >
            <FiPlus size={16} aria-hidden="true" /> Submit safety assessment
          </button>
        ) : (
          <Link to="/login?next=%2Frisk-alerts" className="ny-btn ny-btn-primary shrink-0">
            <FiPlus size={16} aria-hidden="true" /> Sign in to share safety feedback
          </Link>
        )}
      </div>

      <DestinationRiskPanel />

      <SafetyOverview
        score={scoreFromAlerts(alerts)}
        earthquakeRisk={alerts.some((a) => /earthquake|seismic/i.test(a.title || a.type || a.alert_type || "")) ? "Alert recorded" : "No recorded alert"}
      />

      <div className="flex justify-between items-center my-6">
        <Filter
          options={LEVEL_OPTIONS}
          value={level}
          onChange={(val) => setLevel(val)}
          placeholder="All Risk Levels"
        />
        <span className="text-sm font-semibold text-gray-500">
          {total} Active Alert{total === 1 ? "" : "s"}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <BarChartCard
            title="Alerts by Risk Level"
            labels={["Low", "Moderate", "High", "Critical"]}
            data={counts}
            label="Alerts"
          />
        </div>

        <div className="lg:col-span-2">
          {loading ? (
            <Loader />
          ) : loadError ? (
            <div role="alert" className="ny-panel p-5 text-center">
              <p className="font-bold text-[var(--ny-danger)]">Safety alerts unavailable</p>
              <p className="mt-2 text-sm text-[var(--ny-text-secondary)]">{loadError}</p>
              <button type="button" onClick={loadAlerts} className="ny-btn ny-btn-secondary mt-4">Try again</button>
            </div>
          ) : alerts.length ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {alerts.map((alert) => (
                <AlertCard key={alert.id} alert={alert} />
              ))}
            </div>
          ) : (
            <EmptyState
              title="No active alerts"
              subtitle="No alert records are currently available for this view."
            />
          )}
        </div>
      </div>

      {/* MODAL: TRAVELER SAFETY FEEDBACK FORM */}
      <AnimatePresence>
        {isAuthenticated && showFeedbackModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              role="dialog"
              aria-modal="true"
              aria-labelledby="safety-feedback-title"
              className="bg-white rounded-3xl p-6 sm:p-8 max-w-xl w-full shadow-2xl space-y-4 border border-[#E5E0D5] max-h-[90vh] overflow-y-auto"
            >
              <div className="flex items-center justify-between border-b pb-3">
                <div>
                  <h3 id="safety-feedback-title" className="text-lg font-bold text-gray-900">Traveler Safety & Hazard Survey</h3>
                  <p className="text-xs text-gray-500">Help us keep destination safety information useful for future travellers.</p>
                </div>
                <button type="button" aria-label="Close safety feedback" onClick={() => setShowFeedbackModal(false)} className="text-gray-400 hover:text-gray-600">
                  <FiX size={20} />
                </button>
              </div>

              <form onSubmit={handleSubmitSafetyFeedback} className="space-y-4 text-xs">
                <div>
                  <label htmlFor="feedback-destination" className="font-semibold text-gray-700">Destination Name *</label>
                  <input
                    required
                    id="feedback-destination"
                     placeholder="e.g. Everest Base Camp / Annapurna Sanctuary / Mustang"
                    className="input-field mt-1 text-sm"
                    value={feedbackForm.destination_name}
                    onChange={(e) => setFeedbackForm({ ...feedbackForm, destination_name: e.target.value })}
                  />
                </div>

                <div className="p-4 rounded-2xl bg-[#F7F8F5] space-y-3">
                  <div className="flex items-center justify-between">
                    <label className="font-bold text-[#102A2E]">Did anyone become sick on this trip?</label>
                    <input
                      type="checkbox"
                      checked={feedbackForm.became_sick}
                      onChange={(e) => setFeedbackForm({ ...feedbackForm, became_sick: e.target.checked })}
                      className="w-4 h-4 text-emerald-700 rounded"
                    />
                  </div>
                  {feedbackForm.became_sick && (
                    <input
                      placeholder="Sickness type (e.g. Altitude Sickness / AMS, Food Poisoning, Dehydration)"
                      className="input-field text-xs"
                      value={feedbackForm.sickness_type}
                      onChange={(e) => setFeedbackForm({ ...feedbackForm, sickness_type: e.target.value })}
                    />
                  )}
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="feedback-hazard" className="font-semibold text-gray-700">Natural Hazard Witnessed</label>
                    <select
                      className="input-field mt-1 text-xs"
                      value={feedbackForm.hazard_witnessed}
                      onChange={(e) => setFeedbackForm({ ...feedbackForm, hazard_witnessed: e.target.value })}
                    >
                      <option value="None">None / Clear Trail</option>
                      <option value="Landslide">Landslide</option>
                      <option value="Avalanche">Avalanche</option>
                      <option value="Flood">Flood</option>
                      <option value="Heavy Snow">Heavy Snowstorm</option>
                      <option value="Rockfall">Rockfall</option>
                    </select>
                  </div>
                  <div>
                    <label className="font-semibold text-gray-700">Overall Safety Score (1-10)</label>
                    <input
                      type="number"
                      min={1}
                      max={10}
                      step={0.5}
                      className="input-field mt-1 text-xs"
                      value={feedbackForm.overall_safety_rating}
                      onChange={(e) => setFeedbackForm({ ...feedbackForm, overall_safety_rating: e.target.value })}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                  <div>
                    <label className="font-semibold text-gray-700">Transport Ease (1-5)</label>
                    <input
                      type="number"
                      min={1}
                      max={5}
                      className="input-field mt-1 text-xs"
                      value={feedbackForm.transport_accessibility_rating}
                      onChange={(e) => setFeedbackForm({ ...feedbackForm, transport_accessibility_rating: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="font-semibold text-gray-700">Helpfulness (1-5)</label>
                    <input
                      type="number"
                      min={1}
                      max={5}
                      className="input-field mt-1 text-xs"
                      value={feedbackForm.people_helpfulness_rating}
                      onChange={(e) => setFeedbackForm({ ...feedbackForm, people_helpfulness_rating: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="font-semibold text-gray-700">Greeting / Hospitality (1-5)</label>
                    <input
                      type="number"
                      min={1}
                      max={5}
                      className="input-field mt-1 text-xs"
                      value={feedbackForm.greeting_behavior_rating}
                      onChange={(e) => setFeedbackForm({ ...feedbackForm, greeting_behavior_rating: e.target.value })}
                    />
                  </div>
                </div>

                <div>
                  <label className="font-semibold text-gray-700">Comments & Safety Advice</label>
                  <textarea
                    rows={2}
                    placeholder="Share any tips (e.g. trail condition, water purification, guide requirement)..."
                    className="input-field mt-1 text-xs"
                    value={feedbackForm.comments}
                    onChange={(e) => setFeedbackForm({ ...feedbackForm, comments: e.target.value })}
                  />
                </div>

                <div className="flex justify-end gap-3 pt-3 border-t">
                  <button
                    type="button"
                    onClick={() => setShowFeedbackModal(false)}
                    className="px-4 py-2 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn-primary px-5 py-2.5 text-xs font-bold bg-[#102A2E] hover:bg-[#1D5146] text-white rounded-xl shadow-lg"
                  >
                    Submit safety feedback
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default RiskAlertDashboard;
