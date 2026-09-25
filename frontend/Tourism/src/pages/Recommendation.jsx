import { useEffect, useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { motion } from "framer-motion"
import { FiAlertTriangle, FiAnchor, FiAperture, FiArrowRight, FiBookOpen, FiCamera, FiCheckCircle, FiCompass, FiCoffee, FiDroplet, FiFeather, FiHome, FiMapPin, FiMoon, FiSliders, FiSun, FiUsers, FiWind, FiZap } from "react-icons/fi"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import destinationApi from "../api/destinationApi"
import axiosClient from "../api/axiosClient"
import usePublicConfig from "../hooks/usePublicConfig"
import { getDestinationImageUrl } from "../utils/imageUtils"
import PlaceholderImage from "../components/common/PlaceholderImage"
import EmptyState from "../components/common/EmptyState"
import SkeletonLoader from "../components/common/SkeletonLoader"
import Breadcrumbs from "../components/common/Breadcrumbs"
import PageHeader from "../components/common/PageHeader"

const INTERESTS = [
  { key: "relaxed", label: "Relaxation", icon: FiCoffee },
  { key: "adventure", label: "Adventure", icon: FiZap },
  { key: "family", label: "Family", icon: FiUsers },
  { key: "trekking", label: "Trekking", icon: FiCompass },
  { key: "educational", label: "Education & crafts", icon: FiBookOpen },
  { key: "spiritual", label: "Spiritual", icon: FiDroplet },
  { key: "cultural", label: "Culture", icon: FiAperture },
  { key: "wildlife", label: "Wildlife", icon: FiWind },
  { key: "photography", label: "Photography", icon: FiCamera },
  { key: "romantic", label: "Romantic", icon: FiSun },
  { key: "solitude", label: "Solitude", icon: FiMoon },
  { key: "food", label: "Food & culinary", icon: FiAnchor },
  { key: "nature", label: "Nature & forests", icon: FiFeather },
  { key: "lakes_rivers", label: "Lakes & rivers", icon: FiDroplet },
  { key: "history", label: "History & archaeology", icon: FiBookOpen },
  { key: "artisan_crafts", label: "Arts & handicrafts", icon: FiAperture },
  { key: "village_life", label: "Local life & villages", icon: FiHome },
  { key: "wellness", label: "Wellness & meditation", icon: FiSun },
  { key: "camping", label: "Camping", icon: FiCompass },
  { key: "cycling", label: "Cycling & outdoor activities", icon: FiZap },
  { key: "birdwatching", label: "Birdwatching", icon: FiWind },
]

const SELECTS = {
  budget: [["any", "Any budget"], ["low", "Budget"], ["medium", "Mid-range"], ["high", "Premium"]],
  difficulty: [["any", "Any difficulty"], ["easy", "Easy"], ["moderate", "Moderate"], ["hard", "Hard"]],
  season: [["any", "Any season"], ["spring", "Spring"], ["summer", "Summer / monsoon"], ["autumn", "Autumn"], ["winter", "Winter"]],
  travelStyle: [["any", "Any group"], ["solo", "Solo"], ["couple", "Couple"], ["family", "Family"]],
}

const PROVINCES = ["", "Koshi", "Madhesh", "Bagmati", "Gandaki", "Lumbini", "Karnali", "Sudurpashchim"]

function SelectField({ label, value, options, onChange }) {
  return (
    <label className="space-y-2">
      <span className="text-sm font-semibold text-[var(--ny-text-secondary)]">{label}</span>
      <select className="input-field" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map(([key, text]) => <option key={key} value={key}>{text}</option>)}
      </select>
    </label>
  )
}

export default function Recommendation() {
  const publicConfig = usePublicConfig()
  const configuredInterests = publicConfig.settings?.trip_interests
  const cmsInterests = useMemo(
    () => (Array.isArray(configuredInterests) ? configuredInterests : []).filter((row) => row?.key && row?.label && row.enabled !== false),
    [configuredInterests],
  )
  const interestList = useMemo(
    () => cmsInterests.length ? cmsInterests.map((row) => ({ key: row.key, label: row.label, icon: null, emoji: row.emoji || "✨" })) : INTERESTS,
    [cmsInterests],
  )
  const [selected, setSelected] = useState(["cultural", "nature"])
  const [showMoreInterests, setShowMoreInterests] = useState(false)
  const [form, setForm] = useState({ days: 5, budget: "any", difficulty: "any", season: "any", travelStyle: "family", province: "" })
  const [explorationMode, setExplorationMode] = useState("balanced")
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [hasRun, setHasRun] = useState(false)
  const [meta, setMeta] = useState(null)
  const [loadError, setLoadError] = useState("")
  const [interactionConsent, setInteractionConsent] = useState(false)
  const [nearMe, setNearMe] = useState(null)
  const [locating, setLocating] = useState(false)
  const [geoError, setGeoError] = useState("")

  useEffect(() => {
    const timer = setTimeout(() => {
      const available = new Set(interestList.map((interest) => interest.key))
      setSelected((current) => {
        const retained = current.filter((key) => available.has(key))
        if (retained.length) return retained
        return interestList.slice(0, 2).map((interest) => interest.key)
      })
    }, 0)
    return () => clearTimeout(timer)
  }, [interestList])

  const visibleInterests = showMoreInterests ? interestList : interestList.slice(0, 8)
  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }))
  const toggleInterest = (key) => setSelected((current) => current.includes(key) ? current.filter((item) => item !== key) : [...current, key])

  const requestMyLocation = () => {
    setGeoError("")
    if (!navigator.geolocation) { setGeoError("This browser cannot share a location"); return }
    setLocating(true)
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setNearMe({ lat: +position.coords.latitude.toFixed(5), lng: +position.coords.longitude.toFixed(5) })
        setLocating(false)
      },
      () => {
        setGeoError("Location permission was not granted; recommendations continue without it")
        setLocating(false)
      },
      { enableHighAccuracy: false, maximumAge: 300000, timeout: 10000 },
    )
  }

  const loadRecommendations = async () => {
    if (!selected.length) { setLoadError("Choose at least one experience to continue."); return }
    setLoading(true)
    setHasRun(true)
    setLoadError("")
    try {
      const { data } = await destinationApi.moodRecommendations({
        mood: selected.join(","), days: form.days, budget: form.budget, difficulty: form.difficulty,
        season: form.season, travel_style: form.travelStyle, province: form.province, mode: explorationMode, limit: 18,
        ...(nearMe ? { latitude: nearMe.lat, longitude: nearMe.lng } : {}),
      })
      const results = data.results || data.recommendations || (Array.isArray(data) ? data : [])
      setItems(Array.isArray(results) ? results : [])
      setMeta({ source: data.source, version: data.model_version, preferences: data.preferences })
    } catch {
      setItems([])
      setMeta(null)
      setLoadError("Recommendations are temporarily unavailable. Please try again, or browse the full destination catalogue.")
    } finally {
      setLoading(false)
    }
  }

  const trackSelection = (item) => {
    if (!interactionConsent) return
    axiosClient.post("/recommendation-events/", { event_type: "select", destination: item.id, score: item.ml_score, context: { preferences: meta?.preferences || {}, source: meta?.source }, consented: true }).catch(() => {})
  }

  return (
    <div className="ny-page bg-[var(--ny-bg)]">
      <CMSPageIntro pageKey="recommendation" />
      <div className="container-app space-y-6 py-6 sm:py-8">
        <Breadcrumbs items={[{ label: "Trip recommendations", to: "/recommendation" }]} />
        <PageHeader title="Find your kind of Nepal" subtitle="Tell us what you enjoy and how you want to travel. We will match your choices with recorded destinations — no ratings or details are invented when the catalogue is quiet." icon={FiCompass} />

        <section className="ny-panel p-5 sm:p-7" aria-labelledby="recommendation-preferences">
          <div className="flex flex-col gap-2 border-b border-[var(--ny-border)] pb-5 sm:flex-row sm:items-center sm:justify-between">
            <div><p className="ny-kicker">Step 1 · Your interests</p><h2 id="recommendation-preferences" className="mt-2 !text-xl">What kind of Nepal experience are you looking for?</h2></div>
            <span className="text-sm text-[var(--ny-text-secondary)]">{selected.length} selected</span>
          </div>
          <div className="mt-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
            {visibleInterests.map(({ key, label, icon: Icon, emoji }) => {
              const active = selected.includes(key)
              return <button key={key} type="button" onClick={() => toggleInterest(key)} className={`flex min-h-12 items-center gap-2 rounded-[var(--ny-radius-md)] border px-3 text-left text-sm font-semibold transition ${active ? "border-[var(--ny-green)] bg-[var(--ny-green)] text-white" : "border-[var(--ny-border)] bg-white text-[var(--ny-text-secondary)] hover:border-[var(--ny-green)] hover:bg-[var(--ny-soft-green)] hover:text-[var(--ny-green)]"}`} aria-pressed={active}>{Icon ? <Icon size={17} aria-hidden="true" /> : <span aria-hidden="true">{emoji || "✨"}</span>}<span className="text-xs leading-5">{label}</span></button>
            })}
          </div>
          {interestList.length > 8 && <button type="button" onClick={() => setShowMoreInterests((value) => !value)} className="mt-4 text-sm font-semibold text-[var(--ny-green)] hover:underline">{showMoreInterests ? "Show fewer interests" : "Show more interests"}</button>}

          <div className="mt-8 border-t border-[var(--ny-border)] pt-5">
            <p className="ny-kicker">Step 2 · Your trip</p>
            <h2 className="mt-2 !text-xl">A few practical preferences</h2>
            <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <SelectField label="Budget level" value={form.budget} options={SELECTS.budget} onChange={(value) => update("budget", value)} />
              <SelectField label="Difficulty" value={form.difficulty} options={SELECTS.difficulty} onChange={(value) => update("difficulty", value)} />
              <SelectField label="Travel season" value={form.season} options={SELECTS.season} onChange={(value) => update("season", value)} />
              <SelectField label="Travel group" value={form.travelStyle} options={SELECTS.travelStyle} onChange={(value) => update("travelStyle", value)} />
              <label className="space-y-2"><span className="text-sm font-semibold text-[var(--ny-text-secondary)]">Province</span><select className="input-field" value={form.province} onChange={(event) => update("province", event.target.value)}>{PROVINCES.map((province) => <option key={province || "all"} value={province}>{province || "All provinces"}</option>)}</select></label>
              <label className="space-y-2"><span className="text-sm font-semibold text-[var(--ny-text-secondary)]">Trip length: <strong className="text-[var(--ny-green)]">{form.days} days</strong></span><input className="mt-3 w-full accent-[var(--ny-green)]" type="range" min="1" max="21" value={form.days} onChange={(event) => update("days", Number(event.target.value))} /></label>
            </div>
            <div className="mt-5 grid gap-3 rounded-[var(--ny-radius-md)] border border-[var(--ny-border)] bg-[var(--ny-soft-green)] p-4 sm:grid-cols-[auto_minmax(0,1fr)] sm:items-center">
              <span className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--ny-text)]"><FiSliders size={16} className="text-[var(--ny-green)]" aria-hidden="true" />Exploration mode</span>
              <select className="input-field" value={explorationMode} onChange={(event) => setExplorationMode(event.target.value)} aria-label="Choose exploration mode">
                <option value="popular">More popular places</option>
                <option value="balanced">Balanced variety</option>
                <option value="hidden_gems">Discover hidden gems</option>
              </select>
            </div>
            <div className="mt-5 flex flex-wrap items-center gap-3 rounded-[var(--ny-radius-md)] border border-[var(--ny-border)] bg-[var(--ny-soft-green)] px-4 py-3">
              <button type="button" onClick={() => nearMe ? setNearMe(null) : requestMyLocation()} disabled={locating} className="ny-btn ny-btn-secondary min-h-10 px-3">{locating ? "Finding your location…" : nearMe ? "Stop using my location" : "Use my location (optional)"}</button>
              {nearMe && <span className="text-xs text-[var(--ny-text-secondary)]">Using {nearMe.lat}, {nearMe.lng} for nearby ranking.</span>}
              {geoError && <span className="text-xs text-[var(--ny-danger)]">{geoError}</span>}
            </div>
            <label className="mt-5 flex items-start gap-2 text-xs leading-5 text-[var(--ny-text-secondary)]"><input type="checkbox" checked={interactionConsent} onChange={(event) => setInteractionConsent(event.target.checked)} className="mt-1" />Allow anonymous interaction events to improve future ranking. No account event is stored without this permission.</label>
          </div>

          <div className="mt-6 flex flex-col gap-3 border-t border-[var(--ny-border)] pt-5 sm:flex-row sm:items-center sm:justify-between"><p className="text-sm text-[var(--ny-text-secondary)]">Step 3 · Review matches from the live catalogue.</p><button type="button" onClick={loadRecommendations} disabled={loading || !selected.length} className="ny-btn ny-btn-primary"><FiCompass size={16} aria-hidden="true" />{loading ? "Finding places…" : "Show my recommendations"}</button></div>
          {loadError && <div className="mt-4 flex items-start gap-2 rounded-[var(--ny-radius-md)] border border-[#F3C7C7] bg-[var(--ny-soft-red)] p-4 text-sm text-[var(--ny-danger)]" role="alert"><FiAlertTriangle size={17} className="mt-0.5 shrink-0" aria-hidden="true" />{loadError}</div>}
        </section>

        {meta && !loading && <div className={`flex items-start gap-2 rounded-[var(--ny-radius-md)] border px-4 py-3 text-sm ${meta.offline ? "border-[#E9D59A] bg-[var(--ny-soft-gold)] text-[var(--ny-text-secondary)]" : "border-[var(--ny-border)] bg-[var(--ny-soft-green)] text-[var(--ny-text-secondary)]"}`} role="status"><FiCheckCircle size={16} className={`mt-0.5 shrink-0 ${meta.offline ? "text-[var(--ny-warm-gold)]" : "text-[var(--ny-success)]"}`} aria-hidden="true" /><span>{meta.offline ? "Showing saved catalogue picks while the live recommendation service is unavailable." : `${items.length} recorded destinations matched your selected preferences.`}</span></div>}

        {loading ? <SkeletonLoader count={6} /> : hasRun && items.length ? <section aria-labelledby="recommendation-results"><div className="flex items-end justify-between gap-3"><div><p className="ny-kicker">Your matches</p><h2 id="recommendation-results" className="mt-2">Places to consider</h2></div><p className="text-sm text-[var(--ny-text-secondary)]">{items.length} results</p></div><div className="mt-5 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-2 min-[1240px]:grid-cols-3">{items.map((item, index) => <RecommendationCard key={item.id || item.slug || index} item={item} onSelect={() => trackSelection(item)} />)}</div></section> : hasRun && !loadError ? <EmptyState title="No recommendations found" subtitle="Try broadening your interests or removing a preference." action={<Link to="/destinations" className="ny-btn ny-btn-primary">Browse all destinations</Link>} /> : null}
      </div>
    </div>
  )
}

function RecommendationCard({ item, onSelect }) {
  const image = item.cover_image_url || getDestinationImageUrl(item)
  const reasons = Array.isArray(item.why_recommended) ? item.why_recommended.filter(Boolean) : []
  const location = item.display_city || item.district || item.province
  return <motion.article initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2, delay: 0.02 }} className="ny-card flex h-full flex-col overflow-hidden"><div className="relative h-48 overflow-hidden bg-[#EAF1EE]"><PlaceholderImage src={image} title={item.name} alt={item.name} className="h-full w-full" />{item.category_name && <span className="absolute bottom-3 left-3 rounded-full bg-white/95 px-2.5 py-1 text-xs font-semibold text-[var(--ny-green)]">{item.category_name}</span>}{item.ml_score != null && <span className="absolute right-3 top-3 rounded-full bg-white/95 px-2.5 py-1 text-xs font-semibold text-[var(--ny-green)]">{Math.round(item.ml_score * 100)}% match</span>}</div><div className="flex flex-1 flex-col p-5"><h3 className="text-lg font-bold">{item.name || "Destination information unavailable"}</h3>{location && <p className="mt-1 flex items-center gap-1.5 text-sm text-[var(--ny-text-secondary)]"><FiMapPin size={14} className="text-[var(--ny-green)]" aria-hidden="true" />{location}</p>}<div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-xs text-[var(--ny-text-secondary)]"><span>{item.recommended_days ? `${item.recommended_days} day${item.recommended_days === 1 ? "" : "s"} suggested` : "Duration unavailable"}</span>{item.difficulty && <span>{item.difficulty} difficulty</span>}{item.budget_level && <span>{item.budget_level} budget</span>}</div><div className="mt-4 border-t border-[var(--ny-border)] pt-4"><p className="text-xs font-bold uppercase tracking-[0.08em] text-[var(--ny-green)]">Why we suggested this</p>{reasons.length ? <ul className="mt-2 space-y-2">{reasons.slice(0, 3).map((reason) => <li key={reason} className="flex gap-2 text-sm text-[var(--ny-text-secondary)]"><FiCheckCircle size={15} className="mt-0.5 shrink-0 text-[var(--ny-success)]" aria-hidden="true" />{reason}</li>)}</ul> : <p className="mt-2 text-sm text-[var(--ny-text-secondary)]">Matched against the interests and trip details you selected.</p>}</div>{(item.risk_summary?.level || item.recommended_season) && <p className="mt-4 text-xs text-[var(--ny-text-muted)]">{item.risk_summary?.level ? `Risk information: ${item.risk_summary.level}` : ""}{item.recommended_season ? `${item.risk_summary?.level ? " · " : ""}Best time: ${item.recommended_season}` : ""}</p>}<div className="mt-auto flex flex-wrap gap-2 pt-5">{(item.slug && !item.offline) ? <Link to={`/destinations/${item.slug}`} onClick={onSelect} className="ny-btn ny-btn-primary flex-1">View destination <FiArrowRight size={15} aria-hidden="true" /></Link> : <span className="ny-btn ny-btn-secondary flex-1 cursor-not-allowed">Details unavailable</span>}{(item.slug && !item.offline) && <Link to={`/risk-alerts?destination=${encodeURIComponent(item.slug)}`} className="ny-btn ny-btn-secondary">Safety</Link>}</div></div></motion.article>
}
