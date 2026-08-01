import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiPhoneCall, FiAlertOctagon, FiMapPin, FiNavigation,
  FiShield, FiPlusSquare, FiActivity, FiSun, FiHome, FiUsers,
  FiWifiOff, FiHeart, FiX,
} from "react-icons/fi"

import useGeolocation from "../hooks/useGeolocation"
import MapView from "../components/map/MapView"
import Loader from "../components/common/Loader"
import { getEmergency } from "../services/mlService"
import emergencyService from "../api/emergencyService"

// National Nepal hotlines — these are fixed numbers, always dialable
// regardless of GPS/backend availability, so they're hardcoded rather
// than fetched. The `type` maps to EmergencyContact.ContactType so a
// live, nearby record (with real distance + is_24_hours) can be matched
// in underneath each one when available.
const HOTLINES = [
  { type: "police", label: "Police", phone: "100", icon: FiShield, color: "bg-himalaya-500" },
  { type: "ambulance", label: "Ambulance", phone: "102", icon: FiPlusSquare, color: "bg-nepalred-500" },
  { type: "fire_station", label: "Fire Station", phone: "101", icon: FiActivity, color: "bg-saffron-500" },
  { type: "tourism_office", label: "Tourism Office", phone: "1144", icon: FiSun, color: "bg-forest-500" },
  { type: "ward_office", label: "Local Ward Office", phone: null, icon: FiHome, color: "bg-himalaya-600" },
  { type: "embassy", label: "Embassy", phone: null, icon: FiUsers, color: "bg-forest-600" },
]

const Emergency = () => {
  const { position } = useGeolocation()
  const [sosOpen, setSosOpen] = useState(false)

  const [hospitals, setHospitals] = useState([])
  const [police, setPolice] = useState([])
  const [nearbyByType, setNearbyByType] = useState({}) // { police: {name, distance_km, is_24_hours, ...} }
  const [loading, setLoading] = useState(true)

  async function loadEmergencyFacilities() {
    if (!position) return

    try {
      setLoading(true)

      const [hospitalResponse, policeResponse, nearestResponse] = await Promise.all([
        getEmergency(position.lat, position.lng, "hospital", 5),
        getEmergency(position.lat, position.lng, "police_station", 5),
        emergencyService.nearby(position.lat, position.lng).catch(() => ({ data: [] })),
      ])

      setHospitals(hospitalResponse.facilities || [])
      setPolice(policeResponse.facilities || [])

      // Index the structured EmergencyContact results by type for quick
      // lookup under each hotline card.
      const list = nearestResponse.data?.results || nearestResponse.data || []
      const byType = {}
      list.forEach((c) => { byType[c.contact_type] = c })
      setNearbyByType(byType)
    } catch (error) {
      console.log("Emergency error:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (position) loadEmergencyFacilities()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [position])

  const directionsUrl = (lat, lng) => `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`

  return (
    <div className="container-app py-10 fade-in">
      <div className="flex items-center justify-between flex-wrap gap-4 mb-2">
        <h1 className="section-title flex items-center gap-2 text-nepalred-500 mb-0">
          <FiAlertOctagon />
          Emergency Assistance
        </h1>

        {/* NEW: prominent SOS button per the brief. There is no single
            "911-style" universal emergency number in Nepal, so tapping
            this opens a quick-dial sheet with the 3 most critical
            numbers rather than pretending one button dials everything. */}
        <button
          onClick={() => setSosOpen(true)}
          className="pulse-soft flex items-center gap-2 bg-nepalred-500 hover:bg-nepalred-600 text-white font-bold px-6 py-3 rounded-full shadow-premium hover:shadow-premium-hover transition-all"
        >
          <FiAlertOctagon size={20} /> SOS — Get Help Now
        </button>
      </div>

      <p className="text-gray-500 text-sm mb-6">
        Find nearby hospitals, police stations and emergency services based on your current location.
      </p>

      {/* NEW: big per-service emergency cards — national hotline number
          always shown, plus the nearest real contact of that type (with
          live distance and 24-hour status) when one exists in range. */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-10">
        {HOTLINES.map(({ type, label, phone, icon: Icon, color }, i) => {
          const nearest = nearbyByType[type]
          const callNumber = phone || nearest?.phone_number

          return (
            <motion.div
              key={type}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
              className="card-base p-4 flex flex-col"
            >
              <div className={`w-10 h-10 rounded-xl ${color} text-white flex items-center justify-center mb-3`}>
                <Icon size={18} />
              </div>
              <p className="font-bold text-dark text-sm">{label}</p>

              {nearest ? (
                <>
                  <p className="text-xs text-gray-500 mt-1 truncate">{nearest.name}</p>
                  <div className="flex items-center gap-2 text-xs text-gray-400 mt-1">
                    {nearest.distance_km != null && <span>{nearest.distance_km} km away</span>}
                    <span className={nearest.is_24_hours ? "text-forest-600 font-medium" : "text-saffron-600 font-medium"}>
                      {nearest.is_24_hours ? "Open 24hrs" : "Hours vary"}
                    </span>
                  </div>
                </>
              ) : (
                <p className="text-xs text-gray-400 mt-1">National hotline</p>
              )}

              <div className="flex gap-2 mt-3">
                {callNumber && (
                  <a
                    href={`tel:${callNumber}`}
                    className="flex-1 flex items-center justify-center gap-1 text-xs font-semibold bg-gray-50 hover:bg-gray-100 text-dark rounded-lg py-2"
                  >
                    <FiPhoneCall size={12} /> Call
                  </a>
                )}
                {nearest?.latitude && (
                  <a
                    href={directionsUrl(nearest.latitude, nearest.longitude)}
                    target="_blank"
                    rel="noreferrer"
                    className="flex-1 flex items-center justify-center gap-1 text-xs font-semibold bg-himalaya-50 hover:bg-himalaya-100 text-himalaya-600 rounded-lg py-2"
                  >
                    <FiNavigation size={12} /> Go
                  </a>
                )}
              </div>
            </motion.div>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* MAP */}
        <div className="lg:col-span-2 rounded-xl2 overflow-hidden shadow-premium">
          <MapView
            userLocation={position}
            hospitals={hospitals}
            policeStations={police}
            height="450px"
          />
        </div>

        {/* Nationwide hotline quick-reference, kept simple/reliable */}
        <div className="space-y-3">
          <h3 className="font-semibold">Nationwide Hotlines</h3>
          {[
            { name: "National Police", phone: "100" },
            { name: "Ambulance", phone: "102" },
            { name: "Fire Service", phone: "101" },
          ].map((item) => (
            <a
              key={item.phone}
              href={`tel:${item.phone}`}
              className="card-base p-4 flex justify-between items-center"
            >
              <div>
                <p className="font-medium">{item.name}</p>
                <p className="text-sm text-gray-400">{item.phone}</p>
              </div>
              <FiPhoneCall className="text-himalaya-500" />
            </a>
          ))}
        </div>
      </div>

      {/* HOSPITAL LIST — unchanged, already worked */}
      <div className="mt-10">
        <h2 className="text-xl font-semibold mb-4">Nearby Hospitals</h2>
        {loading ? (
          <Loader />
        ) : hospitals.length ? (
          <div className="grid md:grid-cols-2 gap-4">
            {hospitals.map((hospital, index) => (
              <div key={index} className="card-base p-5">
                <h3 className="font-bold text-lg">{hospital["Hospital Name"] || hospital.Name}</h3>
                <p className="text-sm text-gray-500 flex gap-2 mt-2">
                  <FiMapPin />
                  {hospital.Address}
                </p>
                <p className="text-sm mt-2">📞 {hospital.Phone}</p>
                {hospital.distance_km && (
                  <p className="text-sm text-forest-600 mt-2">{hospital.distance_km} km away</p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No hospitals found nearby.</p>
        )}
      </div>

      {/* POLICE LIST — unchanged, already worked */}
      <div className="mt-10">
        <h2 className="text-xl font-semibold mb-4">Nearby Police Stations</h2>
        {police.length ? (
          <div className="grid md:grid-cols-2 gap-4">
            {police.map((station, index) => (
              <div key={index} className="card-base p-5">
                <h3 className="font-bold">{station["Police Station"] || station.Name}</h3>
                <p className="text-sm text-gray-500 mt-2">{station.Address}</p>
                <p className="text-sm mt-2">📞 {station.Phone}</p>
                {station.distance_km && (
                  <p className="text-sm text-forest-600">{station.distance_km} km away</p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No police stations found.</p>
        )}
      </div>

      {/* NEW: Mountain & Helicopter Rescue. Deliberately NOT hardcoding
          a specific rescue-company phone number here — I can't verify
          one is currently correct, and giving wrong emergency contact
          info would be actively dangerous. The real, safe procedure in
          Nepal is described instead. */}
      <div className="mt-10 card-base p-6 border border-saffron-100">
        <h2 className="text-xl font-semibold mb-3 flex items-center gap-2">
          <FiNavigation className="text-saffron-600" /> Mountain & Helicopter Rescue
        </h2>
        <p className="text-sm text-gray-600 mb-2">
          Helicopter evacuation in Nepal is coordinated through your <b>travel insurance provider's 24/7
          emergency line</b> (confirm coverage for high-altitude rescue before trekking) or your <b>trekking
          agency/guide</b>, who can arrange rescue directly with licensed operators.
        </p>
        <p className="text-sm text-gray-600">
          If you have no signal, the Tourist Police (1144) or the nearest checkpoint/teahouse can relay a
          rescue request — descending to a lower altitude is often the single most effective first step for
          altitude sickness while help is arranged.
        </p>
      </div>

      {/* NEW: Offline Emergency Guidance — general knowledge, no network
          or backend dependency, so it's useful exactly when connectivity
          is the problem. */}
      <div className="mt-6 card-base p-6 border border-himalaya-100">
        <h2 className="text-xl font-semibold mb-3 flex items-center gap-2">
          <FiWifiOff className="text-himalaya-500" /> Offline Emergency Guidance
        </h2>
        <ul className="text-sm text-gray-600 space-y-2 list-disc list-inside">
          <li>Altitude sickness (headache, nausea, dizziness): stop ascending, descend if symptoms worsen, never push through severe symptoms.</li>
          <li>Bleeding: apply firm, direct pressure with the cleanest cloth available; elevate the injury if possible.</li>
          <li>Hypothermia: get out of wet clothing, insulate from the ground, share body heat, avoid alcohol.</li>
          <li>Lost/no signal: stay where you are if possible, use a whistle or bright clothing to signal, retrace known trail markers rather than shortcutting.</li>
          <li>Always tell someone your planned route and expected return time before setting out.</li>
        </ul>
        <p className="text-xs text-gray-400 mt-3">
          General guidance only — not a substitute for professional medical care or a wilderness first aid course.
        </p>
      </div>

      {/* SOS quick-dial modal */}
      <AnimatePresence>
        {sosOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            onClick={() => setSosOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl p-6 w-full max-w-sm"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-lg text-nepalred-500">Who do you need?</h3>
                <button onClick={() => setSosOpen(false)}><FiX /></button>
              </div>
              <div className="space-y-2">
                {[
                  { label: "Police", phone: "100", icon: FiShield },
                  { label: "Ambulance", phone: "102", icon: FiHeart },
                  { label: "Tourist Police", phone: "1144", icon: FiSun },
                ].map(({ label, phone, icon: Icon }) => (
                  <a
                    key={phone}
                    href={`tel:${phone}`}
                    className="flex items-center justify-between bg-gray-50 hover:bg-nepalred-50 rounded-xl px-4 py-3 transition-colors"
                  >
                    <span className="flex items-center gap-2 font-medium">
                      <Icon className="text-nepalred-500" /> {label}
                    </span>
                    <span className="text-nepalred-600 font-bold">{phone}</span>
                  </a>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default Emergency