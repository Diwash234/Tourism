import { useState } from "react"
import { FiAlertTriangle, FiCheckCircle, FiX, FiSend } from "react-icons/fi"
import axiosClient from "../../api/axiosClient"
import useToast from "../../hooks/useToast"

export default function ReportErrorModal({ isOpen, onClose, destination, fieldName = "", currentVal = "" }) {
  const { showToast } = useToast()
  const [reportType, setReportType] = useState("map_location")
  const [suggestedValue, setSuggestedValue] = useState("")
  const [description, setDescription] = useState("")
  const [submitting, setSubmitting] = useState(false)

  if (!isOpen) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await axiosClient.post("/reports/submit/", {
        destination_id: destination?.id || null,
        report_type: reportType,
        page_url: window.location.pathname,
        field_name: fieldName || "general",
        displayed_value: currentVal || "",
        suggested_value: suggestedValue,
        description,
      })
      showToast("Thank you! Your report was sent to the Data Quality Desk for verification.", "success")
      setSuggestedValue("")
      setDescription("")
      onClose()
    } catch {
      showToast("Could not submit report. Please try again.", "error")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="bg-slate-950 border border-slate-800 rounded-3xl max-w-lg w-full p-6 space-y-4 shadow-2xl text-white">
        <div className="flex justify-between items-start border-b border-slate-800 pb-3">
          <div>
            <span className="text-[10px] font-black uppercase text-amber-400">Data Integrity Guard</span>
            <h3 className="text-lg font-black mt-0.5">Report Incorrect Information</h3>
            {destination?.name && (
              <p className="text-xs text-slate-400">Destination: <span className="text-white font-bold">{destination.name}</span></p>
            )}
          </div>
          <button type="button" onClick={onClose} className="p-1.5 rounded-full bg-slate-800 text-slate-400 hover:text-white">
            <FiX size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3 text-xs">
          <div className="space-y-1">
            <label className="font-bold text-slate-300 block">Problem Category</label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-amber-400"
            >
              <option value="map_location">📍 Wrong Map Location / Coordinates</option>
              <option value="route">🚗 Incorrect Route / Transit Details</option>
              <option value="fare">💵 Incorrect Fare / Ticket Cost</option>
              <option value="travel_time">⏱️ Wrong Distance / Travel Time</option>
              <option value="opening_hours">🕒 Outdated Opening Hours</option>
              <option value="photo">🖼️ Wrong or Low-Quality Photo</option>
              <option value="description">📝 Incorrect Description / Info</option>
              <option value="moved">🚫 Place Moved, Renamed or Closed</option>
              <option value="other">ℹ️ Other Data Issue</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="font-bold text-slate-300 block">Corrected Value (if known)</label>
            <input
              type="text"
              value={suggestedValue}
              onChange={(e) => setSuggestedValue(e.target.value)}
              placeholder="e.g., Real bus fare is NPR 650, or exact GPS is 28.21, 83.96"
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-amber-400"
            />
          </div>

          <div className="space-y-1">
            <label className="font-bold text-slate-300 block">Additional Context / Notes</label>
            <textarea
              rows="3"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Explain why this information is incorrect..."
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-amber-400"
            />
          </div>

          <div className="p-3 rounded-xl bg-amber-950/40 border border-amber-500/30 text-[11px] text-amber-200">
            💡 <b>Data Integrity Promise:</b> Reports are reviewed by administrators before updating official datasets. Unverified claims are never published automatically.
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
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
              className="px-5 py-2 rounded-xl bg-amber-400 hover:bg-amber-500 text-slate-950 font-black flex items-center gap-1.5 shadow"
            >
              <FiSend size={14} /> {submitting ? "Submitting..." : "Submit Report"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
