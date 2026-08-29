import { useEffect, useState } from "react"
import { useSearchParams } from "react-router-dom"
import { FiAlertTriangle, FiCheckCircle, FiClock, FiSearch, FiShield } from "react-icons/fi"
import destinationApi from "../../api/destinationApi"
import riskApi from "../../api/riskApi"

const COLORS = {
  low: "bg-emerald-50 text-emerald-800 border-emerald-200",
  moderate: "bg-amber-50 text-amber-800 border-amber-200",
  high: "bg-red-50 text-red-800 border-red-200",
  critical: "bg-red-100 text-red-900 border-red-300",
}

function Badge({ level = "low" }) {
  return <span className={`rounded-full border px-3 py-1 text-xs font-black uppercase ${COLORS[level] || COLORS.low}`}>{level}</span>
}

export default function DestinationRiskPanel() {
  const [params, setParams] = useSearchParams()
  const [query, setQuery] = useState(params.get("destination") || "Pokhara")
  const [suggestions, setSuggestions] = useState([])
  const [risk, setRisk] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const assess = async (value = query) => {
    if (!value.trim()) return
    setLoading(true); setError("")
    try {
      const { data } = await riskApi.assessDestination(value.trim())
      setRisk(data)
      setQuery(data.destination.name)
      setParams({ destination: data.destination.slug }, { replace: true })
      setSuggestions([])
    } catch (err) {
      setRisk(null)
      setError(err.response?.data?.detail || "No approved destination matched that search.")
    } finally { setLoading(false) }
  }

  useEffect(() => {
    const initial = params.get("destination")
    if (initial) assess(initial)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (query.length < 2 || risk?.destination?.name === query) return setSuggestions([])
    const timer = setTimeout(() => {
      destinationApi.autocomplete(query).then(({ data }) => setSuggestions(data.results || data || [])).catch(() => setSuggestions([]))
    }, 220)
    return () => clearTimeout(timer)
  }, [query, risk])

  const current = risk?.current_conditions
  const historical = risk?.historical

  return (
    <section className="rounded-3xl border border-rose-100 bg-white shadow-sm overflow-hidden">
      <div className="p-5 sm:p-6 bg-gradient-to-r from-slate-950 to-rose-950 text-white">
        <div className="flex items-start gap-3 mb-4">
          <FiShield className="text-rose-300 mt-1" size={22} />
          <div><h2 className="font-black text-xl">Destination safety analysis</h2><p className="text-xs text-rose-100/80">Search a place to combine history, traveler records, active observations and the existing model baseline.</p></div>
        </div>
        <form onSubmit={(e) => { e.preventDefault(); assess() }} className="relative flex gap-2">
          <div className="relative flex-1">
            <FiSearch className="absolute left-3 top-3.5 text-gray-400" />
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search Pokhara, Mardi Himal, Rara Lake…" className="w-full rounded-xl bg-white text-gray-900 pl-10 pr-3 py-3 text-sm" />
            {suggestions.length > 0 && <div className="absolute z-20 top-full mt-1 left-0 right-0 rounded-xl bg-white text-gray-900 shadow-xl border overflow-hidden">
              {suggestions.slice(0, 6).map((item) => <button type="button" key={item.id} onClick={() => assess(item.slug)} className="w-full text-left px-4 py-2.5 text-sm hover:bg-gray-50 border-b last:border-0"><b>{item.name}</b><span className="text-xs text-gray-400 ml-2">{item.district}</span></button>)}
            </div>}
          </div>
          <button disabled={loading} className="rounded-xl bg-rose-600 hover:bg-rose-500 px-5 py-3 text-sm font-black disabled:opacity-50">{loading ? "Calculating…" : "Analyze"}</button>
        </form>
        {error && <p className="mt-2 text-xs text-rose-200">{error}</p>}
      </div>

      {risk && <div className="p-5 sm:p-6 space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div><p className="text-xs font-bold uppercase text-gray-400">{risk.destination.district} · {risk.destination.province}</p><h3 className="text-2xl font-black text-gray-900">{risk.destination.name}</h3><p className="text-xs text-gray-500 mt-1">Calculated {new Date(risk.calculated_at).toLocaleString()}</p></div>
          <div className={`rounded-2xl border p-4 min-w-48 ${COLORS[risk.overall.level]}`}><p className="text-[10px] font-black uppercase">Model risk indicator</p><div className="flex items-end gap-2"><b className="text-3xl">{risk.overall.score}</b><Badge level={risk.overall.level} /></div><p className="text-[10px] mt-1">Not an official warning</p></div>
        </div>

        <div className="grid md:grid-cols-3 gap-3">
          <div className="rounded-2xl border p-4"><p className="text-xs font-black text-gray-500 uppercase">Current conditions</p><div className="mt-2 flex items-center justify-between"><b>{current.active_count} active records</b><Badge level={current.level} /></div><p className="text-xs text-gray-500 mt-2">Official warning: <b>{current.official_warning_present ? "Present" : "None recorded"}</b></p></div>
          <div className="rounded-2xl border p-4"><p className="text-xs font-black text-gray-500 uppercase">Historical evidence</p><div className="mt-2 flex items-center justify-between"><b>{historical.incident_count} sourced incidents</b><Badge level={historical.level} /></div><p className="text-xs text-gray-500 mt-2">{historical.baseline_match ? `Baseline: ${historical.baseline_match.destination}${historical.baseline_match.distance_km ? ` (${historical.baseline_match.distance_km} km proxy)` : ""}.` : "No nearby imported baseline."} Dated records remain separate from live warnings.</p></div>
          <div className="rounded-2xl border p-4"><p className="text-xs font-black text-gray-500 uppercase">Traveler evidence</p><b className="block mt-2">{risk.traveler_evidence.report_count} reports</b><p className="text-xs text-gray-500 mt-2">Average safety: <b>{risk.traveler_evidence.average_safety_rating ?? "No ratings"}{risk.traveler_evidence.average_safety_rating ? "/10" : ""}</b></p></div>
        </div>

        {current.items.length > 0 && <div><h4 className="font-black flex items-center gap-2"><FiAlertTriangle className="text-rose-600" /> Current observations & warnings</h4><div className="mt-2 space-y-2">{current.items.map((item) => <div key={item.id} className="rounded-xl border p-3 flex gap-3"><Badge level={item.severity} /><div><b className="text-sm">{item.title}</b><p className="text-xs text-gray-500">{item.source_name} · {new Date(item.observed_at).toLocaleString()}{item.distance_km != null ? ` · ${item.distance_km} km away` : ""}</p><p className="text-xs mt-1">{item.description}</p></div></div>)}</div></div>}

        <div className="grid lg:grid-cols-2 gap-5">
          <div><h4 className="font-black">Risk history by hazard</h4>{historical.breakdown.length ? <div className="mt-2 grid grid-cols-2 gap-2">{historical.breakdown.map((item) => <div className="rounded-xl bg-gray-50 p-3" key={item.hazard_type}><b className="text-sm">{item.label}</b><span className="block text-xs text-gray-500">{item.incident_count} records</span></div>)}</div> : <p className="text-xs text-gray-500 mt-2">No structured historical incidents have been entered for this destination yet.</p>}</div>
          <div><h4 className="font-black flex items-center gap-2"><FiClock /> Incident timeline</h4>{historical.timeline.length ? <div className="mt-2 space-y-2">{historical.timeline.slice(0, 6).map((item) => <div key={item.id} className="border-l-2 border-rose-200 pl-3"><b className="text-sm">{item.title}</b><p className="text-xs text-gray-500">{item.event_date} · {item.source_name || item.source_type} {item.verified && "· verified"}</p></div>)}</div> : <p className="text-xs text-gray-500 mt-2">No dated incident timeline available.</p>}</div>
        </div>

        <div className="rounded-2xl bg-amber-50 border border-amber-200 p-4 text-xs text-amber-900"><FiCheckCircle className="inline mr-1" /><b>Safety note:</b> {risk.disclaimer}</div>
      </div>}
    </section>
  )
}
