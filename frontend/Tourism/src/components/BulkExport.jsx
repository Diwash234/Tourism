import { useState, useCallback } from "react"
import { FiDownload, FiFileText, FiFile, FiLoader, FiAlertCircle, FiShield } from "react-icons/fi"
import axiosClient from "../api/axiosClient"
import useToast from "../hooks/useToast"
import useAuth from "../hooks/useAuth"

const DATA_TYPES = [
  { value: "destinations", label: "Destinations" },
  { value: "hotels", label: "Hotels" },
  { value: "bookings", label: "Bookings" },
  { value: "reviews", label: "Reviews" },
]

const FORMATS = [
  { value: "csv", label: "CSV", icon: FiFileText },
  { value: "json", label: "JSON", icon: FiFile },
]

/**
 * Bulk data export component. Only visible to admin users.
 * Supports CSV and JSON formats with progress indication.
 */
const BulkExport = () => {
  const showToast = useToast()
  const { isAdmin } = useAuth()
  const [dataType, setDataType] = useState("destinations")
  const [format, setFormat] = useState("csv")
  const [exporting, setExporting] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState(null)

  const handleExport = useCallback(async () => {
    setExporting(true)
    setProgress(0)
    setError(null)

    try {
      // Simulate progress since we can't get real download progress easily
      const progressInterval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 15, 90))
      }, 200)

      // The export route is admin-namespaced: /admin/export/ (BulkExportView).
      // It was called as "/export/", which does not exist, so every export
      // here 404'd and the button reported "Export failed".
      const response = await axiosClient.get("/admin/export/", {
        params: { type: dataType, format },
        responseType: "blob",
      })

      clearInterval(progressInterval)
      setProgress(100)

      // Extract filename from Content-Disposition header
      const disposition = response.headers["content-disposition"]
      const filenameMatch = disposition?.match(/filename="?([^"]+)"?/)
      const filename = filenameMatch
        ? filenameMatch[1]
        : `${dataType}-export.${format}`

      // Trigger download
      const blob = new Blob([response.data], {
        type: format === "csv" ? "text/csv" : "application/json",
      })
      const url = URL.createObjectURL(blob)
      const link = document.createElement("a")
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      showToast(`Export completed: ${filename}`, "success")
    } catch (err) {
      // BulkExportView reports failures as {"error": {"code", "message"}},
      // so the message is nested one level deeper than a normal DRF error.
      const data = err?.response?.data
      const msg =
        data?.error?.message || data?.detail || data?.message ||
        "Export failed. Please try again."
      setError(msg)
      showToast(msg, "error")
    } finally {
      setExporting(false)
      setProgress(0)
    }
  }, [dataType, format, showToast])

  // Only render for admin users
  if (!isAdmin) {
    return (
      <div className="ny-card p-5">
        <div className="flex items-center gap-2 text-ny-text-muted">
          <FiShield size={18} />
          <span className="text-sm">Admin access required to use bulk export.</span>
        </div>
      </div>
    )
  }

  return (
    <div className="ny-card p-5">
      <h3 className="text-lg font-bold text-ny-text flex items-center gap-2 mb-1">
        <FiDownload size={18} className="text-ny-green" />
        Bulk Export
      </h3>
      <p className="text-sm text-ny-text-secondary mb-4">
        Export platform data for backup or analysis.
      </p>

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-ny-soft-red border border-red-200 mb-4" role="alert">
          <FiAlertCircle size={16} className="text-ny-danger flex-shrink-0" />
          <span className="text-sm text-ny-danger">{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
        {/* Data type selector */}
        <div>
          <label className="ny-field-label" htmlFor="export-data-type">Data Type</label>
          <select
            id="export-data-type"
            value={dataType}
            onChange={(e) => setDataType(e.target.value)}
            className="input-field"
            disabled={exporting}
          >
            {DATA_TYPES.map((dt) => (
              <option key={dt.value} value={dt.value}>{dt.label}</option>
            ))}
          </select>
        </div>

        {/* Format selector */}
        <div>
          <label className="ny-field-label">Format</label>
          <div className="flex gap-2">
            {FORMATS.map(({ value, label, icon: Icon }) => (
              <button
                key={value}
                type="button"
                onClick={() => setFormat(value)}
                disabled={exporting}
                className={`flex-1 flex items-center justify-center gap-2 p-3 rounded-xl border transition-colors ${
                  format === value
                    ? "border-ny-green bg-ny-soft-green text-ny-green"
                    : "border-ny-border text-ny-text-secondary hover:border-ny-green/50"
                }`}
              >
                <Icon size={16} />
                <span className="text-sm font-semibold">{label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Progress bar */}
      {exporting && (
        <div className="mb-4">
          <div className="flex items-center justify-between text-xs text-ny-text-muted mb-1">
            <span>Exporting {dataType} as {format.toUpperCase()}...</span>
            <span>{progress}%</span>
          </div>
          <div className="h-2 rounded-full bg-gray-200 overflow-hidden">
            <div
              className="h-full rounded-full bg-ny-green transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      <button
        onClick={handleExport}
        disabled={exporting}
        className="ny-btn ny-btn-primary w-full"
        type="button"
      >
        {exporting ? (
          <>
            <FiLoader size={16} className="animate-spin" />
            Exporting...
          </>
        ) : (
          <>
            <FiDownload size={16} />
            Export {DATA_TYPES.find((d) => d.value === dataType)?.label} as {format.toUpperCase()}
          </>
        )}
      </button>
    </div>
  )
}

export default BulkExport
