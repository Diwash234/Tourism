import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  FiShield, FiAlertTriangle, FiPlus, FiCheckCircle, FiActivity,
  FiUserCheck, FiSmile, FiTruck, FiX
} from "react-icons/fi";

import alertApi from "../api/alertApi";
import adminApi from "../api/adminApi";

import AlertCard from "../components/cards/AlertCard";
import SafetyOverview from "../components/cards/SafetyOverview";
import Loader from "../components/common/Loader";
import EmptyState from "../components/common/EmptyState";
import Filter from "../components/common/Filter";
import BarChartCard from "../components/charts/BarChartCard";
import useToast from "../hooks/useToast";

const LEVEL_OPTIONS = [
  { label: "Low", value: "low" },
  { label: "Moderate", value: "moderate" },
  { label: "High", value: "high" },
];

const RiskAlertDashboard = () => {
  const { showToast } = useToast();
  const [alerts, setAlerts] = useState([]);
  const [level, setLevel] = useState("");
  const [loading, setLoading] = useState(true);

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
    transport_accessibility_rating: 4,
    people_helpfulness_rating: 5,
    greeting_behavior_rating: 5,
    overall_safety_rating: 9.0,
    comments: "",
  });

  const loadAlerts = async () => {
    setLoading(true);
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
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [level]);

  const handleSubmitSafetyFeedback = async (e) => {
    e.preventDefault();
    if (!feedbackForm.destination_name) {
      return showToast("Please specify the destination name", "error");
    }
    try {
      await adminApi.submitRiskFeedback(feedbackForm);
      showToast("Safety & risk assessment logged! ML risk index updated. 🙏", "success");
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
        transport_accessibility_rating: 4,
        people_helpfulness_rating: 5,
        greeting_behavior_rating: 5,
        overall_safety_rating: 9.0,
        comments: "",
      });
    } catch (err) {
      showToast("Could not submit safety feedback", "error");
    }
  };

  const counts = ["low", "moderate", "high"].map(
    (lvl) => alerts.filter((a) => (a.severity || "").toLowerCase() === lvl).length
  );
  const total = alerts.length;

  return (
    <div className="container-app py-8 space-y-6 animate-fadeIn">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-4">
        <div>
          <span className="px-3.5 py-1 rounded-full bg-rose-100 text-rose-800 text-xs font-bold uppercase tracking-wider">
            Live Risk Sentinel
          </span>
          <h1 className="text-3xl font-extrabold text-gray-900 mt-1 flex items-center gap-2">
            <FiShield className="text-purple-700" /> Nepal Safety & Risk Alert Sentinel
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Real-time hazard advisories, high-altitude weather tracking, and traveler risk assessments.
          </p>
        </div>

        <button
          onClick={() => setShowFeedbackModal(true)}
          className="px-5 py-2.5 rounded-xl bg-purple-700 hover:bg-purple-800 text-white font-bold text-sm flex items-center gap-2 shadow-lg shadow-purple-900/20 transition-all shrink-0"
        >
          <FiPlus size={16} /> Submit Safety & Hazard Assessment
        </button>
      </div>

      <SafetyOverview />

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
            <EmptyState
              title="No active alerts"
              subtitle="All destinations currently look safe."
            />
          )}
        </div>
      </div>

      {/* MODAL: TRAVELER SAFETY FEEDBACK FORM */}
      <AnimatePresence>
        {showFeedbackModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl p-6 sm:p-8 max-w-xl w-full shadow-2xl space-y-4 border border-purple-100 max-h-[90vh] overflow-y-auto"
            >
              <div className="flex items-center justify-between border-b pb-3">
                <div>
                  <h3 className="text-lg font-bold text-gray-900">Traveler Safety & Hazard Survey</h3>
                  <p className="text-xs text-gray-500">Calibrates ML real-time safety scores for upcoming travelers</p>
                </div>
                <button onClick={() => setShowFeedbackModal(false)} className="text-gray-400 hover:text-gray-600">
                  <FiX size={20} />
                </button>
              </div>

              <form onSubmit={handleSubmitSafetyFeedback} className="space-y-4 text-xs">
                <div>
                  <label className="font-semibold text-gray-700">Destination Name *</label>
                  <input
                    required
                    placeholder="e.g. Everest Base Camp / Annapurna Sanctuary / Mustang"
                    className="input-field mt-1 text-sm"
                    value={feedbackForm.destination_name}
                    onChange={(e) => setFeedbackForm({ ...feedbackForm, destination_name: e.target.value })}
                  />
                </div>

                <div className="p-4 rounded-2xl bg-purple-50 space-y-3">
                  <div className="flex items-center justify-between">
                    <label className="font-bold text-purple-900">Did anyone become sick on this trip?</label>
                    <input
                      type="checkbox"
                      checked={feedbackForm.became_sick}
                      onChange={(e) => setFeedbackForm({ ...feedbackForm, became_sick: e.target.checked })}
                      className="w-4 h-4 text-purple-600 rounded"
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
                    <label className="font-semibold text-gray-700">Natural Hazard Witnessed</label>
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
                      onChange={(e) => setFeedbackForm({ ...feedbackForm, overall_safety_rating: parseFloat(e.target.value) })}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="font-semibold text-gray-700">Transport Ease (1-5)</label>
                    <input
                      type="number"
                      min={1}
                      max={5}
                      className="input-field mt-1 text-xs"
                      value={feedbackForm.transport_accessibility_rating}
                      onChange={(e) => setFeedbackForm({ ...feedbackForm, transport_accessibility_rating: parseInt(e.target.value) })}
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
                      onChange={(e) => setFeedbackForm({ ...feedbackForm, people_helpfulness_rating: parseInt(e.target.value) })}
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
                      onChange={(e) => setFeedbackForm({ ...feedbackForm, greeting_behavior_rating: parseInt(e.target.value) })}
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
                    className="btn-primary px-5 py-2.5 text-xs font-bold bg-purple-700 hover:bg-purple-800 text-white rounded-xl shadow-lg"
                  >
                    Submit Assessment to ML Engine
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
