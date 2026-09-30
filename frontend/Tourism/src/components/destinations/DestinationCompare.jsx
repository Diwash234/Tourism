import { useState, useMemo } from "react"
import { FiX, FiStar, FiMapPin, FiDollarSign, FiClock, FiCheck, FiMinus } from "react-icons/fi"
import { useTranslation } from "../../hooks/useTranslation"
import LazyImage from "../common/LazyImage"
import Badge from "../common/Badge"

/**
 * Side-by-side destination comparison tool.
 * Users can select up to 3 destinations to compare key metrics.
 */
export default function DestinationCompare({ destinations = [] }) {
  const { t } = useTranslation()
  const [selected, setSelected] = useState([])

  const toggleDestination = (dest) => {
    setSelected(prev => {
      if (prev.find(d => d.id === dest.id)) return prev.filter(d => d.id !== dest.id)
      if (prev.length >= 3) return prev
      return [...prev, dest]
    })
  }

  const comparisonData = useMemo(() => {
    if (selected.length < 2) return null

    const metrics = [
      { key: "rating", label: "Rating", icon: FiStar, format: (v) => v?.toFixed(1) || "—" },
      { key: "district", label: "District", icon: FiMapPin, format: (v) => v || "—" },
      { key: "budget_level", label: "Budget", icon: FiDollarSign, format: (v) => v || "—" },
      { key: "recommended_duration", label: "Duration", icon: FiClock, format: (v) => v || "—" },
      { key: "category", label: "Category", icon: null, format: (v) => v || "—" },
      { key: "risk_level", label: "Risk Level", icon: null, format: (v) => v || "—" },
      { key: "elevation", label: "Elevation", icon: null, format: (v) => v ? `${v}m` : "—" },
    ]

    return metrics.map(metric => ({
      ...metric,
      values: selected.map(d => ({
        value: d[metric.key],
        formatted: metric.format(d[metric.key]),
        isBest: false,
      })),
    }))
  }, [selected])

  if (destinations.length < 2) return null

  return (
    <div className="space-y-6">
      {/* Destination Selector */}
      <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
        <h3 className="text-sm font-bold text-gray-900 dark:text-white mb-3">Compare Destinations</h3>
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">Select 2-3 destinations to compare side by side</p>
        <div className="flex flex-wrap gap-2">
          {destinations.map(dest => {
            const isSelected = selected.find(d => d.id === dest.id)
            return (
              <button
                key={dest.id}
                type="button"
                onClick={() => toggleDestination(dest)}
                className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
                  isSelected
                    ? "bg-[var(--ny-green)] text-white shadow-md"
                    : "bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-600"
                }`}
              >
                {isSelected ? <FiCheck size={14} /> : <FiMinus size={14} />}
                {dest.name}
              </button>
            )
          })}
        </div>
      </div>

      {/* Comparison Table */}
      {comparisonData && (
        <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[var(--ny-border)] bg-gray-50 dark:bg-slate-800/50">
                  <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider w-32">
                    Metric
                  </th>
                  {selected.map(dest => (
                    <th key={dest.id} className="px-4 py-3 text-center">
                      <div className="flex flex-col items-center gap-2">
                        <div className="h-16 w-16 rounded-xl overflow-hidden bg-gray-100 dark:bg-slate-700">
                          <LazyImage
                            src={dest.image_url || dest.images?.[0]?.src || "/placeholder-destination.jpg"}
                            alt={dest.name}
                            className="w-full h-full"
                          />
                        </div>
                        <span className="text-sm font-bold text-gray-900 dark:text-white">{dest.name}</span>
                        <button
                          type="button"
                          onClick={() => toggleDestination(dest)}
                          className="p-1 rounded-full text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
                          aria-label={`Remove ${dest.name}`}
                        >
                          <FiX size={14} />
                        </button>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--ny-border)]">
                {comparisonData.map((metric, i) => (
                  <tr key={metric.key} className={i % 2 === 0 ? "bg-white dark:bg-slate-800" : "bg-gray-50/50 dark:bg-slate-800/30"}>
                    <td className="px-4 py-3 text-xs font-semibold text-gray-600 dark:text-gray-400">
                      <div className="flex items-center gap-2">
                        {metric.icon && <metric.icon size={14} className="text-gray-400" />}
                        {metric.label}
                      </div>
                    </td>
                    {metric.values.map((v, j) => (
                      <td key={j} className="px-4 py-3 text-center">
                        <span className={`text-sm font-semibold ${v.isBest ? "text-[var(--ny-green)]" : "text-gray-700 dark:text-gray-300"}`}>
                          {v.formatted}
                        </span>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
