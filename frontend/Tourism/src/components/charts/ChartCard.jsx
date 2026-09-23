import { useMemo } from "react"
import "./ChartSetup"
import { Bar, Line, Pie } from "react-chartjs-2"
import ErrorBoundary from "../common/ErrorBoundary"

// Brand palette for charts (JS literals — Tailwind classes don't apply here).
export const CHART_COLORS = ["#1B8A5A", "#0B3D91", "#F59E0B", "#DC143C", "#3f66b8", "#70B1AB"]

const TYPES = { bar: Bar, line: Line, pie: Pie }

/** Content signature — array identity is ignored so callers can pass literals. */
export function signatureFor(type, labels, data, label) {
  return `${type}|${label}|${JSON.stringify(labels)}|${JSON.stringify(data)}`
}

export function hasChartData(labels, data) {
  return Array.isArray(labels) && labels.length > 0 && Array.isArray(data) && data.length > 0
}

/** Builds the chart.js config for a given chart type. Pure — unit testable. */
export function makeChartData(type, labels, data, label, colors) {
  const style =
    type === "pie"
      ? { backgroundColor: colors }
      : type === "line"
      ? { borderColor: colors[0], backgroundColor: "rgba(27,138,90,0.15)", tension: 0.4, fill: true }
      : { backgroundColor: colors[0], borderRadius: 6 }
  return { labels, datasets: [{ label, data, ...style }] }
}

export function makeChartOptions(type, showLegend) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: type === "pie" ? true : showLegend } },
  }
}

/**
 * Single place that renders a chart.js chart.
 *
 * Two fixes live here:
 * 1. `data`/`options` are memoised. Previously every card passed fresh object
 *    literals on each render, so react-chartjs-2's
 *    `[options, data.labels, data.datasets]` effect fired on every render and
 *    drove its `destroyChart()` + `setTimeout(renderChart)` path — the race
 *    that surfaced in production as `TypeError: destroy is not a function`.
 * 2. Charts are keyed by a content signature, so a dataset/type change remounts
 *    through the guarded mount/unmount path instead of the async redraw path.
 * Empty datasets render a placeholder rather than an empty chart.
 */
export default function ChartCard({
  type,
  title,
  labels = [],
  data = [],
  label = "Value",
  showLegend = false,
  colors = CHART_COLORS,
}) {
  const Chart = TYPES[type] || Bar

  const hasData = hasChartData(labels, data)

  // Callers pass inline array literals, so identity changes on every render.
  // Key the memo on the *content* signature and read the latest values from a
  // ref — that keeps `data`/`options` referentially stable and stops
  // react-chartjs-2 re-running its update/redraw effect on every render.
  const signature = signatureFor(type, labels, data, label)
  // No ref needed: when `signature` changes the memo recomputes during that
  // render, and its closure already holds the current labels/data/label/colors.
  const chartData = useMemo(
    () => makeChartData(type, labels, data, label, colors),
    // Recompute only when the CONTENT signature changes — callers pass inline
    // array literals whose identity changes every render (intentional).
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [signature, type]
  )

  const options = useMemo(() => makeChartOptions(type, showLegend), [type, showLegend])

  return (
    <div className="card-base p-5">
      {title && <h4 className="font-semibold mb-4">{title}</h4>}
      {!hasData ? (
        <div className="h-52 flex items-center justify-center text-sm text-gray-400 border border-dashed border-gray-200 rounded-xl">
          No data to chart yet
        </div>
      ) : (
        <ErrorBoundary name={`chart-${type}`}>
          <div className="h-52">
            <Chart key={signature} data={chartData} options={options} />
          </div>
        </ErrorBoundary>
      )}
    </div>
  )
}
