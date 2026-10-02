// Honest route-quality labels for every route shown to travellers.
// "osrm" = real road routing; the bundled GraphML graph gives an approximate
// road corridor; straight-line is only a distance estimate, never a road.
const QUALITY = {
  road: { key: "road", label: "Road route", detail: "Street-level road routing (OSRM). Suitable for turn-by-turn navigation.", tone: "border-emerald-200 bg-emerald-50 text-emerald-800" },
  corridor: { key: "corridor", label: "Approximate corridor", detail: "Estimated along the bundled national road graph — follows main roads only; not turn-by-turn accurate.", tone: "border-amber-200 bg-amber-50 text-amber-900" },
  straight: { key: "straight_line", label: "Straight-line estimate", detail: "Direct distance between points — not a road. Actual travel is longer.", tone: "border-red-200 bg-red-50 text-red-800" },
}

export function routeQuality(source) {
  const s = String(source || "").toLowerCase()
  if (s === "osrm") return QUALITY.road
  if (s.includes("straight")) return QUALITY.straight
  if (s.includes("graph") || s.includes("corridor") || s.includes("bundled")) return QUALITY.corridor
  return { key: "unknown", label: "Route source unknown", detail: "Treat distances and times as estimates.", tone: "border-slate-200 bg-slate-50 text-slate-700" }
}

export function RouteQualityBadge({ source, className = "" }) {
  const q = routeQuality(source)
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-bold ${q.tone} ${className}`} title={q.detail} data-testid="route-quality" data-quality={q.key}>
      {q.label}
    </span>
  )
}
