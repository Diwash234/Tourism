import { useState } from "react"
import { FiShield, FiAlertTriangle } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

export default function RiskAssessmentForm({ onSuccess }) {
  const { showToast } = useToast()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    destination_name: "",
    became_sick: false,
    sickness_type: "",
    hazard_witnessed: "None",
    transport_accessibility_rating: 4,
    people_helpfulness_rating: 5,
    greeting_behavior_rating: 5,
    overall_safety_rating: 9.0,
    comments: "",
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.destination_name) return showToast("Destination name required", "error")
    setLoading(true)
    try {
      await adminApi.submitRiskFeedback(form)
      showToast("Safety & risk assessment submitted to ML Sentinel! 🛡️", "success")
      onSuccess?.()
    } catch {
      showToast("Submission failed", "error")
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 text-xs">
      <div>
        <label className="font-semibold text-gray-700">Destination Name *</label>
        <input
          required
          placeholder="e.g. Everest Base Camp / Annapurna Base Camp"
          className="input-field mt-1 text-sm"
          value={form.destination_name}
          onChange={(e) => setForm({ ...form, destination_name: e.target.value })}
        />
      </div>

      <div className="p-3 rounded-xl bg-purple-50 space-y-2">
        <div className="flex items-center justify-between">
          <span className="font-bold text-purple-900">Did anyone become sick?</span>
          <input
            type="checkbox"
            checked={form.became_sick}
            onChange={(e) => setForm({ ...form, became_sick: e.target.checked })}
          />
        </div>
        {form.became_sick && (
          <input
            placeholder="e.g. Altitude Sickness (AMS), Food Poisoning"
            className="input-field text-xs"
            value={form.sickness_type}
            onChange={(e) => setForm({ ...form, sickness_type: e.target.value })}
          />
        )}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="font-semibold text-gray-700">Hazard Witnessed</label>
          <select
            className="input-field mt-1 text-xs"
            value={form.hazard_witnessed}
            onChange={(e) => setForm({ ...form, hazard_witnessed: e.target.value })}
          >
            <option value="None">None / Clear Trail</option>
            <option value="Landslide">Landslide</option>
            <option value="Avalanche">Avalanche</option>
            <option value="Flood">Flood</option>
            <option value="Heavy Snow">Heavy Snowstorm</option>
          </select>
        </div>
        <div>
          <label className="font-semibold text-gray-700">Safety Rating (1-10)</label>
          <input
            type="number"
            min={1}
            max={10}
            step={0.5}
            className="input-field mt-1 text-xs"
            value={form.overall_safety_rating}
            onChange={(e) => setForm({ ...form, overall_safety_rating: parseFloat(e.target.value) || 9 })}
          />
        </div>
      </div>

      <div>
        <label className="font-semibold text-gray-700">Comments / Local Advice</label>
        <textarea
          rows={2}
          placeholder="Trail condition, hospitality or water safety notes..."
          className="input-field mt-1 text-xs"
          value={form.comments}
          onChange={(e) => setForm({ ...form, comments: e.target.value })}
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="btn-primary w-full py-2.5 text-xs font-bold bg-purple-700 hover:bg-purple-800 text-white rounded-xl shadow-md"
      >
        {loading ? "Submitting..." : "Submit Safety Report to ML"}
      </button>
    </form>
  )
}
