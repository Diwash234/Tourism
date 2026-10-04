import { useState, useEffect, useCallback } from "react"
import { FiPlus, FiSearch, FiEdit, FiTrash, FiMapPin, FiRoute, FiArrowRight, FiRefreshCw, FiCheck, FiX, FiChevronDown, FiChevronUp, FiMap, FiCompass, FiTarget, FiAlertTriangle } from "react-icons/fi"
import { motion, AnimatePresence } from "framer-motion"
import adminApi from "../../api/adminApi"
import destinationApi from "../../api/destinationApi"
import useToast from "../../hooks/useToast"

const TRANSPORT_MODES = [
  "Private Car / Taxi", "Tourist Bus", "Motorcycle", "Walking / Trek", "Flight"
]

const ROUTE_SOURCES = [
  "Nepal Transit Board & Highway Authority",
  "OSRM Routing Engine",
  "Google Maps API",
  "Local Survey",
  "Community Reported"
]

const CONFIDENCE_LEVELS = [
  "VERIFIED", "CALCULATED", "ESTIMATED", "APPROXIMATE"
]

const initialRouteForm = {
  destination_id: "",
  origin: "",
  transport_mode: "Private Car / Taxi",
  distance_km: "",
  approx_duration: "",
  estimated_fare_npr: "",
  route_source: "Nepal Transit Board & Highway Authority",
  operator_name: "",
  confidence_level: "VERIFIED",
  is_verified: false,
  origin_latitude: "",
  origin_longitude: "",
  destination_latitude: "",
  destination_longitude: "",
  waypoints: [],
  road_condition: "",
  notes: ""
}

export default function NavigationManagerPanel() {
  const { showToast } = useToast()

  // State
  const [routes, setRoutes] = useState([])
  const [destinations, setDestinations] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [transportFilter, setTransportFilter] = useState("")
  const [verifiedFilter, setVerifiedFilter] = useState("")
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [totalCount, setTotalCount] = useState(0)
  const [totalPages, setTotalPages] = useState(0)
  const [sortConfig, setSortConfig] = useState({ key: "created_at", direction: "desc" })

  // Modal state
  const [showModal, setShowModal] = useState(false)
  const [editingRoute, setEditingRoute] = useState(null)
  const [form, setForm] = useState(initialRouteForm)
  const [formErrors, setFormErrors] = useState({})
  const [saving, setSaving] = useState(false)
  const [calculating, setCalculating] = useState(false)
  const [calcResult, setCalcResult] = useState(null)

  // View state
  const [viewMode, setViewMode] = useState("table")
  const [selectedIds, setSelectedIds] = useState([])
  const [showRouteCalculator, setShowRouteCalculator] = useState(false)
  const [calcOrigin, setCalcOrigin] = useState("")
  const [calcDestination, setCalcDestination] = useState("")
  const [calcTransportMode, setCalcTransportMode] = useState("Private Car / Taxi")
  const [destSearchResults, setDestSearchResults] = useState([])
  const [calcLoading, setCalcLoading] = useState(false)

  // Map/coordinate state
  const [showCoordPicker, setShowCoordPicker] = useState(false)
  const [coordTarget, setCoordTarget] = useState("")

  // Fetch data
  const fetchRoutes = useCallback(async () => {
    setLoading(true)
    try {
      const params = {
        page: currentPage,
        page_size: pageSize,
        search: search || undefined,
        transport_mode: transportFilter || undefined,
        is_verified: verifiedFilter ? (verifiedFilter === "true") : undefined,
        ordering: `${sortConfig.direction === "desc" ? "-" : ""}${sortConfig.key}`
      }
      const { data } = await adminApi.getTransitRoutes(params)
      const results = data.results || data || []
      setRoutes(results)
      setTotalCount(data.count || results.length)
      setTotalPages(Math.ceil((data.count || results.length) / pageSize))
    } catch (err) {
      showToast("Failed to load routes", "error")
      setRoutes([])
    } finally {
      setLoading(false)
    }
  }, [currentPage, pageSize, search, transportFilter, verifiedFilter, sortConfig, showToast])

  const fetchDestinations = useCallback(async () => {
    try {
      const { data } = await destinationApi.getDestinations({ page_size: 500, status: "approved" })
      setDestinations(data.results || data || [])
    } catch (err) {
      console.error("Failed to load destinations:", err)
    }
  }, [])

  useEffect(() => { fetchRoutes() }, [fetchRoutes])
  useEffect(() => { fetchDestinations() }, [fetchDestinations])

  // Destination search for calculator
  useEffect(() => {
    if (!calcDestination.trim() || calcDestination.length < 2) {
      setDestSearchResults([])
      return
    }
    const timer = setTimeout(() => {
      destinationApi.getDestinations({ search: calcDestination, page_size: 8 })
        .then(({ data }) => setDestSearchResults(data.results || data || []))
        .catch(() => setDestSearchResults([]))
    }, 250)
    return () => clearTimeout(timer)
  }, [calcDestination])

  // Handlers
  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === "asc" ? "desc" : "asc"
    }))
  }

  const openCreateModal = () => {
    setEditingRoute(null)
    setForm(initialRouteForm)
    setFormErrors({})
    setCalcResult(null)
    setShowModal(true)
  }

  const openEditModal = (route) => {
    setEditingRoute(route)
    setForm({
      ...initialRouteForm,
      id: route.id,
      destination_id: route.destination?.id || route.destination_id || "",
      origin: route.origin || "",
      transport_mode: route.transport_mode || "Private Car / Taxi",
      distance_km: route.distance_km?.toString() || "",
      approx_duration: route.approx_duration || "",
      estimated_fare_npr: route.estimated_fare_npr?.toString() || "",
      route_source: route.route_source || "Nepal Transit Board & Highway Authority",
      operator_name: route.operator_name || "",
      confidence_level: route.confidence_level || "VERIFIED",
      is_verified: route.is_verified === true,
      origin_latitude: route.origin_latitude?.toString() || "",
      origin_longitude: route.origin_longitude?.toString() || "",
      destination_latitude: route.destination_latitude?.toString() || "",
      destination_longitude: route.destination_longitude?.toString() || "",
      waypoints: route.waypoints || [],
      road_condition: route.road_condition || "",
      notes: route.notes || ""
    })
    setFormErrors({})
    setCalcResult(null)
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setEditingRoute(null)
    setForm(initialRouteForm)
    setFormErrors({})
    setCalcResult(null)
  }

  const validateForm = () => {
    const errors = {}
    if (!form.destination_id) errors.destination_id = "Destination is required"
    if (!form.origin.trim()) errors.origin = "Origin is required"
    if (!form.transport_mode) errors.transport_mode = "Transport mode is required"
    if (form.distance_km && (parseFloat(form.distance_km) < 0)) errors.distance_km = "Distance must be positive"
    if (form.estimated_fare_npr && (parseFloat(form.estimated_fare_npr) < 0)) errors.estimated_fare_npr = "Fare must be positive"
    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSave = async () => {
    if (!validateForm()) return
    setSaving(true)
    try {
      const payload = {
        destination: parseInt(form.destination_id),
        origin: form.origin,
        transport_mode: form.transport_mode,
        distance_km: form.distance_km ? parseFloat(form.distance_km) : null,
        approx_duration: form.approx_duration || null,
        estimated_fare_npr: form.estimated_fare_npr ? parseFloat(form.estimated_fare_npr) : null,
        route_source: form.route_source,
        operator_name: form.operator_name,
        confidence_level: form.confidence_level,
        is_verified: form.is_verified,
        origin_latitude: form.origin_latitude ? parseFloat(form.origin_latitude) : null,
        origin_longitude: form.origin_longitude ? parseFloat(form.origin_longitude) : null,
        destination_latitude: form.destination_latitude ? parseFloat(form.destination_latitude) : null,
        destination_longitude: form.destination_longitude ? parseFloat(form.destination_longitude) : null,
        waypoints: form.waypoints,
        road_condition: form.road_condition,
        notes: form.notes
      }

      if (editingRoute) {
        await adminApi.updateTransitRoute(editingRoute.id, payload)
        showToast("Route updated successfully", "success")
      } else {
        await adminApi.createTransitRoute(payload)
        showToast("Route created successfully", "success")
      }
      closeModal()
      fetchRoutes()
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || "Save failed"
      showToast(msg, "error")
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm("Delete this route? This cannot be undone.")) return
    try {
      await adminApi.deleteTransitRoute(id)
      showToast("Route deleted", "success")
      fetchRoutes()
    } catch (err) {
      showToast(err.response?.data?.detail || "Delete failed", "error")
    }
  }

  const handleVerify = async (route) => {
    try {
      await adminApi.verifyTransitRoute(route.id)
      showToast("Route verified successfully", "success")
      fetchRoutes()
    } catch (err) {
      showToast(err.response?.data?.detail || "Verification failed", "error")
    }
  }

  const handleRecalculate = async (route) => {
    try {
      const { data } = await adminApi.recalculateTransitRoute(route.id)
      const before = data.previous?.distance_km ? `${data.previous.distance_km} km` : "no stored distance"
      showToast(`Recalculated: ${before} → ${data.current.distance_km} km (${data.current.duration_source}); needs re-verification`, "success")
      fetchRoutes()
    } catch (err) {
      showToast(err.response?.data?.detail || "Recalculation failed", "error")
    }
  }

  const handleBulkVerify = async () => {
    if (!selectedIds.length) return
    try {
      await Promise.all(selectedIds.map(id => adminApi.verifyTransitRoute(id)))
      showToast(`${selectedIds.length} routes verified`, "success")
      setSelectedIds([])
      fetchRoutes()
    } catch (err) {
      showToast("Bulk verification failed", "error")
    }
  }

  const handleBulkRecalculate = async () => {
    if (!selectedIds.length) return
    try {
      await Promise.all(selectedIds.map(id => adminApi.recalculateTransitRoute(id)))
      showToast(`${selectedIds.length} routes recalculated`, "success")
      fetchRoutes()
    } catch (err) {
      showToast("Bulk recalculation failed", "error")
    }
  }

  const exportCSV = () => {
    const headers = ["ID", "Origin", "Destination", "Transport Mode", "Distance (km)", "Duration", "Fare (NPR)", "Verified", "Source"]
    const rows = routes.map(r => [
      r.id, r.origin, r.destination?.name || r.destination_id, r.transport_mode,
      r.distance_km || "", r.approx_duration || "", r.estimated_fare_npr || "",
      r.is_verified ? "Yes" : "No", r.route_source
    ])
    const csv = [headers, ...rows].map(r => r.map(v => `"${v}"`).join(",")).join("\n")
    const blob = new Blob([csv], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `routes_${new Date().toISOString().split("T")[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const openCalculator = () => {
    setShowRouteCalculator(true)
  }

  const handleCalcDestinationSelect = (dest) => {
    setCalcDestination(dest.name)
    setForm(prev => ({ ...prev, destination_id: dest.id, destination_latitude: dest.latitude, destination_longitude: dest.longitude }))
    setDestSearchResults([])
  }

  const handleCalculateRoute = async () => {
    if (!calcOrigin || !calcDestination) {
      showToast("Both origin and destination are required", "error")
      return
    }
    if (!form.destination_id) {
      showToast("Select a destination first", "error")
      return
    }

    setCalcLoading(true)
    try {
      const payload = {
        destination_id: form.destination_id,
        origin_name: calcOrigin,
        transport_mode: calcTransportMode
      }

      // Try to get coordinates from destination
      const dest = destinations.find(d => d.id == form.destination_id)
      if (dest?.latitude && dest?.longitude) {
        payload.start_latitude = dest.latitude
        payload.start_longitude = dest.longitude
      }

      const { data } = await adminApi.getRoute(payload)
      setCalcResult(data)

      // Auto-fill form with calculated values
      setForm(prev => ({
        ...prev,
        distance_km: data.distance_km?.toString() || "",
        approx_duration: data.duration_min ? `${data.duration_min} mins` : "",
        origin_latitude: data.origin?.latitude?.toString() || "",
        origin_longitude: data.origin?.longitude?.toString() || "",
        destination_latitude: data.destination?.latitude?.toString() || "",
        destination_longitude: data.destination?.longitude?.toString() || ""
      }))
      showToast("Route calculated successfully", "success")
    } catch (err) {
      showToast(err.response?.data?.detail || "Calculation failed", "error")
    } finally {
      setCalcLoading(false)
    }
  }

  const handleCoordPick = (lat, lng) => {
    setForm(prev => ({ ...prev, [coordTarget]: lat.toFixed(6), [coordTarget === "origin_latitude" ? "origin_longitude" : "destination_longitude"]: lng.toFixed(6) }))
    setShowCoordPicker(false)
  }

  const toggleSelect = (id) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])
  }

  const toggleSelectAll = () => {
    if (selectedIds.length === routes.length) {
      setSelectedIds([])
    } else {
      setSelectedIds(routes.map(r => r.id))
    }
  }

  // Render
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <FiRoute className="text-emerald-600" />
            Navigation Route Manager
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage transit routes — create, verify, recalculate, calculate distances
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={exportCSV} className="px-4 py-2 rounded-xl bg-white border border-slate-200 text-slate-700 text-sm font-bold flex items-center gap-2 hover:bg-slate-50 transition">
            <FiDownload /> Export CSV
          </button>
          <button onClick={openCalculator} className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold flex items-center gap-2">
            <FiCompass /> Route Calculator
          </button>
          <button onClick={openCreateModal} className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold flex items-center gap-2">
            <FiPlus /> Add Route
          </button>
        </div>
      </div>

      {/* Route Calculator Modal */}
      <AnimatePresence>
        {showRouteCalculator && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="bg-white rounded-3xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
              <div className="p-6 border-b border-slate-200 flex items-center justify-between sticky top-0 bg-white z-10 rounded-t-3xl">
                <h2 className="text-xl font-black text-slate-900 flex items-center gap-2">
                  <FiCompass className="text-blue-600" />
                  Route Calculator
                </h2>
                <button onClick={() => setShowRouteCalculator(false)} className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 transition">✕</button>
              </div>
              <div className="p-6 space-y-4">
                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">Origin *</label>
                    <div className="relative">
                      <FiMapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                      <inpu
                        className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Type origin (e.g. Kathmandu, Pokhara, or coordinates)..."
                        value={calcOrigin}
                        onChange={(e) => setCalcOrigin(e.target.value)}
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1">Destination *</label>
                    <div className="relative">
                      <FiTarget className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                      <inpu
                        className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Type destination name..."
                        value={calcDestination}
                        onChange={(e) => setCalcDestination(e.target.value)}
                      />
                    </div>
                  </div>
                </div>

                {destSearchResults.length > 0 && (
                  <div className="bg-blue-50 border border-blue-200 rounded-xl p-3">
                    <p className="text-sm font-bold text-blue-900 mb-2">Matching destinations:</p>
                    <div className="flex flex-wrap gap-2">
                      {destSearchResults.map(d => (
                        <button key={d.id} onClick={() => handleCalcDestinationSelect(d)} className="px-3 py-1.5 rounded-lg bg-white border border-blue-200 text-blue-800 text-sm font-medium hover:bg-blue-50 transition">
                          {d.name} ({d.district})
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-1">Transport Mode</label>
                  <select value={calcTransportMode} onChange={e => setCalcTransportMode(e.target.value)} className="input-field w-full">
                    {TRANSPORT_MODES.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>

                <button onClick={handleCalculateRoute} disabled={calcLoading || !calcOrigin || !calcDestination || !form.destination_id} className="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-bold flex items-center justify-center gap-2">
                  {calcLoading ? "Calculating..." : "Calculate Route"}
                </button>

                {calcResult && (
                  <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl space-y-2">
                    <h4 className="font-bold text-emerald-900">Calculation Result</h4>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div><span className="text-slate-500">Distance:</span> <span className="font-bold text-emerald-700 ml-1">{calcResult.distance_km} km</span></div>
                      <div><span className="text-slate-500">Duration:</span> <span className="font-bold text-emerald-700 ml-1">{calcResult.duration_min} mins</span></div>
                      <div><span className="text-slate-500">Source:</span> <span className="font-bold ml-1">{calcResult.route_source}</span></div>
                      <div><span className="text-slate-500">Confidence:</span> <span className="font-bold ml-1">{calcResult.confidence_level}</span></div>
                    </div>
                    <button onClick={() => {
                      setForm(prev => ({
                        ...prev,
                        distance_km: calcResult.distance_km?.toString() || "",
                        approx_duration: calcResult.duration_min ? `${calcResult.duration_min} mins` : "",
                        origin_latitude: calcResult.origin?.latitude?.toString() || "",
                        origin_longitude: calcResult.origin?.longitude?.toString() || "",
                        destination_latitude: calcResult.destination?.latitude?.toString() || "",
                        destination_longitude: calcResult.destination?.longitude?.toString() || ""
                      }))
                    }} className="w-full mt-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold">
                      Apply to Form
                    </button>
                  </div>
                )}

                <div className="flex gap-3 pt-4">
                  <button onClick={() => setShowRouteCalculator(false)} className="flex-1 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold">Close</button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
        {/* Filters */}
        <div className="p-4 border-b border-slate-200 flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-[250px]">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <inpu
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              placeholder="Search routes by origin, destination, operator..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setCurrentPage(1) }}
            />
          </div>
          <select value={transportFilter} onChange={e => { setTransportFilter(e.target.value); setCurrentPage(1) }} className="input-field px-4 py-2.5 rounded-xl text-sm min-w-[200px]">
            <option value="">All Transport Modes</option>
            {TRANSPORT_MODES.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
          <select value={verifiedFilter} onChange={e => { setVerifiedFilter(e.target.value); setCurrentPage(1) }} className="input-field px-4 py-2.5 rounded-xl text-sm min-w-[160px]">
            <option value="">All Verification</option>
            <option value="true">Verified</option>
            <option value="false">Unverified</option>
          </select>
          <div className="flex items-center gap-2">
            <button onClick={openCalculator} className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold flex items-center gap-2">
              <FiCompass /> Calculate
            </button>
            <button onClick={openCreateModal} className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold flex items-center gap-2">
              <FiPlus /> Add Route
            </button>
          </div>
        </div>

        {/* Bulk Actions */}
        {selectedIds.length > 0 && (
          <div className="px-4 py-3 border-b border-slate-200 bg-amber-50 flex items-center gap-3 flex-wrap">
            <span className="text-sm font-bold text-amber-800">{selectedIds.length} selected</span>
            <button onClick={handleBulkVerify} className="px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-xs font-bold hover:bg-emerald-700">Verify</button>
            <button onClick={handleBulkRecalculate} className="px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-bold hover:bg-blue-700">Recalculate</button>
            <button onClick={() => setSelectedIds([])} className="px-3 py-1.5 rounded-lg bg-slate-200 text-slate-600 text-xs font-bold hover:bg-slate-300 ml-auto">Clear</button>
          </div>
        )}

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-4 py-3 text-left">
                  <input type="checkbox" checked={selectedIds.length === routes.length && routes.length > 0} onChange={toggleSelectAll} className="rounded border-slate-300" />
                </th>
                {["Origin", "Destination", "Mode", "Distance", "Duration", "Fare", "Verified", "Confidence", "Source", "Actions"].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-bold uppercase text-slate-500 cursor-pointer hover:text-emerald-600">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr><td colSpan={11} className="px-4 py-8 text-center text-slate-500">Loading...</td></tr>
              ) : routes.length === 0 ? (
                <tr><td colSpan={11} className="px-4 py-8 text-center text-slate-500">No routes found</td></tr>
              ) : (
                routes.map(route => (
                  <tr key={route.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3">
                      <input type="checkbox" checked={selectedIds.includes(route.id)} onChange={() => toggleSelect(route.id)} className="rounded border-slate-300" />
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-slate-900">{route.origin}</div>
                      {route.origin_latitude && route.origin_longitude && (
                        <div className="text-xs text-slate-500 font-mono">{parseFloat(route.origin_latitude).toFixed(4)}, {parseFloat(route.origin_longitude).toFixed(4)}</div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-slate-900">{route.destination?.name || route.destination_id}</div>
                      {route.destination_latitude && route.destination_longitude && (
                        <div className="text-xs text-slate-500 font-mono">{parseFloat(route.destination_latitude).toFixed(4)}, {parseFloat(route.destination_longitude).toFixed(4)}</div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-700 text-xs font-bold">{route.transport_mode}</span>
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-700">{route.distance_km || "—"} km</td>
                    <td className="px-4 py-3 text-slate-600">{route.approx_duration || "—"}</td>
                    <td className="px-4 py-3 text-slate-600">{route.estimated_fare_npr ? `NPR ${route.estimated_fare_npr}` : "—"}</td>
                    <td className="px-4 py-3 text-center">
                      {route.is_verified ? (
                        <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-700 text-xs font-bold">✓ Verified</span>
                      ) : (
                        <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-700 text-xs font-bold">Unverified</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                        route.confidence_level === "VERIFIED" ? "bg-emerald-100 text-emerald-700" :
                        route.confidence_level === "CALCULATED" ? "bg-blue-100 text-blue-700" : "bg-slate-100 text-slate-700"
                      }`}>
                        {route.confidence_level}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500 max-w-xs truncate">{route.route_source}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <button onClick={() => openEditModal(route)} className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition" title="Edit">
                          <FiEdit size={14} />
                        </button>
                        <button onClick={() => handleVerify(route)} disabled={route.is_verified} className="p-2 rounded-lg bg-slate-100 hover:bg-emerald-100 text-slate-600 hover:text-emerald-600 transition disabled:opacity-40" title="Verify">
                          <FiCheck size={14} />
                        </button>
                        <button onClick={() => handleRecalculate(route)} className="p-2 rounded-lg bg-slate-100 hover:bg-blue-100 text-slate-600 hover:text-blue-600 transition" title="Recalculate">
                          <FiRefreshCw size={14} />
                        </button>
                        <button onClick={() => handleDelete(route.id)} className="p-2 rounded-lg bg-slate-100 hover:bg-rose-100 text-slate-600 hover:text-rose-600 transition" title="Delete">
                          <FiTrash size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              )}
            </tbody>
          </table>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-4 py-3 border-t border-slate-200 flex items-center justify-between">
              <span className="text-sm text-slate-500">Page {currentPage} of {totalPages} • {totalCount} total</span>
              <div className="flex gap-1">
                <button onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1} className="px-3 py-1.5 rounded-lg bg-white border border-slate-200 disabled:opacity-40 text-sm font-bold">Prev</button>
                <button onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages} className="px-3 py-1.5 rounded-lg bg-white border border-slate-200 disabled:opacity-40 text-sm font-bold">Next</button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Edit Modal */}
      <AnimatePresence>
        {showModal && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="bg-white rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
              <div className="p-6 border-b border-slate-200 flex items-center justify-between sticky top-0 bg-white z-10 rounded-t-3xl">
                <h2 className="text-xl font-black text-slate-900 flex items-center gap-2">
                  <FiRoute className="text-emerald-600" />
                  {editingRoute ? "Edit Route" : "New Route"}
                </h2>
                <button onClick={closeModal} className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 transition">✕</button>
              </div>

              <form onSubmit={e => { e.preventDefault(); handleSave() }} className="p-6 space-y-6">
                <div className="grid lg:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-1">Destination *</label>
                      <select value={form.destination_id} onChange={e => setForm({...form, destination_id: e.target.value})} className={`w-full px-4 py-2.5 rounded-xl border ${formErrors.destination_id ? "border-red-400" : "border-slate-200"} focus:outline-none focus:ring-2 focus:ring-emerald-500`}>
                        <option value="">Select destination</option>
                        {destinations.map(d => <option key={d.id} value={d.id}>{d.name} ({d.district})</option>)}
                      </select>
                      {formErrors.destination_id && <p className="text-red-500 text-xs mt-1">{formErrors.destination_id}</p>}
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-1">Origin *</label>
                      <input value={form.origin} onChange={e => setForm({...form, origin: e.target.value})} className={`w-full px-4 py-2.5 rounded-xl border ${formErrors.origin ? "border-red-400" : "border-slate-200"} focus:outline-none focus:ring-2 focus:ring-emerald-500`} placeholder="e.g. Kathmandu" />
                      {formErrors.origin && <p className="text-red-500 text-xs mt-1">{formErrors.origin}</p>}
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-1">Transport Mode *</label>
                      <select value={form.transport_mode} onChange={e => setForm({...form, transport_mode: e.target.value})} className={`w-full px-4 py-2.5 rounded-xl border ${formErrors.transport_mode ? "border-red-400" : "border-slate-200"} focus:outline-none focus:ring-2 focus:ring-emerald-500`}>
                        {TRANSPORT_MODES.map(m => <option key={m} value={m}>{m}</option>)}
                      </select>
                      {formErrors.transport_mode && <p className="text-red-500 text-xs mt-1">{formErrors.transport_mode}</p>}
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-sm font-bold text-slate-700 mb-1">Distance (km)</label>
                        <input value={form.distance_km} onChange={e => setForm({...form, distance_km: e.target.value})} className={`w-full px-4 py-2.5 rounded-xl border ${formErrors.distance_km ? "border-red-400" : "border-slate-200"} focus:outline-none focus:ring-2 focus:ring-emerald-500`} placeholder="200" type="number" step="0.1" />
                        {formErrors.distance_km && <p className="text-red-500 text-xs mt-1">{formErrors.distance_km}</p>}
                      </div>
                      <div>
                        <label className="block text-sm font-bold text-slate-700 mb-1">Duration</label>
                        <input value={form.approx_duration} onChange={e => setForm({...form, approx_duration: e.target.value})} className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="6 hours" />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-sm font-bold text-slate-700 mb-1">Fare (NPR)</label>
                        <input value={form.estimated_fare_npr} onChange={e => setForm({...form, estimated_fare_npr: e.target.value})} className={`w-full px-4 py-2.5 rounded-xl border ${formErrors.estimated_fare_npr ? "border-red-400" : "border-slate-200"} focus:outline-none focus:ring-2 focus:ring-emerald-500`} placeholder="1500" type="number" step="0.01" />
                        {formErrors.estimated_fare_npr && <p className="text-red-500 text-xs mt-1">{formErrors.estimated_fare_npr}</p>}
                      </div>
                      <div>
                        <label className="block text-sm font-bold text-slate-700 mb-1">Confidence Level</label>
                        <select value={form.confidence_level} onChange={e => setForm({...form, confidence_level: e.target.value})} className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500">
                          {CONFIDENCE_LEVELS.map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-1">Route Source</label>
                      <select value={form.route_source} onChange={e => setForm({...form, route_source: e.target.value})} className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500">
                        {ROUTE_SOURCES.map(s => <option key={s} value={s}>{s}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-1">Operator Name</label>
                      <input value={form.operator_name} onChange={e => setForm({...form, operator_name: e.target.value})} className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="e.g. Greenline, Sajha Yatayat" />
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-sm font-bold text-slate-700 mb-1">Origin Latitude</label>
                        <div className="flex gap-2">
                          <input value={form.origin_latitude} onChange={e => setForm({...form, origin_latitude: e.target.value})} className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="27.7172" type="number" step="any" />
                          <button type="button" onClick={() => { setCoordTarget("origin_latitude"); setShowCoordPicker(true) }} className="px-3 py-2.5 rounded-xl bg-emerald-100 hover:bg-emerald-200 text-emerald-700 font-bold flex items-center gap-1"><FiMapPin size={14} /> Pick</button>
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-bold text-slate-700 mb-1">Origin Longitude</label>
                        <div className="flex gap-2">
                          <input value={form.origin_longitude} onChange={e => setForm({...form, origin_longitude: e.target.value})} className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="85.3240" type="number" step="any" />
                          <button type="button" onClick={() => { setCoordTarget("origin_longitude"); setShowCoordPicker(true) }} className="px-3 py-2.5 rounded-xl bg-emerald-100 hover:bg-emerald-200 text-emerald-700 font-bold flex items-center gap-1"><FiMapPin size={14} /> Pick</button>
                        </div>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-sm font-bold text-slate-700 mb-1">Destination Latitude</label>
                        <div className="flex gap-2">
                          <input value={form.destination_latitude} onChange={e => setForm({...form, destination_latitude: e.target.value})} className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="28.2096" type="number" step="any" />
                          <button type="button" onClick={() => { setCoordTarget("destination_latitude"); setShowCoordPicker(true) }} className="px-3 py-2.5 rounded-xl bg-emerald-100 hover:bg-emerald-200 text-emerald-700 font-bold flex items-center gap-1"><FiMapPin size={14} /> Pick</button>
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-bold text-slate-700 mb-1">Destination Longitude</label>
                        <div className="flex gap-2">
                          <input value={form.destination_longitude} onChange={e => setForm({...form, destination_longitude: e.target.value})} className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="83.9856" type="number" step="any" />
                          <button type="button" onClick={() => { setCoordTarget("destination_longitude"); setShowCoordPicker(true) }} className="px-3 py-2.5 rounded-xl bg-emerald-100 hover:bg-emerald-200 text-emerald-700 font-bold flex items-center gap-1"><FiMapPin size={14} /> Pick</button>
                        </div>
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-1">Waypoints (JSON array)</label>
                      <textarea value={JSON.stringify(form.waypoints, null, 2)} onChange={e => { try { setForm({...form, waypoints: JSON.parse(e.target.value)}) } catch {} }} rows={3} className="w-full px-4 py-2.5 rounded-xl border border-slate-200 font-mono text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder='[{"name": "Stop 1", "lat": 27.8, "lng": 85.5}]' />
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-1">Road Condition</label>
                      <textarea value={form.road_condition} onChange={e => setForm({...form, road_condition: e.target.value})} rows={2} className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="Good, some potholes near..." />
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-1">Notes</label>
                      <textarea value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} rows={2} className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="Additional notes..." />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" checked={form.is_verified} onChange={e => setForm({...form, is_verified: e.target.checked})} className="rounded border-slate-300 text-emerald-600" />
                        <span className="text-sm font-medium text-slate-700">Verified</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" checked={form.is_active} onChange={e => setForm({...form, is_active: e.target.checked})} className="rounded border-slate-300 text-emerald-600" />
                        <span className="text-sm font-medium text-slate-700">Active</span>
                      </label>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200 sticky bottom-0 bg-white z-10 rounded-b-3xl">
                  <button type="button" onClick={closeModal} className="px-5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold">Cancel</button>
                  <button type="submit" disabled={saving} className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-black disabled:opacity-50 flex items-center gap-2">
                    {saving ? "Saving..." : (editingRoute ? "Update Route" : "Create Route")}
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default NavigationManagerPanel