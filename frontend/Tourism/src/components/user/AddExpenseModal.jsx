import { useState } from "react"
import { FiDollarSign, FiX, FiCheck, FiPlus } from "react-icons/fi"
import axiosClient from "../../api/axiosClient"
import useToast from "../../hooks/useToast"

export default function AddExpenseModal({ isOpen, onClose, onSuccess }) {
  const { showToast } = useToast()
  const [form, setForm] = useState({
    title: "",
    category: "food",
    amount: "",
    currency: "NPR",
    date: new Date().toISOString().split("T")[0],
    notes: "",
  })
  const [submitting, setSubmitting] = useState(false)

  if (!isOpen) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.amount || Number(form.amount) <= 0) {
      showToast("Please enter a valid expense amount in NPR.", "error")
      return
    }

    setSubmitting(true)
    try {
      await axiosClient.post("/budgets/", {
        title: form.title || `${form.category.toUpperCase()} Expense`,
        category: form.category,
        amount: Number(form.amount),
        currency: form.currency,
        date: form.date,
        notes: form.notes,
      })

      showToast(`Expense of NPR ${Number(form.amount).toLocaleString()} logged!`, "success")
      setForm({
        title: "",
        category: "food",
        amount: "",
        currency: "NPR",
        date: new Date().toISOString().split("T")[0],
        notes: "",
      })
      onClose()
      if (onSuccess) onSuccess()
    } catch (err) {
      showToast(err.response?.data?.detail || "Could not log expense.", "error")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="bg-slate-950 border border-slate-800 rounded-3xl max-w-md w-full p-6 space-y-4 shadow-2xl text-white">
        <div className="flex justify-between items-start border-b border-slate-800 pb-3">
          <div>
            <span className="text-[10px] font-black uppercase text-emerald-400">Budget Tracker</span>
            <h3 className="text-lg font-black mt-0.5">Log Quick Expenditure</h3>
          </div>
          <button type="button" onClick={onClose} className="p-1.5 rounded-full bg-slate-800 text-slate-400 hover:text-white">
            <FiX size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3 text-xs">
          <div>
            <label className="font-bold text-slate-300 block mb-1">Expense Title / Item</label>
            <input
              type="text"
              required
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="e.g., Dal Bhat lunch, Pokhara Taxi, Park Entry Fee"
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-400"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="font-bold text-slate-300 block mb-1">Category</label>
              <select
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-emerald-400"
              >
                <option value="accommodation">🏨 Stay / Hotel</option>
                <option value="food">🍛 Food & Dining</option>
                <option value="transportation">🚌 Transit / Taxi</option>
                <option value="activities">🎟️ Permits & Entry</option>
                <option value="shopping">🛍️ Shopping / Gear</option>
                <option value="other">ℹ️ Miscellaneous</option>
              </select>
            </div>

            <div>
              <label className="font-bold text-slate-300 block mb-1">Amount (NPR) *</label>
              <input
                type="number"
                required
                min={1}
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
                placeholder="NPR 1,500"
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-400"
              />
            </div>
          </div>

          <div>
            <label className="font-bold text-slate-300 block mb-1">Date</label>
            <input
              type="date"
              value={form.date}
              onChange={(e) => setForm({ ...form, date: e.target.value })}
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-emerald-400"
            />
          </div>

          <div>
            <label className="font-bold text-slate-300 block mb-1">Notes / Receipts (Optional)</label>
            <textarea
              rows="2"
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              placeholder="e.g. Paid cash at Lakeside Pokhara restaurant"
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-400"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-black flex items-center gap-1.5 shadow"
            >
              <FiCheck size={16} /> {submitting ? "Saving..." : "Log Expense"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
