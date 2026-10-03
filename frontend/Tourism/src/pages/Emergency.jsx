import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import VerificationBadge from "../components/common/VerificationBadge"
import { useI18n } from "../i18n"
import { Link, useSearchParams } from "react-router-dom"
import { FiActivity, FiAlertTriangle, FiCheckCircle, FiExternalLink, FiMapPin, FiNavigation, FiPhoneCall, FiSearch, FiShield, FiTool } from "react-icons/fi"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import Breadcrumbs from "../components/common/Breadcrumbs"
import EmptyState from "../components/common/EmptyState"
import SkeletonLoader from "../components/common/SkeletonLoader"
import useGeolocation from "../hooks/useGeolocation"
import useToast from "../hooks/useToast"
import useAuth from "../hooks/useAuth"
import safetyApi from "../api/safetyApi"
import emergencyApi from "../api/emergencyApi"
import destinationApi from "../api/destinationApi"
import PrintableTravelBrief from "../components/itinerary/PrintableTravelBrief"

const TYPE_META = {
  hospital: { key: "emergency.type_hospital", fallback: "Hospital / clinic", icon: FiActivity, color: "bg-[var(--ny-soft-red)] text-[var(--ny-danger)]" },
  police: { key: "emergency.type_police", fallback: "Police station", icon: FiShield, color: "bg-[var(--ny-soft-blue)] text-[var(--ny-info)]" },
  ambulance: { key: "emergency.type_ambulance", fallback: "Ambulance", icon: FiNavigation, color: "bg-[var(--ny-soft-green)] text-[var(--ny-green)]" },
  blood_bank: { key: "emergency.type_blood_bank", fallback: "Blood bank", icon: FiTool, color: "bg-[var(--ny-soft-red)] text-[var(--ny-danger)]" },
  pharmacy: { key: "emergency.type_pharmacy", fallback: "Pharmacy", icon: FiActivity, color: "bg-[var(--ny-soft-green)] text-[var(--ny-green)]" },
  fire_station: { key: "emergency.type_fire", fallback: "Fire and rescue", icon: FiAlertTriangle, color: "bg-[var(--ny-soft-gold)] text-[var(--ny-warning)]" },
  tourist_police: { key: "emergency.type_tourist_police", fallback: "Tourist police", icon: FiShield, color: "bg-[var(--ny-soft-green)] text-[var(--ny-green)]" },
  traffic_police: { key: "emergency.type_traffic_police", fallback: "Traffic police", icon: FiNavigation, color: "bg-[var(--ny-soft-blue)] text-[var(--ny-info)]" },
}

// Quick picks for the empty state. These are only search terms: the backend
// resolves each one to a real destination record and its stored coordinates.
const QUICK_PLACES = ["Kathmandu", "Pokhara", "Chitwan", "Lumbini", "Dhangadhi", "Biratnagar"]

const phoneHref = (value) => `tel:${String(value || "").replace(/[^0-9+]/g, "")}`

function FacilityCard({ facility }) {
  const { t } = useI18n()
  const meta = TYPE_META[facility.type] || { key: "emergency.type_default", fallback: "Emergency facility", icon: FiActivity, color: "bg-[var(--ny-soft-green)] text-[var(--ny-green)]" }
  const typeLabel = t(meta.key) !== meta.key ? t(meta.key) : meta.fallback
  const Icon = meta.icon
  const hasPhone = Boolean(facility.phone_number) && !facility.phone_is_national_fallback
  const hasCoordinates = facility.latitude != null && facility.longitude != null
  const directions = hasCoordinates ? `https://www.google.com/maps/dir/?api=1&destination=${facility.latitude},${facility.longitude}` : null
  return (
    <article className="ny-card flex h-full flex-col p-5">
      <div className="flex items-start justify-between gap-3"><span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${meta.color}`}><Icon size={13} aria-hidden="true" />{typeLabel}</span>{facility.distance_km != null && <span title={facility.travel_time_basis || t("emergency.straight_line_note")} className="shrink-0 text-right text-xs font-semibold text-[var(--ny-text-secondary)]">{facility.distance_km} {t("common.km")}{facility.estimated_travel_time_min != null ? <span className="block text-xs font-medium">{t("emergency.approx_min", { n: facility.estimated_travel_time_min })}</span> : <span className="block text-xs font-medium">{t("emergency.road_time_unavailable")}</span>}</span>}</div>
      {facility.image_url && <img loading="lazy" decoding="async" src={facility.image_url} alt="" className="mt-4 h-32 w-full rounded-[var(--ny-radius-md)] object-cover" />}
      <div className="mt-4 flex-1"><h3 className="text-base font-bold">{facility.name || t("emergency.facility_name_unavailable")}</h3><p className="mt-1 flex gap-1.5 text-sm text-[var(--ny-text-secondary)]"><FiMapPin size={14} className="mt-0.5 shrink-0 text-[var(--ny-green)]" aria-hidden="true" />{facility.address || facility.district || t("emergency.address_unavailable")}</p></div>
      {facility.outside_requested_radius && <p className="mt-3 rounded-[var(--ny-radius-sm)] bg-[var(--ny-soft-gold)] px-3 py-2 text-xs text-[var(--ny-warning)]">{t("emergency.outside_radius")}</p>}
      {facility.phone_is_national_fallback && <p className="mt-2 text-xs text-[var(--ny-text-secondary)]">{t("emergency.phone_fallback_note")}</p>}
      <div className="mt-4 flex flex-wrap gap-2 border-t border-[var(--ny-border)] pt-4">{hasPhone ? <a href={phoneHref(facility.phone_number)} aria-label={t("emergency.call_facility", { name: facility.name || t("emergency.facility_name_unavailable") })} className="ny-btn ny-btn-danger min-h-10 flex-1 px-3"><FiPhoneCall size={15} aria-hidden="true" />{facility.phone_number}</a> : <span className="ny-btn ny-btn-secondary min-h-10 flex-1 cursor-not-allowed">{t("emergency.phone_unavailable")}</span>}{hasCoordinates && <Link to={`/navigation?dest=${encodeURIComponent(facility.name || "")}`} className="ny-btn ny-btn-secondary min-h-10 px-3"><FiNavigation size={15} aria-hidden="true" />{t("emergency.route")}</Link>}{directions && <a href={directions} target="_blank" rel="noreferrer" className="ny-btn ny-btn-secondary min-h-10 px-3" aria-label={t("emergency.open_in_maps")}><FiExternalLink size={15} aria-hidden="true" /></a>}</div>
      <div className="mt-3 flex flex-wrap gap-2 text-xs text-[var(--ny-text-muted)]"><VerificationBadge record={facility} />{facility.source_name && <span>· {t("emergency.source")}: {facility.source_name}</span>}{facility.opening_hours && <span>· {facility.opening_hours}</span>}{facility.updated_at && <span>· {t("emergency.updated")} {new Date(facility.updated_at).toLocaleDateString()}</span>}</div>
    </article>
  )
}

// Last successful national-hotline response, kept on this device so the
// numbers still show without signal. Always labelled with when it was saved.
const HOTLINE_STORE_KEY = "ny.emergency.national_hotlines.v1"
const saveHotlines = (rows) => {
  try { localStorage.setItem(HOTLINE_STORE_KEY, JSON.stringify({ rows, saved_at: new Date().toLocaleString() })) } catch { /* storage full or disabled */ }
}
const readSavedHotlines = () => {
  try { return JSON.parse(localStorage.getItem(HOTLINE_STORE_KEY) || "null") } catch { return null }
}

export default function Emergency() {
  const { t } = useI18n()
  const { position, locating, error: geoError, retry: requestLocation } = useGeolocation({ auto: false })
  const { showToast } = useToast()
  const { isAuthenticated } = useAuth()
  const [params, setParams] = useSearchParams()
  const [query, setQuery] = useState("")
  const [suggestions, setSuggestions] = useState([])
  const [activeSuggestion, setActiveSuggestion] = useState(-1)
  const [directory, setDirectory] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState("all")
  const [radius, setRadius] = useState(50)
  const [sosStatus, setSosStatus] = useState("")
  const [nationalHotlines, setNationalHotlines] = useState([])
  const [nationalLoading, setNationalLoading] = useState(true)
  const [nationalError, setNationalError] = useState("")
  const [loadedInitial, setLoadedInitial] = useState(false)
  const [showPrintBrief, setShowPrintBrief] = useState(false)
  const lookupRequestRef = useRef(0)
  const sosRequestRef = useRef(0)
  const selectedReference = params.get("destination")

  const [savedCopyAt, setSavedCopyAt] = useState("")
  const loadNationalHotlines = useCallback(() => {
    setNationalLoading(true)
    setNationalError("")
    setSavedCopyAt("")
    return emergencyApi.nationalHotlines()
      .then(({ data, headers }) => {
        const rows = Array.isArray(data?.national_hotlines) ? data.national_hotlines : []
        setNationalHotlines(rows)
        if (headers?.["x-ny-offline"]) {
          setSavedCopyAt(readSavedHotlines()?.saved_at || "an earlier visit")
        } else if (rows.length) {
          saveHotlines(rows)
        }
      })
      .catch(() => {
        // Offline or server down: fall back to the last copy this device saw.
        const saved = readSavedHotlines()
        if (saved?.rows?.length) {
          setNationalHotlines(saved.rows)
          setSavedCopyAt(saved.saved_at)
        } else {
          setNationalError(t("emergency.contacts_load_error"))
        }
      })
      .finally(() => setNationalLoading(false))
  }, [])

  useEffect(() => {
    const timer = setTimeout(() => loadNationalHotlines(), 0)
    return () => clearTimeout(timer)
  }, [loadNationalHotlines])

  const loadDestination = async (reference) => {
    if (!reference) return
    const requestId = ++lookupRequestRef.current
    sosRequestRef.current += 1
    setSosStatus("")
    setDirectory(null)
    setLoading(true)
    try {
      const { data } = await emergencyApi.forDestination(reference, { radius_km: radius, limit: 10 })
      if (requestId !== lookupRequestRef.current) return
      setDirectory(data)
      setQuery(data.location?.destination_name || "")
      setParams({ destination: data.location?.destination_slug || reference }, { replace: true })
      setSuggestions([])
       setActiveSuggestion(-1)
    } catch (error) {
      if (requestId !== lookupRequestRef.current) return
      setDirectory(null)
      showToast(error.response?.data?.detail || t("emergency.destination_unavailable"), "error")
    } finally {
      if (requestId === lookupRequestRef.current) {
        setLoading(false)
        setLoadedInitial(true)
      }
    }
  }

  const loadCoordinates = async (lat, lng) => {
    const requestId = ++lookupRequestRef.current
    sosRequestRef.current += 1
    setSosStatus("")
    setDirectory(null)
    setLoading(true)
    try {
      const { data } = await emergencyApi.nearby(lat, lng, { radius_km: radius, limit: 10 })
      if (requestId !== lookupRequestRef.current) return
      setDirectory(data)
      setQuery("")
    } catch {
      if (requestId !== lookupRequestRef.current) return
      setDirectory(null)
      showToast(t("emergency.nearby_unavailable"), "error")
    } finally {
      if (requestId === lookupRequestRef.current) {
        setLoading(false)
        setLoadedInitial(true)
      }
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      if (selectedReference && !loadedInitial) loadDestination(selectedReference)
      else if (position && !loadedInitial) loadCoordinates(position.lat, position.lng)
      else if (!selectedReference && !position && !loadedInitial) { setLoading(false); setLoadedInitial(true) }
    }, 0)
    return () => clearTimeout(timer)
  // The lookup functions intentionally use the current radius and toast
  // context; the initial-location effect should run only for these inputs.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [position, selectedReference, loadedInitial])

  useEffect(() => {
    if (query.trim().length < 2 || query === directory?.location?.destination_name) {
      const clearTimer = setTimeout(() => { setSuggestions([]); setActiveSuggestion(-1) }, 0)
      return () => clearTimeout(clearTimer)
    }
    const timer = setTimeout(() => {
      destinationApi.autocomplete(query)
        .then(({ data }) => setSuggestions(data.results || data || []))
        .catch(() => setSuggestions([]))
        .finally(() => setActiveSuggestion(-1))
    }, 220)
    return () => clearTimeout(timer)
  }, [query, directory])

  const facilities = useMemo(() => {
    if (!directory) return []
    const all = [...(directory.hospitals || []), ...(directory.police || []), ...(directory.specialized_contacts || [])]
    if (activeTab === "all") return all
    if (activeTab === "hospital") return all.filter((item) => item.type === "hospital")
    if (activeTab === "police") return all.filter((item) => item.type === "police" || item.type === "tourist_police")
    if (activeTab === "pharmacy") return all.filter((item) => item.type === "pharmacy")
    if (activeTab === "fire") return all.filter((item) => item.type === "fire_station")
    return all.filter((item) => !["hospital", "police"].includes(item.type))
  }, [directory, activeTab])

  const refreshRadius = () => {
    if (directory?.location?.destination_slug) loadDestination(directory.location.destination_slug)
    else if (directory?.location) loadCoordinates(directory.location.latitude, directory.location.longitude)
  }

  const handleSOS = async () => {
    const location = directory?.location
    if (!location) { showToast(t("emergency.sos_need_location"), "info"); return }
    const requestId = ++sosRequestRef.current
    const requestedLocation = { ...location }
    setSosStatus("sending")
    try {
      await safetyApi.triggerSos({ latitude: requestedLocation.latitude, longitude: requestedLocation.longitude, message: `Emergency assistance requested${requestedLocation.destination_name ? ` near ${requestedLocation.destination_name}` : ""}.` })
      if (requestId !== sosRequestRef.current) return
      setSosStatus("sent")
      showToast(t("emergency.sos_recorded"), "success")
    } catch {
      if (requestId !== sosRequestRef.current) return
      setSosStatus("error")
      showToast(t("emergency.sos_failed"), "error")
    }
  }

  const locationTitle = directory?.location?.destination_name || (directory?.location?.source === "coordinates" ? "your selected location" : "Nepal")
  const hotlines = directory?.national_hotlines?.length ? directory.national_hotlines : nationalHotlines
  const counts = directory?.counts || {}

  return (
    <div className="ny-page container-app space-y-6 py-6 sm:py-8" data-testid="emergency-page">
      <CMSPageIntro pageKey="emergency" />
      <Breadcrumbs items={[{ label: t("emergency.title"), to: "/emergency" }]} />
      <header className="overflow-hidden rounded-[var(--ny-radius-xl)] border border-[#E9B9B9] bg-[var(--ny-soft-red)]">
        <div className="flex flex-col gap-6 p-6 sm:p-8 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="ny-kicker !border !border-[#E9B9B9] !bg-white/70 !text-[var(--ny-danger)]">{t("emergency.kicker")}</p>
            <h1 className="mt-3 !text-3xl !text-[var(--ny-text)] sm:!text-4xl">{t("emergency.hero_title")}</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--ny-text-secondary)]">{t("emergency.hero_subtitle")}</p>
          </div>
          <div className="shrink-0 flex flex-col gap-2">
            <div className="flex flex-wrap items-center gap-2">
              {isAuthenticated ? (
                <button type="button" onClick={handleSOS} disabled={sosStatus === "sending"} className="ny-btn ny-btn-danger min-h-12 px-5"><FiAlertTriangle size={17} aria-hidden="true" />{sosStatus === "sending" ? t("emergency.sos_sending") : sosStatus === "sent" ? t("emergency.sos_sent") : t("emergency.sos_cta")}</button>
              ) : (
                <Link to={`/login?next=${encodeURIComponent("/emergency")}`} className="ny-btn ny-btn-danger min-h-12 px-5"><FiAlertTriangle size={17} aria-hidden="true" />{t("emergency.sos_login")}</Link>
              )}
              <button
                type="button"
                onClick={() => setShowPrintBrief(true)}
                className="ny-btn min-h-12 px-4 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-slate-800 font-bold text-xs flex items-center justify-center gap-1.5 shadow-2xs"
                title="Open and print offline emergency medical SOS card and rescue directory"
              >
                <span>🖨️</span>
                <span>{t("emergency.offline_dossier")}</span>
              </button>
            </div>
            <p className="max-w-xs text-xs leading-5 text-[var(--ny-text-secondary)]">{t("emergency.dispatch_note")}</p>
          </div>
        </div>
      </header>

      <section className="ny-panel p-5 sm:p-6" aria-labelledby="emergency-search-title"><h2 id="emergency-search-title" className="text-xl">{t("emergency.find_help_title")}</h2><form onSubmit={(event) => { event.preventDefault(); loadDestination(query) }} className="mt-4 flex flex-col gap-3 sm:flex-row"><div className="relative min-w-0 flex-1"><FiSearch size={17} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--ny-text-muted)]" aria-hidden="true" /><label htmlFor="emergency-search" className="sr-only">{t("emergency.search_label")}</label><input
                  id="emergency-search"
                  data-testid="emergency-search"
                  className="input-field pl-11"
                  value={query}
                  onChange={(event) => { setQuery(event.target.value); setActiveSuggestion(-1) }}
                  onKeyDown={(event) => {
                    if (event.key === "ArrowDown" && suggestions.length) { event.preventDefault(); setActiveSuggestion((value) => Math.min(value + 1, Math.min(suggestions.length, 7) - 1)) }
                    if (event.key === "ArrowUp" && suggestions.length) { event.preventDefault(); setActiveSuggestion((value) => Math.max(value - 1, 0)) }
                    if (event.key === "Enter" && activeSuggestion >= 0 && suggestions[activeSuggestion]) { event.preventDefault(); loadDestination(suggestions[activeSuggestion].slug) }
                    if (event.key === "Escape") { setSuggestions([]); setActiveSuggestion(-1) }
                  }}
                  placeholder={t("emergency.search_placeholder")}
                  autoComplete="off"
                  role="combobox"
                  aria-expanded={suggestions.length > 0}
                  aria-controls="emergency-suggestions"
                  aria-autocomplete="list"
                  aria-activedescendant={activeSuggestion >= 0 ? `emergency-suggestion-${activeSuggestion}` : undefined}
                />{suggestions.length > 0 && <div id="emergency-suggestions" role="listbox" aria-label={t("emergency.search_label")} className="absolute inset-x-0 top-full z-30 mt-1 overflow-hidden rounded-[var(--ny-radius-md)] border border-[var(--ny-border)] bg-white shadow-[var(--ny-shadow-elevated)]">{suggestions.slice(0, 7).map((item) => <button type="button" key={item.id} id={`emergency-suggestion-${suggestions.indexOf(item)}`} role="option" aria-selected={suggestions.indexOf(item) === activeSuggestion} onClick={() => loadDestination(item.slug)} className="flex w-full items-center justify-between gap-3 border-b border-[var(--ny-border)] px-4 py-3 text-left text-sm last:border-0 hover:bg-[var(--ny-soft-green)]"><span className="font-semibold">{item.name}</span><span className="truncate text-xs text-[var(--ny-text-secondary)]">{item.district || item.province || t("emergency.address_unavailable")}</span></button>)}</div>}</div><button type="submit" className="ny-btn ny-btn-primary">{t("emergency.find_help")}</button></form><div className="mt-4 flex flex-wrap items-center gap-3 text-sm"><button type="button" onClick={() => position ? loadCoordinates(position.lat, position.lng) : requestLocation()} disabled={locating} className="ny-btn ny-btn-secondary min-h-10 px-3"><FiMapPin size={15} aria-hidden="true" />{position ? t("emergency.use_gps") : locating ? t("emergency.finding_location") : geoError ? t("emergency.try_location_again") : t("emergency.use_my_location")}</button>{geoError && !position && <span role="alert" className="text-xs text-[var(--ny-warning)]">{t("emergency.location_error")} ({typeof geoError === "string" ? geoError : geoError?.message || t("emergency.location_denied")}). {t("emergency.search_instead")}</span>}<label className="flex items-center gap-2 font-semibold text-[var(--ny-text-secondary)]">{t("emergency.radius")} <select value={radius} onChange={(event) => setRadius(Number(event.target.value))} className="input-field min-h-10 w-auto py-2"><option value="10">10 {t("common.km")}</option><option value="25">25 {t("common.km")}</option><option value="50">50 {t("common.km")}</option><option value="100">100 {t("common.km")}</option><option value="200">200 {t("common.km")}</option></select></label><button type="button" onClick={refreshRadius} disabled={!directory} className="text-sm font-semibold text-[var(--ny-green)] hover:underline">{t("emergency.apply_radius")}</button></div></section>

      {!directory && (
        <section className="ny-panel p-5 sm:p-6" aria-labelledby="national-hotlines-title">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 id="national-hotlines-title" className="text-xl">{t("emergency.verified_contacts")}</h2>
              <p className="mt-1 text-sm text-[var(--ny-text-secondary)]">{t("emergency.contacts_subtitle")}</p>
            </div>
            {nationalError && <button type="button" onClick={loadNationalHotlines} className="ny-btn ny-btn-secondary min-h-11 text-sm">{t("emergency.retry_contacts")}</button>}
          </div>
          {savedCopyAt && !nationalLoading && <p role="status" className="mt-4 rounded-[var(--ny-radius-md)] border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">{t("emergency.offline_copy")} ({savedCopyAt}).</p>}{nationalLoading ? <p className="mt-4 text-sm text-[var(--ny-text-secondary)]">{t("emergency.loading_contacts")}</p> : nationalError ? <p role="alert" className="mt-4 rounded-[var(--ny-radius-md)] border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">{nationalError}</p> : hotlines.length > 0 ? <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{hotlines.map((item) => item.phone_number ? <a key={item.type || item.phone_number} href={phoneHref(item.phone_number)} className="ny-card flex flex-col p-4 transition hover:-translate-y-0.5"><span className="text-xs font-bold uppercase tracking-[0.08em] text-[var(--ny-text-secondary)]">{item.name}</span><strong className="mt-2 text-2xl text-[var(--ny-green)]">{item.phone_number}</strong><span className="mt-1 text-xs text-[var(--ny-text-secondary)]">{item.description || t("emergency.contact_record")}</span></a> : <div key={item.type || item.name} className="ny-card flex flex-col p-4"><span className="text-xs font-bold uppercase tracking-[0.08em] text-[var(--ny-text-secondary)]">{item.name}</span><strong className="mt-2 text-lg text-[var(--ny-text-secondary)]">{t("emergency.phone_unavailable_long")}</strong><span className="mt-1 text-xs text-[var(--ny-text-secondary)]">{t("emergency.no_number_listed")}</span></div>)}</div> : <p className="mt-4 text-sm text-[var(--ny-text-secondary)]">{t("emergency.no_contacts")}</p>}
        </section>
      )}

      {loading ? <SkeletonLoader count={3} type="card" /> : !directory ? <EmptyState title={t("emergency.choose_place_title")} subtitle={t("emergency.choose_place_sub")} action={<div className="flex flex-wrap justify-center gap-2"><button type="button" onClick={() => position ? loadCoordinates(position.lat, position.lng) : requestLocation()} disabled={locating} className="ny-btn ny-btn-primary"><FiMapPin size={15} aria-hidden="true" />{locating ? t("emergency.finding_location") : t("emergency.use_my_location")}</button>{QUICK_PLACES.map((place) => <button key={place} type="button" onClick={() => { setQuery(place); loadDestination(place) }} className="ny-btn ny-btn-secondary">{place}</button>)}</div>} /> : <>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-xs font-bold uppercase tracking-[0.08em] text-[var(--ny-text-muted)]">{t("emergency.coverage_around")}</p><h2 className="mt-1">{locationTitle}</h2><p className="mt-1 text-sm text-[var(--ny-text-secondary)]">{directory.location?.district || t("emergency.address_unavailable")}{directory.location?.province ? ` · ${directory.location.province}` : ""} · {directory.radius_km || radius} {t("common.km")} {t("emergency.radius").toLowerCase()}</p></div>{(directory.coverage_gap || (counts.hospitals_within_radius === 0 && counts.police_within_radius === 0)) && <p className="max-w-md rounded-[var(--ny-radius-md)] border border-[#E9D39A] bg-[var(--ny-soft-gold)] p-3 text-sm text-[var(--ny-warning)]">{t("emergency.coverage_gap")} <Link to="/submit-service" className="font-semibold underline">{t("emergency.submit_facility")}</Link></p>}</div>

        {directory && hotlines.length > 0 && <section aria-labelledby="national-hotlines-title"><h2 id="national-hotlines-title" className="text-xl">{t("emergency.verified_contacts")}</h2><p className="mt-1 text-sm text-[var(--ny-text-secondary)]">{t("emergency.directory_supplied")}</p><div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{hotlines.map((item) => item.phone_number ? <a key={item.type || item.phone_number} href={phoneHref(item.phone_number)} className="ny-card flex flex-col p-4 transition hover:-translate-y-0.5"><span className="text-xs font-bold uppercase tracking-[0.08em] text-[var(--ny-text-secondary)]">{item.name}</span><strong className="mt-2 text-2xl text-[var(--ny-green)]">{item.phone_number}</strong><span className="mt-1 text-xs text-[var(--ny-text-secondary)]">{item.description || t("emergency.contact_record")}</span></a> : <div key={item.type || item.name} className="ny-card flex flex-col p-4"><span className="text-xs font-bold uppercase tracking-[0.08em] text-[var(--ny-text-secondary)]">{item.name}</span><strong className="mt-2 text-lg text-[var(--ny-text-secondary)]">{t("emergency.phone_unavailable_long")}</strong><span className="mt-1 text-xs text-[var(--ny-text-secondary)]">{t("emergency.no_number_listed")}</span></div>)}</div></section>}

        <section className="ny-panel p-5 sm:p-6" aria-labelledby="facilities-title"><div className="flex flex-col gap-4 border-b border-[var(--ny-border)] pb-5 lg:flex-row lg:items-end lg:justify-between"><div><h2 id="facilities-title" className="text-xl">{t("emergency.nearest_facilities")}</h2><p className="mt-1 text-sm text-[var(--ny-text-secondary)]">{t("emergency.coverage_label")}: {counts.database_hospitals ?? "—"} {t("emergency.hospitals_unit")} · {counts.database_police_stations ?? "—"} {t("emergency.police_unit")}</p></div><div className="ny-horizontal-scroll flex gap-2" role="group" aria-label={t("emergency.nearest_facilities")}>{[["all", t("emergency.filter_all")], ["hospital", t("emergency.filter_hospitals")], ["police", t("emergency.filter_police")], ["pharmacy", t("emergency.filter_pharmacy")], ["fire", t("emergency.filter_fire")]].map(([key, label]) => <button key={key} data-testid={`emergency-tab-${key}`} type="button" onClick={() => setActiveTab(key)} className={`min-h-10 whitespace-nowrap rounded-full border px-3 text-xs font-semibold ${activeTab === key ? "border-[var(--ny-green)] bg-[var(--ny-green)] text-white" : "border-[var(--ny-border)] bg-white text-[var(--ny-text-secondary)] hover:bg-[var(--ny-soft-green)]"}`} aria-pressed={activeTab === key}>{label}</button>)}</div></div>{facilities.length ? <div className="mt-5 grid gap-5 md:grid-cols-2 xl:grid-cols-3">{facilities.map((facility) => <FacilityCard key={facility.id || `${facility.type}-${facility.name}`} facility={facility} />)}</div> : <div className="mt-5"><EmptyState title={t("emergency.no_filter_match_title")} subtitle={t("emergency.no_filter_match_sub")} action={<Link to="/submit-service" className="ny-btn ny-btn-secondary">{t("emergency.submit_facility_short")}</Link>} /></div>}</section>
        {directory.notice && <p className="flex items-start gap-2 rounded-[var(--ny-radius-md)] border border-[var(--ny-border)] bg-white p-4 text-sm text-[var(--ny-text-secondary)]"><FiCheckCircle size={16} className="mt-0.5 shrink-0 text-[var(--ny-success)]" aria-hidden="true" />{directory.notice}</p>}
      </>}

      {/* Printable Emergency SOS Dossier & Medical ID Card */}
      <PrintableTravelBrief
        isOpen={showPrintBrief}
        onClose={() => setShowPrintBrief(false)}
      />
    </div>
  )
}
