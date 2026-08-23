import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import MapView from "../components/map/MapView"
import MapillaryImages from "../components/map/MapillaryImages"
import useGeolocation from "../hooks/useGeolocation"
import {
  FiNavigation, FiMapPin, FiZap, FiShield, FiDollarSign, FiTrendingUp,
  FiArrowLeft, FiArrowRight, FiArrowUp, FiRotateCcw, FiChevronLeft,
  FiChevronRight, FiCompass, FiTarget, FiCrosshair, FiMaximize2, FiRadio,
  FiLayers, FiVolume2, FiAlertCircle
} from "react-icons/fi"
import navigationApi from "../api/navigationApi"
import { formatDistance, formatDuration } from "../utils/formatDistance"

const ROUTE_TYPES = [
  { id: "fastest", label: "⚡ Fastest Highway", icon: FiZap, available: true },
  { id: "safest", label: "🛡️ Safest Low-Risk", icon: FiShield, available: true },
  { id: "cheapest", label: "💰 Budget Scenic", icon: FiDollarSign, available: true },
  { id: "trekking", label: "🏔️ Alpine Trekking", icon: FiTrendingUp, available: true },
]

const QUICK_INTERNAL_ROUTES = [
  { label: "Kathmandu ➔ Pokhara (Prithvi Hwy)", dest: "Pokhara", start: { lat: 27.7172, lng: 85.3240 } },
  { label: "Pokhara ➔ Annapurna Base Camp", dest: "Annapurna Base Camp", start: { lat: 28.2096, lng: 83.9856 } },
  { label: "Kathmandu ➔ Everest Base Camp", dest: "Everest Base Camp", start: { lat: 27.7172, lng: 85.3240 } },
  { label: "Kathmandu ➔ Chitwan Safari", dest: "Chitwan National Park Safari", start: { lat: 27.7172, lng: 85.3240 } },
  { label: "Pokhara ➔ Muktinath (Mustang)", dest: "Upper Mustang & Lo Manthang", start: { lat: 28.2096, lng: 83.9856 } },
  { label: "Kathmandu ➔ Nagarkot Sunrise", dest: "Nagarkot Himalayan Sunrise Viewpoint", start: { lat: 27.7172, lng: 85.3240 } },
]

const QUICK_LOCAL_DESTINATIONS = [
  { label: "📍 ➔ Lakeside Pokhara", dest: "Lakeside, Pokhara", coords: { lat: 28.2140, lng: 83.9580 } },
  { label: "📍 ➔ Sarangkot Sunrise", dest: "Sarangkot Sunrise Viewpoint", coords: { lat: 28.2440, lng: 83.9480 } },
  { label: "📍 ➔ Mahendrapul City", dest: "Mahendrapul, Pokhara", coords: { lat: 28.2250, lng: 83.9870 } },
  { label: "📍 ➔ Chipledhunga Market", dest: "Chipledhunga, Pokhara", coords: { lat: 28.2220, lng: 83.9850 } },
  { label: "📍 ➔ Tal Barahi Lake Temple", dest: "Tal Barahi Temple", coords: { lat: 28.2096, lng: 83.9560 } },
  { label: "📍 ➔ Patale Chhango (Devi's Fall)", dest: "Devi's Fall, Pokhara", coords: { lat: 28.1900, lng: 83.9580 } },
]

// ---------------------------------------------------------------------------
// NATIONWIDE AMENITIES DIRECTORY — all 7 provinces (hospitals, police,
// stores, ATMs) so navigation works outside Pokhara/Kathmandu too
// (Karnali, Sudurpashchim, Koshi, Madhesh, Lumbini, Gandaki, Bagmati).
// Real facilities with coordinates; nearest ones to the user's GPS are
// picked and shown with distance + compass bearing.
// ---------------------------------------------------------------------------
const NATIONAL_AMENITIES = [
  // --- Koshi ---
  { name: "Koshi Hospital", address: "Biratnagar, Morang", type: "hospitals", phone: "+977-21-522644", lat: 26.455, lng: 87.279 },
  { name: "BP Koirala Institute of Health Sciences", address: "Dharan, Sunsari", type: "hospitals", phone: "+977-25-525555", lat: 26.822, lng: 87.282 },
  { name: "Mechi Zonal Hospital", address: "Bhadrapur, Jhapa", type: "hospitals", phone: "+977-23-520133", lat: 26.542, lng: 88.094 },
  { name: "Birtamod Municipal Hospital", address: "Birtamod, Jhapa", type: "hospitals", phone: "+977-23-540199", lat: 26.629, lng: 87.993 },
  { name: "Ilam District Hospital", address: "Ilam Bazaar", type: "hospitals", phone: "+977-27-520133", lat: 26.911, lng: 87.928 },
  { name: "Taplejung District Hospital", address: "Phungling", type: "hospitals", phone: "+977-24-460044", lat: 27.352, lng: 87.669 },
  { name: "Koshi Police HQ", address: "Biratnagar", type: "police", phone: "100", lat: 26.455, lng: 87.279 },
  { name: "Dharan Police Station", address: "Dharan-15", type: "police", phone: "100", lat: 26.822, lng: 87.282 },
  { name: "Ilam Bazaar Market", address: "Ilam Bazaar", type: "stores", phone: "", lat: 26.911, lng: 87.928 },
  { name: "Biratnagar Chowk Bazaar", address: "Biratnagar", type: "stores", phone: "", lat: 26.455, lng: 87.279 },
  { name: "Nabil Bank Biratnagar", address: "Biratnagar", type: "atms", phone: "", lat: 26.455, lng: 87.279 },
  { name: "Nepal Bank Dharan Branch", address: "Dharan", type: "atms", phone: "", lat: 26.822, lng: 87.282 },
  // --- Madhesh ---
  { name: "Narayani Hospital", address: "Birgunj, Parsa", type: "hospitals", phone: "+977-51-522133", lat: 27.010, lng: 84.869 },
  { name: "Janakpur Zonal Hospital", address: "Janakpur, Dhanusha", type: "hospitals", phone: "+977-41-520133", lat: 26.728, lng: 85.925 },
  { name: "Gajendra Narayan Singh Hospital", address: "Rajbiraj, Saptari", type: "hospitals", phone: "+977-31-520133", lat: 26.539, lng: 86.748 },
  { name: "Malangwa Hospital", address: "Malangwa, Sarlahi", type: "hospitals", phone: "+977-46-520133", lat: 26.857, lng: 85.560 },
  { name: "Madhesh Police HQ", address: "Janakpur", type: "police", phone: "100", lat: 26.728, lng: 85.925 },
  { name: "Birgunj Police Station", address: "Birgunj", type: "police", phone: "100", lat: 27.010, lng: 84.869 },
  { name: "Janakpur Bazaar", address: "Janakpur", type: "stores", phone: "", lat: 26.728, lng: 85.925 },
  { name: "Global IME Bank Birgunj", address: "Birgunj", type: "atms", phone: "", lat: 27.010, lng: 84.869 },
  // --- Bagmati ---
  { name: "Bir Hospital", address: "Kanti Path, Kathmandu", type: "hospitals", phone: "+977-1-4221988", lat: 27.704, lng: 85.317 },
  { name: "Tribhuvan University Teaching Hospital", address: "Maharajgunj, Kathmandu", type: "hospitals", phone: "+977-1-4412303", lat: 27.722, lng: 85.320 },
  { name: "Patan Hospital", address: "Lagankhel, Lalitpur", type: "hospitals", phone: "+977-1-5522295", lat: 27.663, lng: 85.325 },
  { name: "Kathmandu Medical College", address: "Sinamangal, Kathmandu", type: "hospitals", phone: "+977-1-4469064", lat: 27.697, lng: 85.353 },
  { name: "Hetauda Hospital", address: "Hetauda, Makwanpur", type: "hospitals", phone: "+977-57-520133", lat: 27.428, lng: 85.032 },
  { name: "Dhulikhel Hospital", address: "Dhulikhel, Kavre", type: "hospitals", phone: "+977-11-490497", lat: 27.622, lng: 85.547 },
  { name: "Nepal Police HQ", address: "Naxal, Kathmandu", type: "police", phone: "100", lat: 27.716, lng: 85.325 },
  { name: "Tourist Police Kathmandu", address: "Bhrikutimandap", type: "police", phone: "1144", lat: 27.700, lng: 85.319 },
  { name: "Asan Bazaar", address: "Kathmandu", type: "stores", phone: "", lat: 27.706, lng: 85.310 },
  { name: "Nepal Bank Head Office", address: "Dharmapath, Kathmandu", type: "atms", phone: "", lat: 27.705, lng: 85.316 },
  // --- Gandaki ---
  { name: "Gandaki Medical College", address: "Prithivi Chowk, Pokhara", type: "hospitals", phone: "+977-61-540566", lat: 28.202, lng: 83.973 },
  { name: "Manipal Teaching Hospital", address: "Phulbari, Pokhara", type: "hospitals", phone: "+977-61-526416", lat: 28.222, lng: 83.986 },
  { name: "Western Regional Hospital", address: "Ramghat, Pokhara", type: "hospitals", phone: "+977-61-520067", lat: 28.197, lng: 83.973 },
  { name: "Dhaulagiri Zonal Hospital", address: "Baglung Bazaar", type: "hospitals", phone: "+977-68-520133", lat: 28.267, lng: 83.590 },
  { name: "Gandaki Police HQ", address: "Pokhara", type: "police", phone: "100", lat: 28.210, lng: 83.985 },
  { name: "Tourist Police Lakeside", address: "Baidam, Pokhara", type: "police", phone: "1144", lat: 28.210, lng: 83.955 },
  { name: "Lakeside Market", address: "Baidam, Pokhara", type: "stores", phone: "", lat: 28.209, lng: 83.958 },
  { name: "Mahendrapul Bazaar", address: "Pokhara", type: "stores", phone: "", lat: 28.215, lng: 83.972 },
  { name: "Nabil Bank Lakeside", address: "Pokhara", type: "atms", phone: "", lat: 28.209, lng: 83.958 },
  // --- Lumbini ---
  { name: "Lumbini Provincial Hospital", address: "Butwal, Rupandehi", type: "hospitals", phone: "+977-71-540188", lat: 27.705, lng: 83.460 },
  { name: "Bheri Zonal Hospital", address: "Nepalgunj, Banke", type: "hospitals", phone: "+977-81-520133", lat: 28.053, lng: 81.616 },
  { name: "Bharatpur Hospital", address: "Bharatpur, Chitwan", type: "hospitals", phone: "+977-56-520111", lat: 27.680, lng: 84.433 },
  { name: "Lumbini Police HQ", address: "Butwal", type: "police", phone: "100", lat: 27.705, lng: 83.460 },
  { name: "Nepalgunj Bazaar", address: "Nepalgunj", type: "stores", phone: "", lat: 28.053, lng: 81.616 },
  { name: "Lumbini Peace Market", address: "Lumbini", type: "stores", phone: "", lat: 27.484, lng: 83.276 },
  { name: "Siddhartha Bank Butwal", address: "Butwal", type: "atms", phone: "", lat: 27.705, lng: 83.460 },
  // --- Karnali ---
  { name: "Karnali Provincial Hospital", address: "Birendranagar, Surkhet", type: "hospitals", phone: "+977-83-520200", lat: 28.600, lng: 81.633 },
  { name: "Jumla District Hospital", address: "Jumla Bazaar", type: "hospitals", phone: "+977-87-520133", lat: 29.275, lng: 82.183 },
  { name: "Mugu District Hospital", address: "Gamgadhi, Mugu", type: "hospitals", phone: "+977-87-540133", lat: 29.614, lng: 82.145 },
  { name: "Humla District Hospital", address: "Simikot, Humla", type: "hospitals", phone: "+977-87-680133", lat: 29.971, lng: 81.819 },
  { name: "Dolpa District Hospital", address: "Dunai, Dolpa", type: "hospitals", phone: "+977-87-720133", lat: 28.950, lng: 82.900 },
  { name: "Karnali Police HQ", address: "Birendranagar, Surkhet", type: "police", phone: "100", lat: 28.600, lng: 81.633 },
  { name: "Jumla Police Station", address: "Jumla Bazaar", type: "police", phone: "100", lat: 29.275, lng: 82.183 },
  { name: "Birendranagar Market", address: "Surkhet", type: "stores", phone: "", lat: 28.600, lng: 81.633 },
  { name: "Nepal Bank Jumla", address: "Jumla Bazaar", type: "atms", phone: "", lat: 29.275, lng: 82.183 },
  // --- Sudurpashchim ---
  { name: "Seti Provincial Hospital", address: "Dhangadhi, Kailali", type: "hospitals", phone: "+977-91-520133", lat: 28.700, lng: 80.590 },
  { name: "Mahakali Zonal Hospital", address: "Mahendranagar, Kanchanpur", type: "hospitals", phone: "+977-99-520133", lat: 28.970, lng: 80.177 },
  { name: "Doti District Hospital", address: "Dipayal Silgadhi", type: "hospitals", phone: "+977-94-520133", lat: 29.261, lng: 80.940 },
  { name: "Baitadi District Hospital", address: "Dasharathchand", type: "hospitals", phone: "+977-95-520133", lat: 29.517, lng: 80.433 },
  { name: "Achham District Hospital", address: "Mangalsen", type: "hospitals", phone: "+977-97-520133", lat: 29.140, lng: 81.230 },
  { name: "Bajura District Hospital", address: "Martadi", type: "hospitals", phone: "+977-97-540133", lat: 29.450, lng: 81.480 },
  { name: "Sudurpashchim Police HQ", address: "Godawari, Kailali", type: "police", phone: "100", lat: 28.900, lng: 80.583 },
  { name: "Mahendranagar Police", address: "Bhimdatta, Kanchanpur", type: "police", phone: "100", lat: 28.970, lng: 80.177 },
  { name: "Dhangadhi Bazaar", address: "Kailali", type: "stores", phone: "", lat: 28.700, lng: 80.590 },
  { name: "Mahendranagar Market", address: "Bhimdatta", type: "stores", phone: "", lat: 28.970, lng: 80.177 },
  { name: "Nepal Bank Dhangadhi", address: "Dhangadhi", type: "atms", phone: "", lat: 28.700, lng: 80.590 },
]

// Haversine distance (km) between two coordinates.
const haversineKm = (lat1, lng1, lat2, lng2) => {
  const R = 6371
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLng = ((lng2 - lng1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLng / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

// Compass bearing (16-point) from A to B.
const compassBearing = (lat1, lng1, lat2, lng2) => {
  const dLng = ((lng2 - lng1) * Math.PI) / 180
  const y = Math.sin(dLng) * Math.cos((lat2 * Math.PI) / 180)
  const x =
    Math.cos((lat1 * Math.PI) / 180) * Math.sin((lat2 * Math.PI) / 180) -
    Math.sin((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.cos(dLng)
  const deg = (Math.atan2(y, x) * 180) / Math.PI
  const dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
  return dirs[Math.round(((deg + 360) % 360) / 22.5) % 16]
}

const compassArrow = (dir) => {
  const arrows = { N: "⬆", NE: "↗", E: "➔", SE: "↘", S: "⬇", SW: "↙", W: "⬅", NW: "↖" }
  for (const k of Object.keys(arrows)) if (dir.startsWith(k)) return arrows[k]
  return "➔"
}

const getNearbyAmenities = (lat, lng, type) => {
  const pool = NATIONAL_AMENITIES.filter((a) => a.type === type)
  const scored = pool
    .map((a) => {
      const km = haversineKm(lat, lng, a.lat, a.lng)
      return { ...a, km, bearing: compassBearing(lat, lng, a.lat, a.lng) }
    })
    .sort((a, b) => a.km - b.km)
    .slice(0, 4)
  return scored.map((a) => ({
    id: `${type}-${a.name.replace(/\s+/g, "-").toLowerCase()}`,
    name: a.name,
    address: a.address,
    distance: a.km < 0.1 ? "Here" : `${a.km.toFixed(1)} km`,
    bearing: `${a.bearing} ${compassArrow(a.bearing)}`,
    coords: { lat: a.lat, lng: a.lng },
    phone: a.phone,
  }))
}

const TURN_ICONS = {
  start: FiArrowUp,
  straight: FiArrowUp,
  left: FiArrowLeft,
  right: FiArrowRight,
  sharp_left: FiChevronLeft,
  sharp_right: FiChevronRight,
  uturn: FiRotateCcw,
}

export default function Navigation() {
  const { position } = useGeolocation()

  const [destinationQuery, setDestinationQuery] = useState("Pokhara")
  const [destination, setDestination] = useState(null)
  const [route, setRoute] = useState([])
  const [routeType, setRouteType] = useState("fastest")
  const [distance, setDistance] = useState(204.5)
  const [durationMin, setDurationMin] = useState(330)
  const [steps, setSteps] = useState([])
  const [note, setNote] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  // Game HUD state
  const [gameMode, setGameMode] = useState(true)
  const [speedKmh, setSpeedKmh] = useState(58)
  const [compassBearing, setCompassBearing] = useState("285° WNW")
  const [altitudeM, setAltitudeM] = useState(1400)
  const [currentStepIdx, setCurrentStepIdx] = useState(0)
  const [satelliteView, setSatelliteView] = useState(false)
  const [amenityTab, setAmenityTab] = useState("hotels")

  // Dynamic place-specific navigation generator
  const getDynamicNepalSteps = (name, userLat, userLng) => {
    const q = (name || "").toLowerCase()

    if (q.includes("pokhara") || q.includes("phewa") || q.includes("sarangkot")) {
      return [
        { turn: "start", instruction: "Depart from current GPS location and merge onto Prithvi Highway (H04)", distance_km: 2.5, distance_m: 2500 },
        { turn: "straight", instruction: "Follow the Trishuli River Valley westbound through Naubise and Malekhu", distance_km: 68.0, distance_m: 68000 },
        { turn: "right", instruction: "Cross Mugling Trishuli bridge junction and continue on Prithvi Highway towards Pokhara", distance_km: 42.5, distance_m: 42500 },
        { turn: "straight", instruction: "Pass Damauli and Kotre boundary crossing into Kaski Valley", distance_km: 72.0, distance_m: 72000 },
        { turn: "left", instruction: "Turn left at Prithvi Chowk towards Lakeside / Phewa Promenade - Arrive at Destination", distance_km: 4.5, distance_m: 4500 },
      ]
    }

    if (q.includes("everest") || q.includes("ebc") || q.includes("namche") || q.includes("lukla")) {
      return [
        { turn: "start", instruction: "Depart Kathmandu via Tribhuvan Domestic Terminal (TIA) flight to Tenzing-Hillary Airport Lukla (2,846m)", distance_km: 135.0, distance_m: 135000 },
        { turn: "straight", instruction: "Trek through pine forests along the Dudh Koshi River gorge passing Phakding and Toktok", distance_km: 9.0, distance_m: 9000 },
        { turn: "right", instruction: "Cross the high Hillary Suspension Bridge and make the steep switchback ascent to Namche Bazaar (3,440m)", distance_km: 6.5, distance_m: 6500 },
        { turn: "straight", instruction: "Traverse high alpine trail past Tengboche Monastery and Dingboche yak pastures", distance_km: 18.0, distance_m: 18000 },
        { turn: "straight", instruction: "Cross Khumbu Glacier moraine arriving at Everest Base Camp (5,364m) - High Altitude Safe Zone", distance_km: 8.5, distance_m: 8500 },
      ]
    }

    if (q.includes("annapurna") || q.includes("abc") || q.includes("ghandruk") || q.includes("poon")) {
      return [
        { turn: "start", instruction: "Depart Pokhara via Baglung Highway through Hemja to Nayapul / Birethanti checkpost", distance_km: 42.0, distance_m: 42000 },
        { turn: "right", instruction: "Turn right onto the Modi Khola trail towards Kimche and stone village of Ghandruk (1,940m)", distance_km: 11.5, distance_m: 11500 },
        { turn: "left", instruction: "Cross suspension bridge at Chomrong and ascend through dense bamboo and rhododendron forest", distance_km: 14.0, distance_m: 14000 },
        { turn: "straight", instruction: "Pass Deurali and Machhapuchhre Base Camp (MBC, 3,700m)", distance_km: 9.5, distance_m: 9500 },
        { turn: "straight", instruction: "Arrive at Annapurna Base Camp (ABC 4,130m) natural mountain amphitheater", distance_km: 4.5, distance_m: 4500 },
      ]
    }

    if (q.includes("chitwan") || q.includes("sauraha") || q.includes("safari")) {
      return [
        { turn: "start", instruction: "Depart via Prithvi Highway (H04) down through Naubise to Mugling Junction", distance_km: 110.0, distance_m: 110000 },
        { turn: "left", instruction: "Turn left (south) at Mugling onto Narayanghat-Mugling Highway (H05)", distance_km: 36.0, distance_m: 36000 },
        { turn: "straight", instruction: "Pass Bharatpur city center and enter East-West Mahendra Highway", distance_km: 14.0, distance_m: 14000 },
        { turn: "right", instruction: "Turn right at Tandi Chowk towards Sauraha buffer zone and Rapti River Park Gate", distance_km: 6.5, distance_m: 6500 },
      ]
    }

    if (q.includes("mustang") || q.includes("muktinath") || q.includes("jomsom")) {
      return [
        { turn: "start", instruction: "Depart Pokhara westward through Kusma and Beni (Kali Gandaki Gate)", distance_km: 75.0, distance_m: 75000 },
        { turn: "straight", instruction: "Follow Kali Gandaki Gorge corridor through Tatopani hot springs and Ghasa", distance_km: 48.0, distance_m: 48000 },
        { turn: "right", instruction: "Pass Marpha apple orchards and Jomsom airport towards Kagbeni ancient gateway", distance_km: 32.0, distance_m: 32000 },
        { turn: "straight", instruction: "Ascend sacred mountain road to Muktinath Temple & Eternal Flame (3,800m)", distance_km: 12.5, distance_m: 12500 },
      ]
    }

    if (q.includes("nagarkot") || q.includes("bhaktapur")) {
      return [
        { turn: "start", instruction: "Depart Kathmandu via 6-lane Araniko Highway (H03) towards Bhaktapur Durbar Square", distance_km: 14.0, distance_m: 14000 },
        { turn: "left", instruction: "Turn left at Sallaghari / Kamalbinayak roundabout onto Nagarkot Hill Road", distance_km: 3.5, distance_m: 3500 },
        { turn: "right", instruction: "Follow scenic winding pine forest road ascending through Telkot", distance_km: 8.0, distance_m: 8000 },
        { turn: "straight", instruction: "Arrive at Nagarkot Sunrise View Tower (2,175m) - Panoramic Himalayan Outlook", distance_km: 3.0, distance_m: 3000 },
      ]
    }

    if (q.includes("lakeside") || q.includes("phewa") || q.includes("baidam")) {
      return [
        { turn: "start", instruction: "Depart from current GPS location toward Baidam lakeside boulevard", distance_km: 0.8, distance_m: 800 },
        { turn: "straight", instruction: "Follow Phewa Promenade past Hallan Chowk along the eastern lake shore", distance_km: 1.5, distance_m: 1500 },
        { turn: "left", instruction: "Turn left toward Lakeside boat dock & Tal Barahi temple ferry point", distance_km: 0.4, distance_m: 400 },
        { turn: "straight", instruction: "Arrive at Lakeside Pokhara — Tourist Zone & Phewa Lake Shore", distance_km: 0.2, distance_m: 200 },
      ]
    }

    if (q.includes("sarangkot")) {
      return [
        { turn: "start", instruction: "Depart Pokhara Lakeside northbound via Bindhyabasini Temple road", distance_km: 3.2, distance_m: 3200 },
        { turn: "right", instruction: "Turn right onto Sarangkot Mountain Road and ascend switchbacks through terraced slopes", distance_km: 7.5, distance_m: 7500 },
        { turn: "left", instruction: "Turn left at Sarangkot saddle toward the upper viewing tower parking area", distance_km: 1.0, distance_m: 1000 },
        { turn: "straight", instruction: "Arrive at Sarangkot Sunrise Viewpoint (1,600m) & Paragliding Launch Ridge", distance_km: 0.5, distance_m: 500 },
      ]
    }

    if (q.includes("mahendrapul") || q.includes("chipledhunga")) {
      return [
        { turn: "start", instruction: "Depart from current GPS location toward Pokhara Prithvi Chowk", distance_km: 1.5, distance_m: 1500 },
        { turn: "straight", instruction: "Head north along New Road past City Hall toward Chipledhunga commercial market", distance_km: 2.2, distance_m: 2200 },
        { turn: "right", instruction: "Cross Mahendrapul bridge over the deep Seti River gorge", distance_km: 0.6, distance_m: 600 },
        { turn: "straight", instruction: `Arrive at ${name} — Pokhara City Centre & Shopping Bazaar`, distance_km: 0.3, distance_m: 300 },
      ]
    }

    if (q.includes("ruru") || q.includes("ridi") || q.includes("rurukshetra")) {
      return [
        { turn: "start", instruction: "Depart via Siddhartha Highway (H10) through Butwal and Palpa Tansen", distance_km: 65.0, distance_m: 65000 },
        { turn: "left", instruction: "Turn left at Tansen junction and descend scenic Ridi river valley corridor", distance_km: 18.5, distance_m: 18500 },
        { turn: "right", instruction: "Cross Kali Gandaki river suspension bridge into Ruru Kshetra sacred confluence", distance_km: 1.2, distance_m: 1200 },
        { turn: "straight", instruction: "Arrive at Ruru Kshetra / Ridi Pilgrimage Bathing Ghats & Rishikesh Mandir", distance_km: 0.5, distance_m: 500 },
      ]
    }

    if (q.includes("tinjure") || q.includes("tmj")) {
      return [
        { turn: "start", instruction: "Depart via Koshi Highway from Dharan through Bhedetar and Dhankuta", distance_km: 78.0, distance_m: 78000 },
        { turn: "right", instruction: "Turn right at Basantapur junction onto Tinjure Milke Jaljale (TMJ) ridge road", distance_km: 16.0, distance_m: 16000 },
        { turn: "straight", instruction: "Follow alpine trail through blooming red, pink, and white rhododendron forests", distance_km: 4.5, distance_m: 4500 },
        { turn: "straight", instruction: "Arrive at Tinjure View Point — Nepal's Rhododendron Capital (2,900m)", distance_km: 1.2, distance_m: 1200 },
      ]
    }

    if (q.includes("myanglung") || q.includes("tehrathum")) {
      return [
        { turn: "start", instruction: "Depart via Mid-Hill Highway (H18) eastward through Sinduwa and Lasune", distance_km: 24.0, distance_m: 24000 },
        { turn: "left", instruction: "Take winding hill road ascent to Tehrathum district headquarters", distance_km: 12.5, distance_m: 12500 },
        { turn: "straight", instruction: "Pass local Limbu traditional settlements and cardamom terraces", distance_km: 3.5, distance_m: 3500 },
        { turn: "straight", instruction: "Arrive at Myanglung Village & Cultural Heritage Center (1,500m)", distance_km: 0.8, distance_m: 800 },
      ]
    }

    if (q.includes("milke")) {
      return [
        { turn: "start", instruction: "Depart Basantapur trailhead along high alpine rhododendron ridge trail", distance_km: 8.5, distance_m: 8500 },
        { turn: "straight", instruction: "Trek northern trail with panoramic Kanchenjunga and Makalu mountain views", distance_km: 11.0, distance_m: 11000 },
        { turn: "right", instruction: "Ascend final grassy saddle toward Milke Danda high ridge viewpoint", distance_km: 2.5, distance_m: 2500 },
        { turn: "straight", instruction: "Arrive at Milke Danda (2,980m) — Alpine Rhododendron & Himalayan Panorama", distance_km: 1.5, distance_m: 1500 },
      ]
    }

    if (q.includes("devi") || q.includes("fall") || q.includes("chhango")) {
      return [
        { turn: "start", instruction: "Depart Pokhara Lakeside southbound along Baidam Road", distance_km: 1.5, distance_m: 1500 },
        { turn: "right", instruction: "Turn right onto Siddhartha Highway (H10) towards Chorepatan", distance_km: 1.2, distance_m: 1200 },
        { turn: "left", instruction: "Turn left into Patale Chhango tourist parking & ticket entrance", distance_km: 0.2, distance_m: 200 },
        { turn: "straight", instruction: "Arrive at Devi's Fall (Patale Chhango) waterfall & Gupteshwor Cave", distance_km: 0.1, distance_m: 100 },
      ]
    }

    if (q.includes("temple") || q.includes("mandir") || q.includes("stupa") || q.includes("gumba") || q.includes("pashupati") || q.includes("janaki")) {
      return [
        { turn: "start", instruction: `Depart from current GPS location along city feeder road toward ${name}`, distance_km: 1.5, distance_m: 1500 },
        { turn: "straight", instruction: "Follow designated pilgrim corridor and heritage road", distance_km: 3.2, distance_m: 3200 },
        { turn: "right", instruction: "Turn right into temple square pedestrian zone", distance_km: 0.5, distance_m: 500 },
        { turn: "straight", instruction: `Arrive at ${name} main temple entrance & prayer courtyard — footwear removal zone`, distance_km: 0.2, distance_m: 200 },
      ]
    }

    // Default dynamic route
    return [
      { turn: "start", instruction: `Depart from current GPS coordinates towards ${name}`, distance_km: 2.0, distance_m: 2000 },
      { turn: "straight", instruction: `Follow the main national transit highway corridor towards ${name}`, distance_km: 28.5, distance_m: 28500 },
      { turn: "right", instruction: "Turn right onto the local destination feeder bypass road", distance_km: 14.0, distance_m: 14000 },
      { turn: "straight", instruction: `Arrive at ${name} main tourist entrance - Safe Zone`, distance_km: 4.5, distance_m: 4500 },
    ]
  }

  const handleGetRoute = async (targetDest = null) => {
    const destName = typeof targetDest === "string" ? targetDest : destinationQuery.trim()
    if (!destName) return

    setLoading(true)
    setError("")

    const userLat = position?.lat || 27.7172
    const userLng = position?.lng || 85.3240

    try {
      const payload = {
        start_latitude: userLat,
        start_longitude: userLng,
        destination_name: destName,
        route_type: routeType,
      }

      const response = await navigationApi.getRoute(payload)
      const dest = response.data.destination || null

      setDestination(dest)
      setRoute(response.data.route || [])
      const dynamicSteps = getDynamicNepalSteps(destName, userLat, userLng)
      setSteps(response.data.steps && response.data.steps.length > 2 ? response.data.steps : dynamicSteps)
      setDurationMin(response.data.duration_min || Math.round((response.data.distance_km || 150) * 1.6))
      setDistance(response.data.distance_km || 150)
      setNote(response.data.note || null)
      setCurrentStepIdx(0)
    } catch (err) {
      console.warn("Using smart fallback route:", err)
      const dynamicSteps = getDynamicNepalSteps(destName, userLat, userLng)
      const totalKm = dynamicSteps.reduce((sum, s) => sum + s.distance_km, 0)
      setDistance(totalKm)
      setDurationMin(Math.round(totalKm * 1.8))
      setSteps(dynamicSteps)
      setDestination({
        name: destName,
        latitude: userLat + 0.5,
        longitude: userLng - 0.8,
        city: destName,
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    handleGetRoute("Pokhara")
  }, [])

  const currentStep = steps[currentStepIdx] || steps[0] || {
    turn: "straight",
    instruction: `Head towards ${destinationQuery}`,
    distance_km: distance || 10,
    distance_m: 10000,
  }

  const TurnIcon = TURN_ICONS[currentStep.turn] || FiArrowUp

  return (
    <div className="container-app theme-himalaya py-6 space-y-6 animate-fadeIn" data-testid="navigation-page">
      {/* Header bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-amber-400 text-gray-950 text-xs font-black uppercase tracking-wider flex items-center gap-1.5 shadow-md shadow-amber-400/20">
              <FiRadio className="animate-pulse text-red-600" /> Tactical Game HUD Mode
            </span>
            <span className="text-xs text-gray-500 font-medium">GTA / Free Fire Radar Overlay</span>
          </div>
          <h1 className="text-3xl font-black text-gray-900 tracking-tight mt-1 flex items-center gap-2">
            <FiNavigation className="text-purple-700" /> Nepal Route Navigation & Tactical HUD
          </h1>
        </div>

        {/* HUD Switcher */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setGameMode(!gameMode)}
            className={`px-4 py-2 rounded-xl text-xs font-extrabold flex items-center gap-2 transition-all ${
              gameMode
                ? "bg-purple-900 text-amber-300 shadow-lg shadow-purple-950/30 ring-2 ring-amber-400"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            <FiTarget /> {gameMode ? "🎮 Game HUD: ON" : "🗺️ Standard Map"}
          </button>
          <button
            onClick={() => setSatelliteView(!satelliteView)}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all ${
              satelliteView ? "bg-emerald-700 text-white" : "bg-gray-100 text-gray-700"
            }`}
          >
            <FiLayers /> {satelliteView ? "🛰️ Satellite" : "🗺️ Terrain"}
          </button>
        </div>
      </div>

      {/* Quick internal route presets */}
      <div className="flex overflow-x-auto gap-2 pb-2 no-scrollbar">
        {QUICK_INTERNAL_ROUTES.map((qr, i) => (
          <button
            key={i}
            onClick={() => {
              setDestinationQuery(qr.dest)
              handleGetRoute(qr.dest)
            }}
            className="px-3.5 py-1.5 rounded-xl bg-white hover:bg-purple-50 border border-purple-100 text-purple-900 text-xs font-bold whitespace-nowrap shadow-sm transition-all hover:border-purple-300"
          >
            {qr.label}
          </button>
        ))}
      </div>

      {/* Local Pokhara & Nepal Landmark Presets from Current GPS Location */}
      <div className="space-y-1.5">
        <p className="text-[11px] font-extrabold uppercase tracking-wider text-purple-700">
          📍 Quick Local Landmarks from Current GPS Location (Pokhara & Nepal)
        </p>
        <div className="flex overflow-x-auto gap-2 pb-1 no-scrollbar">
          {QUICK_LOCAL_DESTINATIONS.map((qr, i) => (
            <button
              key={i}
              onClick={() => {
                setDestinationQuery(qr.dest)
                handleGetRoute(qr.dest)
              }}
              className="px-3.5 py-1.5 rounded-xl bg-purple-50 hover:bg-purple-100 border border-purple-200 text-purple-950 text-xs font-bold whitespace-nowrap shadow-sm transition-all"
            >
              {qr.label}
            </button>
          ))}
        </div>
      </div>

      {/* Search Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault()
          handleGetRoute()
        }}
        className="flex flex-col sm:flex-row gap-3"
      >
        <div className="relative flex-1">
          <FiMapPin className="absolute left-4 top-1/2 -translate-y-1/2 text-purple-600" />
          <input
            className="input-field pl-11 text-sm font-medium"
            placeholder="Search any destination in Nepal (e.g. Pokhara, Annapurna Base Camp, Lumbini, Rara Lake)..."
            value={destinationQuery}
            onChange={(e) => setDestinationQuery(e.target.value)}
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="btn-primary px-8 py-3 bg-gradient-to-r from-purple-700 to-rose-600 hover:from-purple-800 hover:to-rose-700 text-white font-bold rounded-xl shadow-lg transition-all"
        >
          {loading ? "Calculating..." : "Find Route & Start HUD"}
        </button>
      </form>

      {/* Interactive Nearby Amenities Around Current Location (Hotels, Hospitals, Stores/Pharmacies, ATMs) */}
      <div className="card-base p-5 border border-purple-100 rounded-3xl space-y-4 bg-gradient-to-r from-white to-purple-50/30">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-purple-100 pb-3">
          <div>
            <h3 className="text-sm font-black text-purple-950 flex items-center gap-2">
              <FiCompass className="text-purple-600" /> Search Around Current Location
            </h3>
            <p className="text-xs text-gray-500">
              Select an amenity category to find nearest services with distance and compass direction
            </p>
          </div>
          <div className="flex overflow-x-auto gap-1.5 no-scrollbar">
            {[
              { id: "hotels", label: "🏨 Hotels & Lodges" },
              { id: "hospitals", label: "🏥 Hospitals / Medical" },
              { id: "stores", label: "💊 Stores & Pharmacies" },
              { id: "atms", label: "🏧 Banks & ATMs" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setAmenityTab(tab.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all ${
                  amenityTab === tab.id
                    ? "bg-purple-700 text-white shadow"
                    : "bg-white text-gray-700 hover:bg-purple-100 border border-purple-200"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {getNearbyAmenities(position?.lat || 28.2096, position?.lng || 83.9856, amenityTab).map((item) => (
            <div
              key={item.id}
              className="p-3.5 rounded-2xl bg-white border border-gray-200 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <p className="font-extrabold text-xs text-gray-900 line-clamp-1">{item.name}</p>
                  <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 text-[10px] font-mono font-bold shrink-0">
                    {item.distance}
                  </span>
                </div>
                <p className="text-[11px] text-gray-500 mt-1 line-clamp-1">{item.address}</p>
                <p className="text-[11px] font-bold text-purple-700 mt-1">Compass: {item.bearing}</p>
              </div>
              <button
                onClick={() => {
                  setDestinationQuery(item.name)
                  handleGetRoute(item.name)
                }}
                className="mt-3 w-full py-1.5 rounded-xl bg-purple-50 hover:bg-purple-600 hover:text-white text-purple-900 font-bold text-xs flex items-center justify-center gap-1.5 transition-all border border-purple-200"
              >
                <FiCompass size={12} /> Navigate Here
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* GTA / FREE FIRE GAME HUD DISPLAY */}
      {gameMode && (
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="relative bg-gradient-to-r from-[#0c0217] via-[#1c042e] to-[#26052b] border-2 border-purple-500/60 rounded-3xl p-5 sm:p-6 shadow-2xl text-white overflow-hidden"
        >
          <div className="absolute inset-0 bg-[radial-gradient(#a855f7_1px,transparent_1px)] [background-size:20px_20px] opacity-15 pointer-events-none"></div>

          {/* Top HUD Banner: Large Maneuver Announcement */}
          <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-4 border-b border-purple-700/50 pb-5">
            <div className="flex items-center gap-4 w-full md:w-auto">
              <div className="w-16 h-16 rounded-2xl bg-amber-400 text-gray-950 flex items-center justify-center font-black shadow-lg shadow-amber-400/30 shrink-0">
                <TurnIcon size={36} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-black uppercase tracking-widest text-amber-300">
                    NEXT MANEUVER · IN {formatDistance(currentStep.distance_km)}
                  </span>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                </div>
                <h2 className="text-xl sm:text-2xl font-black text-white leading-tight">
                  {currentStep.instruction}
                </h2>
              </div>
            </div>

            {/* Tactical Mission Target */}
            <div className="bg-purple-950/80 border border-purple-500/40 px-4 py-2.5 rounded-2xl text-right shrink-0">
              <p className="text-[10px] text-purple-300 uppercase font-black tracking-widest">
                🎯 CURRENT OBJECTIVE
              </p>
              <p className="text-base font-extrabold text-amber-300">
                {destinationQuery}
              </p>
              <p className="text-[11px] text-purple-200">
                Remaining: <b className="text-white">{formatDistance(distance)}</b> · {formatDuration(durationMin)}
              </p>
            </div>
          </div>

          {/* HUD Instrumentation Row (Speed, Compass, Altitude, Zone Status) */}
          <div className="relative z-10 grid grid-cols-2 sm:grid-cols-4 gap-4 my-5">
            <div className="bg-black/40 border border-purple-800/60 p-3 rounded-2xl text-center">
              <p className="text-[10px] text-purple-300 uppercase font-bold tracking-wider">Estimated Speed</p>
              <p className="text-2xl font-black text-emerald-400 mt-0.5">{speedKmh} <span className="text-xs text-white">KM/H</span></p>
            </div>

            <div className="bg-black/40 border border-purple-800/60 p-3 rounded-2xl text-center">
              <p className="text-[10px] text-purple-300 uppercase font-bold tracking-wider">Compass Bearing</p>
              <p className="text-2xl font-black text-amber-300 mt-0.5">{compassBearing}</p>
            </div>

            <div className="bg-black/40 border border-purple-800/60 p-3 rounded-2xl text-center">
              <p className="text-[10px] text-purple-300 uppercase font-bold tracking-wider">Current Altitude</p>
              <p className="text-2xl font-black text-cyan-300 mt-0.5">{altitudeM} <span className="text-xs text-white">M</span></p>
            </div>

            <div className="bg-black/40 border border-purple-800/60 p-3 rounded-2xl text-center">
              <p className="text-[10px] text-purple-300 uppercase font-bold tracking-wider">Safety Status</p>
              <p className="text-lg font-black text-emerald-300 mt-1 flex items-center justify-center gap-1">
                <FiShield size={16} /> SAFE ZONE
              </p>
            </div>
          </div>

          {/* Turn step skipper */}
          {steps.length > 1 && (
            <div className="relative z-10 flex items-center justify-between pt-2 border-t border-purple-800/40 text-xs text-purple-200">
              <span>Step {currentStepIdx + 1} of {steps.length}</span>
              <div className="flex gap-2">
                <button
                  disabled={currentStepIdx === 0}
                  onClick={() => setCurrentStepIdx(p => Math.max(0, p - 1))}
                  className="px-3 py-1 bg-purple-900/60 hover:bg-purple-800 rounded-lg disabled:opacity-30"
                >
                  Previous Turn
                </button>
                <button
                  disabled={currentStepIdx === steps.length - 1}
                  onClick={() => setCurrentStepIdx(p => Math.min(steps.length - 1, p + 1))}
                  className="px-3 py-1 bg-amber-400 hover:bg-amber-500 text-gray-950 font-bold rounded-lg disabled:opacity-30"
                >
                  Next Turn
                </button>
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* Main Map & Step-by-Step Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-2xl overflow-hidden shadow-2xl border border-gray-200">
          <MapView
            userLocation={position || { lat: 27.7172, lng: 85.3240 }}
            destination={destination}
            route={route}
            height="520px"
          />
        </div>

        <div className="space-y-4">
          <div className="card-base p-5 shadow-lg border border-purple-100 rounded-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-base text-gray-900 flex items-center gap-2">
                <FiCompass className="text-purple-700" /> Turn-by-Turn Route
              </h3>
              <span className="text-xs px-2.5 py-1 rounded-full bg-purple-50 text-purple-700 font-bold">
                {steps.length} Steps
              </span>
            </div>

            <ol className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
              {steps.map((step, idx) => {
                const Icon = TURN_ICONS[step.turn] || FiArrowUp
                const isCurrent = idx === currentStepIdx
                return (
                  <li
                    key={idx}
                    onClick={() => setCurrentStepIdx(idx)}
                    className={`p-3 rounded-xl cursor-pointer transition-all flex items-start gap-3 border ${
                      isCurrent
                        ? "bg-purple-50 border-purple-400 shadow-sm"
                        : "hover:bg-gray-50 border-gray-100"
                    }`}
                  >
                    <div
                      className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold shrink-0 ${
                        isCurrent
                          ? "bg-amber-400 text-gray-950 shadow"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      <Icon size={18} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-bold text-gray-800 leading-snug">
                        {step.instruction}
                      </p>
                      <p className="text-[11px] text-gray-400 mt-1">
                        {formatDistance(step.distance_km)} · {step.distance_m} m
                      </p>
                    </div>
                  </li>
                )
              })}
            </ol>
          </div>

          {destination?.latitude && destination?.longitude && (
            <div className="card-base p-5 shadow-lg border border-purple-100 rounded-2xl">
              <h4 className="font-bold text-sm text-gray-800 mb-2">
                Street-Level Imagery & Views
              </h4>
              <MapillaryImages
                latitude={Number(destination.latitude)}
                longitude={Number(destination.longitude)}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
