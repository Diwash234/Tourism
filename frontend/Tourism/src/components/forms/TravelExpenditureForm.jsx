import { useState } from "react"
import { FiDollarSign, FiPlus, FiCheckCircle } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

export default function TravelExpenditureForm({ onSuccess }) {
  const { showToast } = useToast()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    destination_name: "",
    num_people: 2,
    num_days: 5,
    travel_mode: "Tourist Bus",
    accommodation_cost: 120,
    travel_cost: 60,
    food_cost: 80,
    entry_cost: 30,
    extra_cost: 20,
    route_details: "Kathmandu to Pokhara via Prithvi Highway",
    notes: "Practical expenditure report",
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.destination_name) {
      return showToast("Please specify the destination name", "error")
    }
    setLoading(true)
    try {
      await adminApi.submitExpenseFeedback(form)
      showToast("Trip expenditure recorded & fed into ML cost prediction engine! 💰", "success")
      onSuccess?.()
    } catch (err) {
      showToast("Failed to record expense", "error")
    } finally {
      setLoading(false)
    }
  }

  const total = Number(form.accommodation_cost || 0) + Number(form.travel_cost || 0) + Number(form.food_cost || 0) + Number(form.entry_cost || 0) + Number(form.extra_cost || 0)

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
            min={1}
            className="input-field mt-1 text-sm"
            value={form.num_people}
            onChange={(e) => setForm({ ...form, num_people: parseInt(e.target.value) || 1 })}
          />
        </div>
        <div>
          <label className="font-semibold text-gray-700">Trip Duration (Days)</label>
          <input
            type="number"
            min={1}
            className="input-field mt-1 text-sm"
            value={form.num_days}
            onChange={(e) => setForm({ ...form, num_days: parseInt(e.target.value) || 1 })}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div>
          <label className="font-semibold text-gray-700">Hotel/Stay (NPR)</label>
          <input
            type="number"
            className="input-field mt-1 text-sm"
            value={form.accommodation_cost}
            onChange={(e) => setForm({ ...form, accommodation_cost: parseFloat(e.target.value) || 0 })}
          />
        </div>
        <div>
          <label className="font-semibold text-gray-700">Transit (NPR)</label>
          <input
            type="number"
            className="input-field mt-1 text-sm"
            value={form.travel_cost}
            onChange={(e) => setForm({ ...form, travel_cost: parseFloat(e.target.value) || 0 })}
          />
        </div>
        <div>
          <label className="font-semibold text-gray-700">Food (NPR)</label>
          <input
            type="number"
            className="input-field mt-1 text-sm"
            value={form.food_cost}
            onChange={(e) => setForm({ ...form, food_cost: parseFloat(e.target.value) || 0 })}
          />
        </div>
        <div>
          <label className="font-semibold text-gray-700">Permit/Entry (NPR)</label>
          <input
            type="number"
            className="input-field mt-1 text-sm"
            value={form.entry_cost}
            onChange={(e) => setForm({ ...form, entry_cost: parseFloat(e.target.value) || 0 })}
          />
        </div>
      </div>

      <div className="p-3.5 rounded-2xl bg-[#F7F8F5] flex items-center justify-between">
        <span className="font-bold text-[#102A2E]">Total Calculated Cost:</span>
        <span className="text-lg font-black text-purple-950">NPR {total.toLocaleString()}</span>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="btn-primary w-full py-3 text-sm font-bold bg-[#102A2E] hover:bg-[#1D5146] text-white rounded-xl shadow-lg"
      >
        {loading ? "Recording..." : "Feed Ground Truth into ML Budget Engine"}
      </button>
    </form>
  )
}
