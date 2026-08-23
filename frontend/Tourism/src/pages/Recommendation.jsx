import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import {
  FiCompass, FiMapPin, FiArrowRight, FiTrendingUp, FiShield,
  FiSun, FiCoffee, FiZap, FiUsers, FiDroplet, FiWind, FiCamera,
  FiMoon, FiAnchor, FiAperture, FiCheckCircle, FiSliders
} from "react-icons/fi"
import { Link } from "react-router-dom"
import destinationApi from "../api/destinationApi"
import axiosClient from "../api/axiosClient"
import { getDestinationImageUrl } from "../utils/imageUtils"
import PlaceholderImage from "../components/common/PlaceholderImage"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import Breadcrumbs from "../components/common/Breadcrumbs"
import PageHeader from "../components/common/PageHeader"

const GREEN = "#1f6b4d"
const TERRA = "#c2603a"
const GOLD = "#b8862f"

const INTERESTS = [
  { key: "relaxed", label: "Relaxation", icon: FiCoffee },
  { key: "adventure", label: "Adventure", icon: FiZap },
  { key: "family", label: "Family", icon: FiUsers },
  { key: "trekking", label: "Trekking", icon: FiCompass },
  { key: "spiritual", label: "Spiritual", icon: FiDroplet },
  { key: "cultural", label: "Culture", icon: FiAperture },
  { key: "wildlife", label: "Wildlife", icon: FiWind },
  { key: "photography", label: "Photography", icon: FiCamera },
  { key: "romantic", label: "Romantic", icon: FiSun },
  { key: "solitude", label: "Solitude", icon: FiMoon },
  { key: "food", label: "Food", icon: FiAnchor },
]

const SELECTS = {
  budget: [["any", "Any budget"], ["low", "Budget"], ["medium", "Mid-range"], ["high", "Premium"]],
  difficulty: [["any", "Any difficulty"], ["easy", "Easy"], ["moderate", "Moderate"], ["hard", "Hard"]],
  season: [["any", "Any season"], ["spring", "Spring"], ["summer", "Summer / Monsoon"], ["autumn", "Autumn"], ["winter", "Winter"]],
  travelStyle: [["any", "Any group"], ["solo", "Solo"], ["couple", "Couple"], ["family", "Family"]],
}

const PROVINCES = ["", "Koshi", "Madhesh", "Bagmati", "Gandaki", "Lumbini", "Karnali", "Sudurpashchim"]

function SelectField({ label, value, options, onChange }) {
  return (
    <label className="space-y-1.5">
      <span className="text-xs font-bold text-gray-600">{label}</span>
      <select className="input-field bg-white" value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map(([key, text]) => <option key={key} value={key}>{text}</option>)}
      </select>
    </label>
  )
}

function riskColor(level) {
  return { low: "text-emerald-700 bg-emerald-50", moderate: "text-amber-700 bg-amber-50", high: "text-red-700 bg-red-50", critical: "text-red-800 bg-red-100" }[level] || "text-gray-700 bg-gray-50"
}

export default function Recommendation() {
  const [items, setItems] = useState([])
  const [selected, setSelected] = useState(["family", "cultural"])
  const [form, setForm] = useState({ days: 5, budget: "any", difficulty: "any", season: "any", travelStyle: "family", province: "" })
  const [loading, setLoading] = useState(false)
  const [hasRun, setHasRun] = useState(false)
  const [meta, setMeta] = useState(null)
  const [interactionConsent, setInteractionConsent] = useState(false)

  const toggleInterest = (key) => setSelected((current) =>
    current.includes(key) ? current.filter((item) => item !== key) : [...current, key]
  )

  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }))

  async function loadRecommendations() {
    if (!selected.length) return
    setLoading(true)
    setHasRun(true)
    try {
      const { data } = await destinationApi.moodRecommendations({
        mood: selected.join(","), days: form.days, budget: form.budget,
        difficulty: form.difficulty, season: form.season,
        travel_style: form.travelStyle, province: form.province, limit: 18,
      })
      const results = data.results || data.recommendations || (Array.isArray(data) ? data : [])
      setMeta({ source: data.source, version: data.model_version, preferences: data.preferences })
      setItems(results.map((item) => ({ ...item, cover_image_url: getDestinationImageUrl(item) })))
    } catch (error) {
      console.error("Recommendation request failed", error)
      setItems([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadRecommendations() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const trackSelection = (item) => {
    if (!interactionConsent) return
    axiosClient.post("/recommendation-events/", {
      event_type: "select", destination: item.id, score: item.ml_score,
      context: { preferences: meta?.preferences || {}, source: meta?.source }, consented: true,
    }).catch(() => {})
  }

  return (
    <div className="min-h-screen bg-[#faf8f4]">
      <div className="container-app py-8 space-y-6">
        <Breadcrumbs items={[{ label: "Smart Recommendations", to: "/recommendation" }]} />
        <PageHeader
          theme="forest" title="Nepal Trip Recommendation Engine"
          subtitle="Live database matching using your interests, trip length, budget, season and travel style. Newly approved destinations are included automatically."
          icon={FiCompass}
        />

        <section className="rounded-3xl bg-white border border-emerald-900/10 shadow-sm p-5 sm:p-7 space-y-6">
          <div className="flex items-center gap-2">
            <FiSliders style={{ color: TERRA }} />
            <h2 className="font-extrabold text-lg text-gray-900">Build your trip profile</h2>
            <span className="ml-auto text-xs font-bold rounded-full px-3 py-1 bg-emerald-50 text-emerald-800">{selected.length} interests</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
            {INTERESTS.map(({ key, label, icon: Icon }) => {
              const active = selected.includes(key)
              return (
                <button key={key} type="button" onClick={() => toggleInterest(key)}
                  className={`rounded-xl border px-3 py-3 flex items-center gap-2 text-xs font-bold transition ${active ? "text-white shadow" : "bg-white text-gray-600 hover:bg-gray-50"}`}
                  style={active ? { background: GREEN, borderColor: GREEN } : {}}>
                  <Icon size={15} /> {label}
                </button>
              )
            })}
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
            <SelectField label="Budget level" value={form.budget} options={SELECTS.budget} onChange={(v) => update("budget", v)} />
            <SelectField label="Difficulty" value={form.difficulty} options={SELECTS.difficulty} onChange={(v) => update("difficulty", v)} />
            <SelectField label="Travel season" value={form.season} options={SELECTS.season} onChange={(v) => update("season", v)} />
            <SelectField label="Travel group" value={form.travelStyle} options={SELECTS.travelStyle} onChange={(v) => update("travelStyle", v)} />
            <label className="space-y-1.5">
              <span className="text-xs font-bold text-gray-600">Province</span>
              <select className="input-field bg-white" value={form.province} onChange={(e) => update("province", e.target.value)}>
                {PROVINCES.map((p) => <option key={p || "all"} value={p}>{p || "All provinces"}</option>)}
              </select>
            </label>
          </div>

          <div className="grid sm:grid-cols-[1fr_auto] gap-5 items-end">
            <label className="space-y-2">
              <span className="text-xs font-bold text-gray-600">Trip length: <b style={{ color: TERRA }}>{form.days} days</b></span>
              <input className="w-full accent-[#1f6b4d]" type="range" min="1" max="21" value={form.days} onChange={(e) => update("days", Number(e.target.value))} />
            </label>
            <button type="button" onClick={loadRecommendations} disabled={loading || !selected.length}
              className="px-7 py-3 rounded-xl text-white font-black text-sm shadow-lg disabled:opacity-50 flex items-center justify-center gap-2"
              style={{ background: `linear-gradient(135deg, ${GREEN}, ${TERRA})` }}>
              <FiCompass /> {loading ? "Matching live destinations…" : "Find my best destinations"}
            </button>
          </div>
          <label className="flex items-center gap-2 text-[11px] text-gray-600"><input type="checkbox" checked={interactionConsent} onChange={(e)=>setInteractionConsent(e.target.checked)} />Allow my recommendation selections to improve future results. Only consented events are stored.</label>
          <p className="text-[11px] text-gray-500">This is a content-based ranking request, not simulated model training. Results come from approved database destinations; interaction history is used only with consent.</p>
        </section>

        {meta && !loading && (
          <div className="flex flex-wrap items-center gap-2 text-xs text-gray-600">
            <FiCheckCircle className="text-emerald-700" />
            <b>Live database model</b><span>·</span><span>{meta.version || "content-v2"}</span><span>·</span><span>{items.length} unique-photo matches</span>
          </div>
        )}

        {loading ? <Loader /> : items.length ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
            {items.map((item, index) => (
              <motion.article key={item.id} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.03 }}
                className="rounded-3xl overflow-hidden border border-black/5 shadow-sm bg-white flex flex-col">
                <div className="h-52 relative overflow-hidden bg-gray-900">
                  <PlaceholderImage src={item.cover_image_url} title={item.name} alt={item.name} className="w-full h-full" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent" />
                  <span className="absolute top-3 left-3 rounded-full px-3 py-1 bg-white/95 text-emerald-800 text-xs font-black flex items-center gap-1"><FiTrendingUp /> {Math.round((item.ml_score || 0) * 100)}% match</span>
                  <span className={`absolute top-3 right-3 rounded-full px-3 py-1 text-xs font-black ${riskColor(item.risk_summary?.level)}`}><FiShield className="inline mr-1" />{item.risk_summary?.level || "unknown"}</span>
                  <h3 className="absolute bottom-4 left-4 right-4 text-white text-xl font-black">{item.name}</h3>
                </div>
                <div className="p-5 flex-1 space-y-4">
                  <p className="text-xs text-gray-500 flex items-center gap-1"><FiMapPin /> {item.display_city || item.district || "Not recorded"}{item.province ? `, ${item.province}` : ""}</p>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-xl bg-gray-50 p-2"><b className="block text-xs capitalize">{item.difficulty || "Not recorded"}</b><span className="text-[10px] text-gray-400">ranking</span></div>
                    <div className="rounded-xl bg-gray-50 p-2"><b className="block text-xs capitalize">{item.budget_level || "Not recorded"}</b><span className="text-[10px] text-gray-400">rank tag</span></div>
                    <div className="rounded-xl bg-gray-50 p-2"><b className="block text-xs">{item.recommended_days || "—"} days</b><span className="text-[10px] text-gray-400">suggested</span></div>
                  </div>
                  <div>
                    <p className="text-[11px] font-black uppercase tracking-wide" style={{ color: GOLD }}>Why this matches</p>
                    <ul className="mt-1 space-y-1">
                      {(item.why_recommended || []).map((reason) => <li key={reason} className="text-xs text-gray-600 flex gap-2"><FiCheckCircle className="shrink-0 mt-0.5 text-emerald-600" />{reason}</li>)}
                    </ul>
                  </div>
                  {item.safety_context?.current_warning && <div className={`rounded-lg px-2 py-1 text-[10px] font-bold ${item.safety_context.availability === "temporarily_unavailable" ? "bg-red-100 text-red-800" : "bg-amber-50 text-amber-800"}`}>⚠ {item.safety_context.current_warning.severity.toUpperCase()}: {item.safety_context.current_warning.title}{item.safety_context.availability === "temporarily_unavailable" && " · Temporarily unavailable"}</div>}
                  <div className="grid grid-cols-2 gap-2 text-[10px] text-gray-600">
                    <span>🏥 {item.safety_context?.nearest_hospital ? `${item.safety_context.nearest_hospital.distance_km} km` : "Unavailable"}</span>
                    <span>👮 {item.safety_context?.nearest_police ? `${item.safety_context.nearest_police.distance_km} km` : "Unavailable"}</span>
                    <span className="col-span-2">🛣️ {item.safety_context?.route_condition || "No verified route condition"}</span>
                  </div>
                  <p className="text-[10px] text-gray-400">Source: {item.data_source || "Database"} · Best: {item.recommended_season || "Not recorded"}</p>
                </div>
                <div className="p-5 pt-0 grid grid-cols-2 gap-2">
                  <Link to={`/destinations/${item.slug}`} onClick={() => trackSelection(item)} className="rounded-xl py-2.5 text-center text-white text-xs font-bold" style={{ background: GREEN }}>Explore <FiArrowRight className="inline" /></Link>
                  <Link to={`/risk-alerts?destination=${encodeURIComponent(item.slug)}`} className="rounded-xl py-2.5 text-center text-xs font-bold border border-rose-200 text-rose-700">Check risk</Link>
                </div>
              </motion.article>
            ))}
          </div>
        ) : hasRun ? <EmptyState title="No matching destinations" subtitle="Try broadening the province or preference filters." /> : null}
      </div>
    </div>
  )
}
