import { useState } from "react"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

export default function TravelExpenditureForm({ onSuccess }) {
  const { showToast } = useToast()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    destination_name: "",
    num_people: "",
    num_days: "",
    travel_mode: "",
    accommodation_cost: "",
    travel_cost: "",
    food_cost: "",
    entry_cost: "",
    extra_cost: "",
    route_details: "",
    notes: "",
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.destination_name) {
      return showToast("Please specify the destination name", "error")
    }
    if (!form.num_people || !form.num_days || !form.travel_mode || ["accommodation_cost", "travel_cost", "food_cost", "entry_cost", "extra_cost"].some((key) => form[key] === "")) {
      return showToast("Complete the trip details and each recorded expense field.", "error")
    }
    setLoading(true)
    try {
      await adminApi.submitExpenseFeedback({
        ...form,
        num_people: Number(form.num_people),
        num_days: Number(form.num_days),
        accommodation_cost: Number(form.accommodation_cost),
        travel_cost: Number(form.travel_cost),
        food_cost: Number(form.food_cost),
        entry_cost: Number(form.entry_cost),
        extra_cost: Number(form.extra_cost),
      })
      showToast("Trip expenditure recorded.", "success")
      onSuccess?.()
    } catch (err) {
      showToast("Failed to record expense", "error")
    } finally {
      setLoading(false)
    }
  }

  const costFields = ["accommodation_cost", "travel_cost", "food_cost", "entry_cost", "extra_cost"]
  const costValues = costFields.map((key) => Number(form[key]))
  const total = costFields.every((key) => form[key] !== "" && Number.isFinite(Number(form[key]))) ? costValues.reduce((sum, value) => sum + value, 0) : null

  return (
    <form onSubmit={handleSubmit} className="space-y-4 text-xs">
      <div>
        <label className="font-semibold text-gray-700">Destination Name *</label>
        <input
          required
          className="input-field mt-1 text-sm font-medium"
          placeholder="e.g. Annapurna Base Camp / Pokhara / Mustang"
          value={form.destination_name}
          onChange={(e) => setForm({ ...form, destination_name: e.target.value })}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="font-semibold text-gray-700">Number of Travelers</label>
          <input
            type="number"
            required min={1}
            className="input-field mt-1 text-sm"
            value={form.num_people}
            onChange={(e) => setForm({ ...form, num_people: e.target.value })}
          />
        </div>
        <div>
          <label className="font-semibold text-gray-700">Trip Duration (Days)</label>
          <input
            type="number"
            required min={1}
            className="input-field mt-1 text-sm"
            value={form.num_days}
            onChange={(e) => setForm({ ...form, num_days: e.target.value })}
          />
        </div>
      </div>

      <div>
        <label className="font-semibold text-gray-700">Travel mode *</label>
        <select
          required
          className="input-field mt-1 text-sm"
          value={form.travel_mode}
          onChange={(e) => setForm({ ...form, travel_mode: e.target.value })}
        >
          <option value="">Select a mode</option>
          <option value="Tourist Bus">Tourist bus</option>
          <option value="Private Car / Taxi">Private car / taxi</option>
          <option value="Flight">Flight</option>
          <option value="Walking / Trek">Walking / trek</option>
          <option value="Other">Other</option>
        </select>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div>
          <label className="font-semibold text-gray-700">Hotel/Stay (NPR)</label>
          <input
            type="number"
            required
            min="0"
            className="input-field mt-1 text-sm"
            value={form.accommodation_cost}
            onChange={(e) => setForm({ ...form, accommodation_cost: e.target.value })}
          />
        </div>
        <div>
          <label className="font-semibold text-gray-700">Transit (NPR)</label>
          <input
            type="number"
            required
            min="0"
            className="input-field mt-1 text-sm"
            value={form.travel_cost}
            onChange={(e) => setForm({ ...form, travel_cost: e.target.value })}
          />
        </div>
        <div>
          <label className="font-semibold text-gray-700">Food (NPR)</label>
          <input
            type="number"
            required
            min="0"
            className="input-field mt-1 text-sm"
            value={form.food_cost}
            onChange={(e) => setForm({ ...form, food_cost: e.target.value })}
          />
        </div>
        <div>
          <label className="font-semibold text-gray-700">Permit/Entry (NPR)</label>
          <input
            type="number"
            required
            min="0"
            className="input-field mt-1 text-sm"
            value={form.entry_cost}
            onChange={(e) => setForm({ ...form, entry_cost: e.target.value })}
          />
        </div>
        <div>
          <label className="font-semibold text-gray-700">Other costs (NPR)</label>
          <input
            type="number"
            required
            min="0"
            className="input-field mt-1 text-sm"
            value={form.extra_cost}
            onChange={(e) => setForm({ ...form, extra_cost: e.target.value })}
          />
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label className="font-semibold text-gray-700">Route or transit details</label>
          <textarea
            rows="2"
            className="input-field mt-1 text-sm"
            value={form.route_details}
            onChange={(e) => setForm({ ...form, route_details: e.target.value })}
            placeholder="Record the route or transit actually used"
          />
        </div>
        <div>
          <label className="font-semibold text-gray-700">Notes</label>
          <textarea
            rows="2"
            className="input-field mt-1 text-sm"
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            placeholder="Optional context for the review team"
          />
        </div>
      </div>

      <div className="p-3.5 rounded-2xl bg-[#F7F8F5] flex items-center justify-between">
        <span className="font-bold text-[#102A2E]">Total Calculated Cost:</span>
        <span className="text-lg font-black text-purple-950">{total != null ? `NPR ${total.toLocaleString()}` : "Complete all cost fields to calculate"}</span>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="btn-primary w-full py-3 text-sm font-bold bg-[#102A2E] hover:bg-[#1D5146] text-white rounded-xl shadow-lg"
      >
        {loading ? "Recording..." : "Record expenditure feedback"}
      </button>
    </form>
  )
}
