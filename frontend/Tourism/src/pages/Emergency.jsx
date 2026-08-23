import { useEffect, useMemo, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import {
  FiPhoneCall, FiAlertTriangle, FiMapPin, FiNavigation, FiShield,
  FiPlusSquare, FiActivity, FiSearch, FiCheckCircle, FiExternalLink
} from "react-icons/fi"
import useGeolocation from "../hooks/useGeolocation"
import Loader from "../components/common/Loader"
import Breadcrumbs from "../components/common/Breadcrumbs"
import safetyApi from "../api/safetyApi"
import emergencyApi from "../api/emergencyApi"
import destinationApi from "../api/destinationApi"
import useToast from "../hooks/useToast"

const TYPE_META = {
  hospital: { label: "Hospital / Clinic", icon: "🏥", color: "bg-rose-100 text-rose-800", fallback: "102" },
  police: { label: "Police Station", icon: "👮", color: "bg-blue-100 text-blue-800", fallback: "100" },
  ambulance: { label: "Ambulance", icon: "🚑", color: "bg-emerald-100 text-emerald-800", fallback: "102" },
  blood_bank: { label: "Blood Bank", icon: "🩸", color: "bg-red-100 text-red-800", fallback: "102" },
  bank: { label: "Bank", icon: "🏦", color: "bg-cyan-100 text-cyan-800", fallback: "" },
  atm: { label: "ATM", icon: "🏧", color: "bg-cyan-100 text-cyan-800", fallback: "" },
  pharmacy: { label: "Pharmacy", icon: "💊", color: "bg-green-100 text-green-800", fallback: "102" },
  fire_station: { label: "Fire & Rescue", icon: "🚒", color: "bg-orange-100 text-orange-800", fallback: "101" },
  tourist_police: { label: "Tourist Police", icon: "🛡️", color: "bg-purple-100 text-purple-800", fallback: "1144" },
  traffic_police: { label: "Traffic Police", icon: "🚦", color: "bg-slate-100 text-slate-800", fallback: "103" },
}

const HOTLINE_COLORS = {
  tourist_police: "from-purple-700 to-indigo-700", police: "from-blue-700 to-cyan-700",
  ambulance: "from-rose-600 to-red-700", fire_station: "from-amber-500 to-orange-600",
  traffic_police: "from-slate-700 to-gray-800",
}

function phoneHref(value) {
  return `tel:${String(value || "").replace(/[^0-9+]/g, "")}`
}

function FacilityCard({ facility }) {
  const meta = TYPE_META[facility.type] || TYPE_META.hospital
  const directions = `https://www.google.com/maps/dir/?api=1&destination=${facility.latitude},${facility.longitude}`
  return (
    <article className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm hover:shadow-lg transition space-y-3">
      <div className="flex items-start justify-between gap-2">
        <span className={`px-2.5 py-1 rounded-full text-[10px] font-black uppercase ${meta.color}`}>{meta.icon} {meta.label}</span>
        {facility.distance_km != null && <span className="text-xs font-black text-purple-700">{facility.distance_km} km · ~{facility.estimated_travel_time_min} min</span>}
      </div>
      {facility.image_url && <img src={facility.image_url} alt={facility.name} className="h-32 w-full rounded-xl object-cover" />}
      <div>
        <h3 className="font-extrabold text-sm text-gray-900">{facility.name}</h3>
        <p className="text-xs text-gray-500 mt-1 flex gap-1"><FiMapPin className="shrink-0 mt-0.5" />{facility.address || facility.district || "Nepal"}</p>
      </div>
      {facility.outside_requested_radius && <p className="text-[10px] rounded-lg bg-amber-50 text-amber-800 px-2 py-1">No service found inside the selected radius; showing the nearest known result.</p>}
      {facility.phone_is_national_fallback && <p className="text-[10px] text-gray-500">Local phone unavailable in the source dataset — national {meta.label.toLowerCase()} line shown.</p>}
      <div className="flex gap-2 pt-2 border-t">
        {(facility.phone_number || meta.fallback) ? <a href={phoneHref(facility.phone_number || meta.fallback)} className="flex-1 rounded-xl bg-purple-700 text-white py-2 text-center text-xs font-black"><FiPhoneCall className="inline mr-1" />{facility.phone_number || meta.fallback}</a> : <span className="flex-1 rounded-xl bg-gray-100 text-gray-500 py-2 text-center text-xs font-bold">Phone unavailable</span>}
        {facility.latitude != null && <a href={directions} target="_blank" rel="noreferrer" className="rounded-xl border border-purple-200 text-purple-800 px-3 py-2 text-xs font-bold"><FiNavigation className="inline" /> Route</a>}
      </div>
      <div className="flex flex-wrap gap-2 text-[10px] text-gray-400">
        <span>{facility.verified ? "✓ Verified" : "Verification pending"}</span>
        {facility.opening_hours && <span>· {facility.opening_hours}</span>}
        {facility.updated_at && <span>· Updated {new Date(facility.updated_at).toLocaleDateString()}</span>}
      </div>
      <a href={facility.source_url || "https://mohp.gov.np/"} target="_blank" rel="noreferrer" className="block text-[10px] text-gray-400 hover:underline">Source: {facility.source_name || "Emergency directory"} <FiExternalLink className="inline" /></a>
    </article>
  )
}

export default function Emergency() {
  const { position } = useGeolocation()
  const { showToast } = useToast()
  const [params, setParams] = useSearchParams()
  const [query, setQuery] = useState("")
  const [suggestions, setSuggestions] = useState([])
  const [directory, setDirectory] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState("all")
  const [radius, setRadius] = useState(50)
  const [sosStatus, setSosStatus] = useState("")
  const [loadedInitial, setLoadedInitial] = useState(false)

  const loadDestination = async (reference) => {
    if (!reference) return
    setLoading(true)
    try {
      const { data } = await emergencyApi.forDestination(reference, { radius_km: radius, limit: 10 })
      setDirectory(data)
      setQuery(data.location.destination_name)
      setParams({ destination: data.location.destination_slug }, { replace: true })
      setSuggestions([])
    } catch (error) {
      showToast(error.response?.data?.detail || "Destination emergency data unavailable", "error")
    } finally { setLoading(false); setLoadedInitial(true) }
  }

  const loadCoordinates = async (lat, lng) => {
    setLoading(true)
    try {
      const { data } = await emergencyApi.nearby(lat, lng, { radius_km: radius, limit: 10 })
      setDirectory(data); setQuery("")
    } catch { showToast("Nearby emergency directory unavailable", "error") }
    finally { setLoading(false); setLoadedInitial(true) }
  }

  useEffect(() => {
    const selected = params.get("destination")
    if (selected && !loadedInitial) loadDestination(selected)
    else if (position && !loadedInitial) loadCoordinates(position.lat, position.lng)
    else if (!selected && !position && !loadedInitial) loadCoordinates(27.7172, 85.3240)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [position])

  useEffect(() => {
    if (query.length < 2 || query === directory?.location?.destination_name) return setSuggestions([])
    const timer = setTimeout(() => destinationApi.autocomplete(query)
      .then(({ data }) => setSuggestions(data.results || data || []))
      .catch(() => setSuggestions([])), 220)
    return () => clearTimeout(timer)
  }, [query, directory])

  const refreshRadius = () => {
    if (directory?.location?.destination_slug) loadDestination(directory.location.destination_slug)
    else if (directory?.location) loadCoordinates(directory.location.latitude, directory.location.longitude)
  }

  const handleSOS = async () => {
    const location = directory?.location
    if (!location) return
    setSosStatus("sending")
    try {
      await safetyApi.triggerSos({ latitude: location.latitude, longitude: location.longitude, message: `Emergency assistance requested${location.destination_name ? ` near ${location.destination_name}` : ""}.` })
      setSosStatus("sent")
      showToast("SOS recorded by the platform. Call 100/102/1144 for immediate dispatch.", "success")
    } catch {
      setSosStatus("call")
      showToast("The platform could not confirm dispatch. Call 100, 102 or 1144 now.", "error")
    }
  }

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

  const locationTitle = directory?.location?.destination_name || (directory?.location?.source === "coordinates" ? "your selected location" : "Nepal")
  const risk = directory?.risk?.overall

  return (
    <div className="container-app py-8 space-y-7 animate-fadeIn">
      <Breadcrumbs items={[{ label: "Emergency Services", to: "/emergency" }]} />

      <section className="rounded-3xl bg-gradient-to-r from-rose-900 via-rose-800 to-purple-950 text-white p-6 sm:p-8 shadow-2xl">
        <div className="flex flex-col lg:flex-row gap-6 justify-between">
          <div><span className="rounded-full bg-rose-500/30 px-3 py-1 text-xs font-black uppercase">Nepal emergency locator</span><h1 className="text-3xl sm:text-4xl font-black mt-2">Nearest Help for Every Destination</h1><p className="text-sm text-rose-100 mt-2 max-w-2xl">Search any approved Nepal destination. Results are calculated from its coordinates and ranked by actual distance.</p></div>
          <div className="shrink-0"><button onClick={handleSOS} disabled={sosStatus === "sending"} className="rounded-2xl bg-rose-600 hover:bg-rose-500 px-7 py-4 font-black shadow-xl disabled:opacity-60"><FiAlertTriangle className="inline mr-2" />{sosStatus === "sending" ? "Recording SOS…" : sosStatus === "sent" ? "SOS Recorded" : "Emergency SOS"}</button><p className="text-[10px] text-rose-200 mt-2 max-w-56">For immediate dispatch, always call 100, 102, or Tourist Police 1144.</p></div>
        </div>
      </section>

      <section className="rounded-3xl bg-white border shadow-sm p-5 space-y-4">
        <form onSubmit={(e) => { e.preventDefault(); loadDestination(query) }} className="relative flex gap-2">
          <div className="relative flex-1"><FiSearch className="absolute left-4 top-3.5 text-gray-400" /><input className="input-field pl-11" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search Pokhara, Rara Lake, Mardi Himal, Janakpur…" />
            {suggestions.length > 0 && <div className="absolute z-30 top-full mt-1 left-0 right-0 bg-white border rounded-xl shadow-2xl overflow-hidden">{suggestions.slice(0, 7).map((item) => <button type="button" key={item.id} onClick={() => loadDestination(item.slug)} className="block w-full text-left px-4 py-3 text-sm hover:bg-gray-50 border-b last:border-0"><b>{item.name}</b><span className="ml-2 text-xs text-gray-400">{item.district}, {item.province}</span></button>)}</div>}
          </div>
          <button className="rounded-xl bg-purple-700 text-white px-6 font-black text-sm">Find help</button>
        </form>
        <div className="flex flex-wrap items-center gap-3 text-xs"><button onClick={() => position && loadCoordinates(position.lat, position.lng)} className="rounded-lg border px-3 py-2 font-bold"><FiMapPin className="inline" /> Use my GPS</button><label className="font-bold text-gray-600">Radius <select value={radius} onChange={(e) => setRadius(Number(e.target.value))} className="ml-1 rounded-lg border p-2"><option value="10">10 km</option><option value="25">25 km</option><option value="50">50 km</option><option value="100">100 km</option><option value="200">200 km</option></select></label><button onClick={refreshRadius} className="text-purple-700 font-black">Apply radius</button></div>
      </section>

      {loading ? <Loader /> : directory && <>
        <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-xs font-black uppercase text-gray-400">Emergency coverage around</p><h2 className="text-2xl font-black">{locationTitle}</h2><p className="text-xs text-gray-500">{directory.location.district} {directory.location.province && `· ${directory.location.province}`} · {directory.radius_km} km radius</p>{directory.location.coordinate_note && <p className="text-[10px] text-gray-400">Location basis: {directory.location.coordinate_note}</p>}{(directory.coverage_gap || (directory.counts?.hospitals_within_radius === 0 && directory.counts?.police_within_radius === 0)) && <p className="mt-2 text-xs text-amber-900 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">There is no verified local hospital or police record for this place in the directory. National hotlines still work. An administrator can add an accurate facility with coordinates, or you can <Link to="/submit-service" className="font-black underline">submit a facility</Link> for review.</p>}</div>{risk && <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3"><p className="text-[10px] font-black uppercase text-amber-800">Risk model indicator</p><b className="text-xl uppercase text-amber-900">{risk.level} · {risk.score}</b><p className="text-[10px] text-amber-700">Not an official warning</p></div>}</div>

        <section className="space-y-3"><h2 className="font-extrabold text-lg flex items-center gap-2"><FiPhoneCall className="text-rose-600" /> Verified national hotlines</h2><div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-3">{directory.national_hotlines.map((item) => <a key={item.type} href={phoneHref(item.phone_number)} className={`rounded-2xl p-4 text-white bg-gradient-to-br ${HOTLINE_COLORS[item.type]} shadow`}><span className="text-[10px] font-black uppercase opacity-80">{item.name}</span><b className="block text-2xl">{item.phone_number}</b><p className="text-[10px] opacity-75">{item.description}</p></a>)}</div></section>

        <section className="rounded-3xl border bg-white p-5 space-y-4"><div className="flex flex-wrap justify-between gap-3"><div><h2 className="font-black text-xl">Nearest emergency facilities</h2><p className="text-xs text-gray-500">Database coverage: {directory.counts.database_hospitals} hospitals · {directory.counts.database_police_stations} police stations</p></div><div className="flex flex-wrap gap-2">{[["all", "All"], ["hospital", `Hospitals (${directory.counts.hospitals_within_radius})`], ["police", `Police (${directory.counts.police_within_radius})`], ["pharmacy", `Pharmacy (${directory.counts.pharmacy_within_radius || 0})`], ["fire", `Fire (${directory.counts.fire_within_radius || 0})`], ["specialized", "Ambulance & other"]].map(([key, label]) => <button key={key} onClick={() => setActiveTab(key)} className={`rounded-xl px-3 py-2 text-xs font-bold ${activeTab === key ? "bg-purple-700 text-white" : "bg-gray-100"}`}>{label}</button>)}</div></div>
          {facilities.length ? <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">{facilities.map((facility) => <FacilityCard key={facility.id} facility={facility} />)}</div> : <div className="rounded-2xl bg-amber-50 border border-amber-200 p-5 text-sm text-amber-900 space-y-2"><p><FiActivity className="inline mr-2" />{activeTab === "pharmacy" ? "No verified pharmacy is currently listed for this area. This platform does not invent pharmacies. You can submit a pharmacy for admin verification." : "No local specialized record is available. Use national Ambulance 102 or Fire 101."}</p><Link to="/submit-service" className="inline-block font-black underline">Submit a facility</Link></div>}
        </section>

        <div className="rounded-2xl border border-blue-200 bg-blue-50 p-4 text-xs text-blue-900"><FiCheckCircle className="inline mr-1" /><b>Data note:</b> {directory.notice}</div>
      </>}
    </div>
  )
}
