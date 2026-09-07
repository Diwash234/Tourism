import { useEffect, useState } from "react"
import {
  FiTruck, FiPlus, FiEdit3, FiTrash2, FiSearch, FiCheckCircle,
  FiMapPin, FiCompass, FiDollarSign, FiClock, FiX, FiCheck
} from "react-icons/fi"
import adminApi from "../../api/adminApi"
import destinationApi from "../../api/destinationApi"
import axiosClient from "../../api/axiosClient"
import useToast from "../../hooks/useToast"

export default function AdminRouteManagerPanel() {
  const { showToast } = useToast()

  const [routes, setRoutes] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")

  // Admin Route Calculator Test Tool
  const [calcFrom, setCalcFrom] = useState("Pokhara")
  const [calcDestSearch, setCalcDestSearch] = useState("")
  const [calcDestResults, setCalcDestResults] = useState([])
  const [calcSelectedDest, setCalcSelectedDest] = useState(null)
  const [calcTransport, setCalcTransport] = useState("Public Deluxe Bus")
  const [calcResult, setCalcResult] = useState(null)
  const [calculating, setCalculating] = useState(false)

  // Edit / Create Route Modal
  const [showModal, setShowModal] = useState(false)
  const [editingRoute, setEditingRoute] = useState(null)
  const [form, setForm] = useState({
    destination_id: "",
    origin: "",
    transport_mode: "Public Deluxe Bus",
    distance_km: "",
    approx_duration: "",
    estimated_fare_npr: "",
    route_source: "Nepal Transit Board & Highway Authority",
    operator_name: "",
    confidence_level: "VERIFIED",
    is_verified: true,
  })

  const loadRoutes = () => {
    setLoading(true)
    adminApi.getTransitRoutes({ search: searchQuery })
      .then(({ data }) => setRoutes(data.results || data || []))
      .catch(() => setRoutes([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadRoutes()
  }, [searchQuery])

  // Destination autocomplete search for calculator
  useEffect(() => {
    if (!calcDestSearch.trim() || calcDestSearch.length < 2) {
      setCalcDestResults([])
      return
    }
    const timer = setTimeout(() => {
      destinationApi.getDestinations({ search: calcDestSearch, page_size: 6 })
        .then(({ data }) => setCalcDestResults(data.results || data || []))
        .catch(() => setCalcDestResults([]))
    }, 250)
    return () => clearTimeout(timer)
  }, [calcDestSearch])

  const handleRunAdminCalculator = async () => {
    if (!calcSelectedDest) {
      return showToast("Select a target destination first.", "error")
    }
    setCalculating(true)
    try {
      const { data } = await axiosClient.post("/navigation/calculate/", {
        destination_id: calcSelectedDest.id,
        origin_name: calcFrom,
        transport_mode: calcTransport,
      })
      setCalcResult(data)
      showToast("Route calculated!", "success")
    } catch {
      showToast("Could not calculate route.", "error")
    } finally {
      setCalculating(false)
    }
  }

  const handleSaveRoute = async (e) => {
    e.preventDefault()
    try {
      const payload = {
        destination: Number(form.destination_id),
        origin: form.origin,
        transport_mode: form.transport_mode,
        distance_km: form.distance_km ? Number(form.distance_km) : null,
        approx_duration: form.approx_duration,
        estimated_fare_npr: form.estimated_fare_npr ? Number(form.estimated_fare_npr) : null,
        route_source: form.route_source,
        operator_name: form.operator_name,
        confidence_level: form.confidence_level,
        is_verified: form.is_verified,
        is_active: true,
      }
      if (editingRoute) {
        await adminApi.updateTransitRoute(editingRoute.id, payload)
        showToast("Route record updated!", "success")
      } else {
        await adminApi.createTransitRoute(payload)
        showToast("New transit route record created!", "success")
      }
      setShowModal(false)
      loadRoutes()
    } catch {
      showToast("Could not save transit route record.", "error")
    }
  }

  return (
    <div className="space-y-6 text-slate-100">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-950 p-6 rounded-3xl border border-slate-800 shadow-xl">
        <div>
          <span className="px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-bold uppercase tracking-wider">
            Transportation & Route Control Desk
          </span>
          <h2 className="text-2xl font-black text-white mt-1">Route & Transport Intelligence</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Manage origin-destination routes, transit modes, operator contacts, verified fares, and run the Admin Route Calculator.
          </p>
        </div>

        <button
          onClick={() => {
            setEditingRoute(null)
            setForm({
              destination_id: "",
              origin: "",
              transport_mode: "Public Deluxe Bus",
              distance_km: "",
              approx_duration: "",
              estimated_fare_npr: "",
              route_source: "Nepal Transit Board & Highway Authority",
              operator_name: "",
              confidence_level: "VERIFIED",
              is_verified: true,
            })
            setShowModal(true)
          }}
          className="px-5 py-2.5 rounded-2xl bg-amber-400 hover:bg-amber-500 text-slate-950 font-black text-xs flex items-center gap-2 shadow"
        >
          <FiPlus size={16} /> Add Transit Route
        </button>
      </div>

      {/* Admin Route Calculator Tool */}
      <div className="p-6 rounded-3xl bg-slate-950 border border-blue-500/30 space-y-4 shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2 text-blue-400 font-bold text-sm">
            <FiCompass /> Admin Route Calculator Test Tool
          </div>
          <span className="text-[11px] text-slate-400">Calculates origin-specific distance & fare provenance</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div>
            <label className="font-bold text-slate-300 block mb-1">Origin City / Landmark</label>
            <input
              type="text"
              value={calcFrom}
              onChange={(e) => setCalcFrom(e.target.value)}
              placeholder="e.g. Pokhara Lakeside, Kathmandu Airport"
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-blue-400"
            />
          </div>

          <div className="relative">
            <label className="font-bold text-slate-300 block mb-1">Target Destination</label>
            {calcSelectedDest ? (
              <div className="flex items-center justify-between p-2 rounded-xl bg-blue-950/40 border border-blue-500/40 text-xs">
                <span className="font-bold text-white truncate">{calcSelectedDest.name}</span>
                <button type="button" onClick={() => setCalcSelectedDest(null)} className="text-slate-400 hover:text-white text-[10px]">Change</button>
              </div>
            ) : (
              <input
                type="text"
                value={calcDestSearch}
                onChange={(e) => setCalcDestSearch(e.target.value)}
                placeholder="Search destination..."
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-blue-400"
              />
            )}
            {calcDestResults.length > 0 && !calcSelectedDest && (
              <div className="absolute top-full left-0 right-0 mt-1 rounded-xl bg-slate-900 border border-slate-700 z-20 max-h-40 overflow-y-auto divide-y divide-slate-800">
                {calcDestResults.map((d) => (
                  <button
                    key={d.id}
                    type="button"
                    onClick={() => { setCalcSelectedDest(d); setCalcDestResults([]) }}
                    className="w-full text-left p-2.5 text-xs text-white hover:bg-slate-800 flex justify-between"
                  >
                    <span>{d.name}</span>
                    <span className="text-[10px] text-slate-400">{d.city || d.district}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div>
            <label className="font-bold text-slate-300 block mb-1">Transport Mode</label>
            <select
              value={calcTransport}
              onChange={(e) => setCalcTransport(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-blue-400"
            >
              <option>Public Deluxe Bus</option>
              <option>Private Car / Taxi</option>
              <option>Tourist Bus</option>
              <option>Local Jeep (4WD)</option>
              <option>Domestic Flight</option>
            </select>
          </div>
        </div>

        <button
          onClick={handleRunAdminCalculator}
          disabled={calculating || !calcSelectedDest}
          className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs disabled:opacity-40"
        >
          {calculating ? "Calculating..." : "Calculate Route Metrics"}
        </button>

        {calcResult && (
          <div className="p-4 rounded-2xl bg-slate-900 border border-blue-500/40 text-xs space-y-2">
            <div className="flex justify-between items-center font-bold text-white">
              <span>{calcResult.origin_name} ➔ {calcResult.destination_name}</span>
              <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 text-[10px] uppercase font-mono">{calcResult.confidence_level}</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] text-slate-300">
              <div><b>Distance:</b> {calcResult.distance_km != null ? `${calcResult.distance_km} km` : "Distance unavailable"}</div>
              <div><b>Duration:</b> {calcResult.estimated_duration}</div>
              <div><b>Fare:</b> {calcResult.fare_npr != null ? `NPR ${calcResult.fare_npr}` : "Fare not recorded"}</div>
              <div><b>Source:</b> {calcResult.fare_source}</div>
            </div>
          </div>
        )}
      </div>

      {/* Routes List Table */}
      <div className="bg-slate-950 border border-slate-800 rounded-3xl overflow-hidden shadow-xl p-5 space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="font-bold text-lg text-white">Recorded Transport Routes</h3>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter by origin or destination..."
            className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none"
          />
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900 text-amber-300 font-bold uppercase text-[10px]">
              <tr>
                <th className="p-3">Route (Origin ➔ Destination)</th>
                <th className="p-3">Mode</th>
                <th className="p-3">Distance</th>
                <th className="p-3">Duration</th>
                <th className="p-3">Fare (NPR)</th>
                <th className="p-3">Confidence</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {routes.map((r) => (
                <tr key={r.id} className="hover:bg-slate-900/50">
                  <td className="p-3 font-bold text-white">{r.origin} ➔ {r.destination_name}</td>
                  <td className="p-3">{r.transport_mode}</td>
                  <td className="p-3">{r.distance_km ? `${r.distance_km} km` : "—"}</td>
                  <td className="p-3">{r.approx_duration || "—"}</td>
                  <td className="p-3 font-mono text-amber-300">{r.estimated_fare_npr ? `NPR ${r.estimated_fare_npr}` : "Not recorded"}</td>
                  <td className="p-3"><span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">{r.confidence_level || "CALCULATED"}</span></td>
                  <td className="p-3 text-right">
                    <button
                      onClick={() => {
                        setEditingRoute(r)
                        setForm({
                          destination_id: r.destination,
                          origin: r.origin,
                          transport_mode: r.transport_mode,
                          distance_km: r.distance_km || "",
                          approx_duration: r.approx_duration || "",
                          estimated_fare_npr: r.estimated_fare_npr || "",
                          route_source: r.route_source || "",
                          operator_name: r.operator_name || "",
                          confidence_level: r.confidence_level || "VERIFIED",
                          is_verified: r.is_verified ?? true,
                        })
                        setShowModal(true)
                      }}
                      className="px-2.5 py-1 rounded bg-amber-500 text-slate-950 font-bold text-[11px] mr-2"
                    >
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
