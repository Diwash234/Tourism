import { useEffect, useState } from "react"
import {
  FiAlertTriangle, FiCheckCircle, FiXCircle, FiFilter, FiSearch,
  FiMessageSquare, FiSend, FiClock
} from "react-icons/fi"
import axiosClient from "../../api/axiosClient"
import useToast from "../../hooks/useToast"

export default function AdminReportManagerPanel() {
  const { showToast } = useToast()

  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState("")
  const [severityFilter, setSeverityFilter] = useState("")

  const [selectedReport, setSelectedReport] = useState(null)
  const [internalNotes, setInternalNotes] = useState("")
  const [newStatus, setNewStatus] = useState("fixed")

  const loadReports = () => {
    setLoading(true)
    const params = {}
    if (statusFilter) params.status = statusFilter
    if (severityFilter) params.severity = severityFilter

    axiosClient.get("/admin/data-reports/", { params })
      .then(({ data }) => setReports(data.results || data || []))
      .catch(() => setReports([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadReports()
  }, [statusFilter, severityFilter])

  const handleResolveReport = async (e) => {
    e.preventDefault()
    if (!selectedReport) return
    try {
      await axiosClient.patch(`/admin/data-reports/${selectedReport.id}/`, {
        status: newStatus,
        internal_notes: internalNotes,
      })
      showToast(`Report #${selectedReport.id} status updated to ${newStatus}`, "success")
      setSelectedReport(null)
      loadReports()
    } catch {
      showToast("Could not update report.", "error")
    }
  }

  return (
    <div className="space-y-6 text-slate-100">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-950 p-6 rounded-3xl border border-slate-800 shadow-xl">
        <div>
          <span className="px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-bold uppercase tracking-wider">
            User Feedback & Error Corrections Queue
          </span>
          <h2 className="text-2xl font-black text-white mt-1">Data Reports & Correction Queue</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Review user-submitted reports for wrong map coordinates, outdated fares, wrong routes, or broken media.
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center text-xs">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white"
        >
          <option value="">All Statuses</option>
          <option value="new">New Reports</option>
          <option value="under_review">Under Review</option>
          <option value="needs_verification">Needs Verification</option>
          <option value="fixed">Fixed & Resolved</option>
          <option value="rejected">Rejected</option>
        </select>

        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white"
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {/* Reports List */}
      <div className="bg-slate-950 border border-slate-800 rounded-3xl overflow-hidden shadow-xl p-5 space-y-4">
        {loading ? (
          <p className="p-8 text-center text-slate-400">Loading reports queue...</p>
        ) : reports.length === 0 ? (
          <p className="p-8 text-center text-slate-400">No open data reports matching filter criteria.</p>
        ) : (
          <div className="space-y-3">
            {reports.map((r) => (
              <div
                key={r.id}
                className="p-4 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
              >
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase ${
                      r.severity === "critical" ? "bg-rose-900/80 text-rose-200" :
                      r.severity === "high" ? "bg-amber-900/80 text-amber-200" : "bg-slate-800 text-slate-300"
                    }`}>
                      {r.severity}
                    </span>
                    <span className="font-black text-white text-sm">
                      {r.report_type.replace("_", " ").toUpperCase()} on {r.destination_name || "General Page"}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-blue-900/60 text-blue-200 text-[10px] font-mono">
                      Status: {r.status}
                    </span>
                  </div>

                  {r.displayed_value && (
                    <p className="text-slate-400">Displayed: <span className="text-rose-300 line-through">{r.displayed_value}</span></p>
                  )}
                  {r.suggested_value && (
                    <p className="text-slate-300">Suggested Fix: <span className="text-emerald-300 font-bold">{r.suggested_value}</span></p>
                  )}
                  {r.description && <p className="text-slate-400 italic">"{r.description}"</p>}
                </div>

                <button
                  onClick={() => {
                    setSelectedReport(r)
                    setInternalNotes(r.internal_notes || "")
                    setNewStatus("fixed")
                  }}
                  className="px-4 py-2 rounded-xl bg-amber-400 hover:bg-amber-500 text-slate-950 font-bold shrink-0 self-start sm:self-center"
                >
                  Investigate & Resolve
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Resolution Modal */}
      {selectedReport && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm">
          <form onSubmit={handleResolveReport} className="bg-slate-950 border border-slate-800 rounded-3xl max-w-md w-full p-6 space-y-4 shadow-2xl text-white text-xs">
            <h3 className="text-lg font-black">Resolve Report #{selectedReport.id}</h3>
            <p className="text-slate-400">{selectedReport.report_type} for {selectedReport.destination_name}</p>

            <div className="space-y-1">
              <label className="font-bold text-slate-300 block">Resolution Status</label>
              <select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white"
              >
                <option value="fixed">Fixed & Verified</option>
                <option value="under_review">Under Review</option>
                <option value="needs_verification">Needs Field Verification</option>
                <option value="rejected">Rejected / Invalid</option>
                <option value="duplicate">Duplicate Report</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="font-bold text-slate-300 block">Internal Admin Notes / Audit Record</label>
              <textarea
                rows="3"
                value={internalNotes}
                onChange={(e) => setInternalNotes(e.target.value)}
                placeholder="Explain what changes were verified and updated in DB..."
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setSelectedReport(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 font-bold"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold"
              >
                Save Resolution
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
