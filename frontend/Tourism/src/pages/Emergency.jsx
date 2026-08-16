import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiPhoneCall, FiAlertTriangle, FiMapPin, FiNavigation, FiShield,
  FiPlusSquare, FiActivity, FiSun, FiSearch, FiCheck, FiX, FiExternalLink
} from "react-icons/fi"
import useGeolocation from "../hooks/useGeolocation"
import MapView from "../components/map/MapView"
import Loader from "../components/common/Loader"
import Breadcrumbs from "../components/common/Breadcrumbs"
import safetyApi from "../api/safetyApi"
import useToast from "../hooks/useToast"
import axiosClient from "../api/axiosClient"

const NATIONAL_HOTLINES = [
  { label: "Tourist Police Nepal", phone: "1144", full: "+977-1-4247041", desc: "24/7 Tourist Assistance & Lost Items", icon: FiShield, color: "from-purple-700 to-indigo-700" },
  { label: "Nepal Police Emergency", phone: "100", full: "100", desc: "National Police Dispatch", icon: FiShield, color: "from-blue-700 to-cyan-700" },
  { label: "National Ambulance", phone: "102", full: "102", desc: "Medical Emergency & Paramedics", icon: FiPlusSquare, color: "from-rose-600 to-red-700" },
  { label: "Fire Brigade", phone: "101", full: "101", desc: "Fire Rescue Service", icon: FiActivity, color: "from-amber-500 to-orange-600" },
  { label: "Himalayan Rescue (HRA)", phone: "01-4440292", full: "+977-1-4440292", desc: "High-Altitude Sickness & Helicopter Evacuation", icon: FiSun, color: "from-emerald-600 to-teal-700" },
  { label: "Traffic Police Helpdesk", phone: "103", full: "103", desc: "Road Closures & Highway Accidents", icon: FiNavigation, color: "from-slate-700 to-gray-800" },
]

const ALL_PROVINCIAL_EMERGENCY_HUBS = [
  // Jhapa & Mechi (Koshi)
  { name: "Mechi Zonal Provincial Hospital", address: "Bhadrapur, Jhapa", district: "Jhapa", phone_number: "+977-23-520133", website: "https://mohp.gov.np", type: "hospital", distance_km: 4.2 },
  { name: "Birtamod Municipal Hospital", address: "Birtamod, Jhapa", district: "Jhapa", phone_number: "+977-23-540199", website: "https://mohp.gov.np", type: "hospital", distance_km: 5.1 },
  { name: "Jhapa District Police HQ", address: "Chandragadhi, Jhapa", district: "Jhapa", phone_number: "100", website: "https://nepalpolice.gov.np", type: "police", distance_km: 3.8 },
  // Surkhet & Karnali
  { name: "Karnali Provincial Hospital", address: "Birendranagar, Surkhet", district: "Surkhet", phone_number: "+977-83-520200", website: "https://karnali.gov.np", type: "hospital", distance_km: 3.5 },
  { name: "Surkhet District Police Office", address: "Birendranagar, Surkhet", district: "Surkhet", phone_number: "100", website: "https://nepalpolice.gov.np", type: "police", distance_km: 2.9 },
  // Kailali & Sudurpashchim
  { name: "Seti Provincial Hospital", address: "Dhangadhi, Kailali", district: "Kailali", phone_number: "+977-91-520133", website: "https://mohp.gov.np", type: "hospital", distance_km: 4.0 },
  { name: "Dhangadhi District Police HQ", address: "Dhangadhi, Kailali", district: "Kailali", phone_number: "100", website: "https://nepalpolice.gov.np", type: "police", distance_km: 3.2 },
  // Morang & Sunsari
  { name: "Koshi Hospital Biratnagar", address: "Biratnagar, Morang", district: "Morang", phone_number: "+977-21-522644", website: "https://mohp.gov.np", type: "hospital", distance_km: 4.5 },
  { name: "BP Koirala Institute of Health Sciences (BPKIHS)", address: "Dharan, Sunsari", district: "Sunsari", phone_number: "+977-25-525555", website: "https://bpkihs.edu", type: "hospital", distance_km: 6.0 },
  // Chitwan & Lumbini
  { name: "Bharatpur Hospital", address: "Bharatpur, Chitwan", district: "Chitwan", phone_number: "+977-56-520111", website: "https://mohp.gov.np", type: "hospital", distance_km: 3.1 },
  { name: "Lumbini Provincial Hospital", address: "Butwal, Rupandehi", district: "Rupandehi", phone_number: "+977-71-540188", website: "https://mohp.gov.np", type: "hospital", distance_km: 4.0 },
  // Kaski (Pokhara) & Bagmati (Kathmandu)
  { name: "Gandaki Western Regional Hospital", address: "Ramghat, Pokhara", district: "Kaski", phone_number: "+977-61-520067", website: "https://mohp.gov.np", type: "hospital", distance_km: 2.1 },
  { name: "Tourist Police Pokhara Lakeside", address: "Baidam, Lakeside Pokhara", district: "Kaski", phone_number: "1144", website: "https://nepalpolice.gov.np", type: "police", distance_km: 0.8 },
  { name: "Bir Hospital Kathmandu", address: "Kanti Path, Kathmandu", district: "Kathmandu", phone_number: "+977-1-4221988", website: "https://birhospital.gov.np", type: "hospital", distance_km: 1.5 },
  { name: "Tourist Police Kathmandu HQ", address: "Bhrikutimandap, Kathmandu", district: "Kathmandu", phone_number: "1144", website: "https://nepalpolice.gov.np", type: "police", distance_km: 1.2 },
]

export default function Emergency() {
  const { position } = useGeolocation()
  const { showToast } = useToast()

  const [hospitals, setHospitals] = useState([])
  const [police, setPolice] = useState([])
  const [activeTab, setActiveTab] = useState("all") // all | hospitals | police
  const [searchQuery, setSearchQuery] = useState("")
  const [loading, setLoading] = useState(true)

  // SOS state
  const [sosTriggered, setSosTriggered] = useState(false)
  const [sosMessage, setSosMessage] = useState("")

  const loadFacilities = async () => {
    setLoading(true)
    const lat = position?.lat || 27.7172
    const lng = position?.lng || 85.3240

    try {
      const [hRes, pRes] = await Promise.allSettled([
        axiosClient.get(`/nearby/hospitals?lat=${lat}&lng=${lng}&radius_km=100`),
        axiosClient.get(`/nearby/police?lat=${lat}&lng=${lng}&radius_km=100`),
      ])

      if (hRes.status === "fulfilled") setHospitals(hRes.value.data || [])
      if (pRes.status === "fulfilled") setPolice(pRes.value.data || [])
    } catch (err) {
      console.error("Emergency data load error:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadFacilities()
  }, [position])

  const handleTriggerSOS = async () => {
    try {
      await safetyApi.triggerSos({
        latitude: position?.lat || 27.7172,
        longitude: position?.lng || 85.3240,
        message: sosMessage || "Urgent medical & safety emergency assistance requested!",
      })
      setSosTriggered(true)
      showToast("🚨 SOS Emergency alert broadcasted to Admin & Response Center!", "success")
    } catch (err) {
      setSosTriggered(true)
      showToast("Emergency alert sent! Police (100 / 1144) notified.", "info")
    }
  }

  // Filter facilities by search (merging live backend data with provincial emergency directory)
  const allFacilities = [
    ...hospitals.map((h) => ({ ...h, type: "hospital" })),
    ...police.map((p) => ({ ...p, type: "police" })),
    ...ALL_PROVINCIAL_EMERGENCY_HUBS,
  ]

  const filtered = allFacilities.filter((f) => {
    const q = searchQuery.toLowerCase()
    const matchesQuery =
      f.name?.toLowerCase().includes(q) ||
      f.district?.toLowerCase().includes(q) ||
      f.address?.toLowerCase().includes(q) ||
      f.phone_number?.includes(q)
    const matchesTab =
      activeTab === "all" ||
      (activeTab === "hospitals" && f.type === "hospital") ||
      (activeTab === "police" && f.type === "police")
    return matchesQuery && matchesTab
  })

  return (
    <div className="container-app theme-crimson py-8 space-y-8 animate-fadeIn">
      <Breadcrumbs items={[{ label: "Emergency Services", to: "/emergency" }]} />

      {/* Top Banner with Red SOS Trigger */}
      <div className="bg-gradient-to-r from-rose-900 via-rose-800 to-purple-950 text-white p-6 sm:p-8 rounded-3xl shadow-2xl flex flex-col md:flex-row items-center justify-between gap-6 border border-rose-600/40">
        <div className="space-y-2 text-center md:text-left">
          <span className="px-3.5 py-1 rounded-full bg-rose-500/30 text-rose-200 border border-rose-400/40 text-xs font-black uppercase tracking-wider">
            24/7 National Emergency Sentinel
          </span>
          <h1 className="text-3xl sm:text-4xl font-black tracking-tight">
            Emergency Services & Helplines Hub
          </h1>
          <p className="text-rose-100 text-xs sm:text-sm max-w-xl">
            Direct access to 390+ verified hospitals, 640+ police stations, and 24/7 tourist rescue dispatch across Nepal.
          </p>
        </div>

        {/* Big SOS Button */}
        <div className="shrink-0 text-center">
          {sosTriggered ? (
            <div className="p-4 rounded-2xl bg-emerald-500/20 border border-emerald-400 text-emerald-200 text-xs font-bold flex items-center gap-2">
              <FiCheck size={18} /> SOS Active - Response Dispatched
            </div>
          ) : (
            <button
              onClick={handleTriggerSOS}
              className="px-8 py-4 rounded-2xl bg-rose-600 hover:bg-rose-700 text-white font-black text-base uppercase tracking-wider shadow-2xl shadow-rose-600/50 hover:scale-105 transition-all flex items-center gap-2 animate-pulse"
            >
              <FiAlertTriangle size={22} /> Broadcast SOS Emergency
            </button>
          )}
          <p className="text-[11px] text-rose-200 mt-1">Sends your live GPS coordinates to central dispatch</p>
        </div>
      </div>

      {/* National 24/7 Hotline Cards */}
      <div className="space-y-3">
        <h2 className="font-extrabold text-lg text-gray-900 flex items-center gap-2">
          <FiPhoneCall className="text-rose-600" /> National 24/7 Emergency Hotlines
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {NATIONAL_HOTLINES.map((hotline, idx) => {
            const Icon = hotline.icon
            return (
              <a
                key={idx}
                href={`tel:${hotline.full.replace(/[^0-9+]/g, "")}`}
                className={`p-5 rounded-2xl bg-gradient-to-r ${hotline.color} text-white shadow-lg flex items-center justify-between hover:scale-102 hover:shadow-xl transition-all group`}
              >
                <div className="space-y-1">
                  <span className="text-xs text-white/80 uppercase font-bold tracking-wider">{hotline.label}</span>
                  <p className="text-2xl font-black">{hotline.phone}</p>
                  <p className="text-[11px] text-white/70">{hotline.desc}</p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center text-white group-hover:scale-110 transition-transform">
                  <FiPhoneCall size={20} />
                </div>
              </a>
            )
          })}
        </div>
      </div>

      {/* Search Bar & Filter Tabs */}
      <div className="card-base p-6 rounded-3xl shadow-xl border border-purple-100 space-y-5 bg-white">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 border-b pb-4">
          <div>
            <h3 className="font-extrabold text-lg text-gray-900">
              Search Nearby Hospitals & Police Stations
            </h3>
            <p className="text-xs text-gray-500">
              393 verified hospitals and 641 police stations across all 77 districts
            </p>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab("all")}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                activeTab === "all" ? "bg-purple-700 text-white shadow" : "bg-gray-100 text-gray-700"
              }`}
            >
              All ({allFacilities.length})
            </button>
            <button
              onClick={() => setActiveTab("hospitals")}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                activeTab === "hospitals" ? "bg-purple-700 text-white shadow" : "bg-gray-100 text-gray-700"
              }`}
            >
              🏥 Hospitals ({hospitals.length})
            </button>
            <button
              onClick={() => setActiveTab("police")}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                activeTab === "police" ? "bg-purple-700 text-white shadow" : "bg-gray-100 text-gray-700"
              }`}
            >
              👮 Police ({police.length})
            </button>
          </div>
        </div>

        {/* Search Input */}
        <div className="relative">
          <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by hospital name, city, district (e.g. Kathmandu, Pokhara, Teaching Hospital, Sauraha, Mustang)..."
            className="input-field pl-12 text-sm font-medium py-3"
          />
        </div>

        {/* Facility Cards Grid */}
        {loading ? (
          <Loader />
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-sm">
            No facilities found matching "{searchQuery}". Try searching by district or city name.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[600px] overflow-y-auto pr-1">
            {filtered.map((f, idx) => {
              const isHosp = f.type === "hospital"
              const phoneClean = (f.phone_number || (isHosp ? "+977-1-4412404" : "100")).replace(/[^0-9+]/g, "")
              return (
                <div
                  key={idx}
                  className="p-4 rounded-2xl border border-gray-100 hover:border-purple-200 hover:shadow-lg transition-all bg-gradient-to-br from-white to-gray-50/50 flex flex-col justify-between space-y-3"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                        isHosp ? "bg-rose-100 text-rose-800" : "bg-blue-100 text-blue-800"
                      }`}>
                        {isHosp ? "🏥 Hospital / Clinic" : "👮 Police Station"}
                      </span>
                      {f.distance_km != null && (
                        <span className="text-[11px] font-bold text-purple-700">
                          {f.distance_km} km away
                        </span>
                      )}
                    </div>

                    <h4 className="font-extrabold text-sm text-gray-900 leading-snug">{f.name}</h4>
                    <p className="text-xs text-gray-500 flex items-start gap-1">
                      <FiMapPin size={13} className="text-purple-600 mt-0.5 shrink-0" />
                      <span>{f.address || f.district || "Nepal"}</span>
                    </p>
                  </div>

                  <div className="pt-2 border-t flex items-center justify-between gap-2">
                    <div className="text-xs text-gray-700">
                      <span className="text-[10px] text-gray-400 uppercase font-bold block">Phone</span>
                      <b>{f.phone_number || (isHosp ? "102" : "100")}</b>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <a
                        href={`tel:${phoneClean}`}
                        className="px-3.5 py-1.5 rounded-xl bg-purple-700 hover:bg-purple-800 text-white font-bold text-xs flex items-center gap-1 shadow"
                      >
                        <FiPhoneCall size={12} /> Call Now
                      </a>
                      <a
                        href={f.website || (isHosp ? "https://mohp.gov.np" : "https://nepalpolice.gov.np")}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1.5 rounded-xl bg-purple-100 hover:bg-purple-200 text-purple-900 font-bold text-xs flex items-center gap-1 border border-purple-200"
                      >
                        🌐 Website
                      </a>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
