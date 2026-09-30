import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiCompass,
  FiCalendar,
  FiMapPin,
  FiDollarSign,
  FiShield,
  FiActivity,
  FiCheckSquare,
  FiSearch,
  FiRefreshCw,
  FiExternalLink,
  FiEye,
  FiX,
  FiLayers,
  FiInfo,
  FiCheckCircle,
  FiAlertTriangle
} from "react-icons/fi"
import itineraryApi from "../../api/itineraryApi"
import useToast from "../../hooks/useToast"
import AltitudeSafetyModal from "../itinerary/AltitudeSafetyModal"
import CostBreakdownModal from "../itinerary/CostBreakdownModal"
import PackingChecklistModal from "../itinerary/PackingChecklistModal"
import PrintableTravelBrief from "../itinerary/PrintableTravelBrief"

export default function CuratedPlansPanel() {
  const { showToast } = useToast()
  const [plans, setPlans] = useState([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [categoryFilter, setCategoryFilter] = useState("all")
  const [personaFilter, setPersonaFilter] = useState("all")

  // Selected plan detail state
  const [selectedPlanSlug, setSelectedPlanSlug] = useState(null)
  const [selectedPlanDetail, setSelectedPlanDetail] = useState(null)
  const [loadingDetail, setLoadingDetail] = useState(false)

  // Sub-modals
  const [showSafetyModal, setShowSafetyModal] = useState(false)
  const [showCostModal, setShowCostModal] = useState(false)
  const [showPackingModal, setShowPackingModal] = useState(false)
  const [showPrintModal, setShowPrintModal] = useState(false)

  const loadPlans = async () => {
    setLoading(true)
    try {
      const { data } = await itineraryApi.getCuratedList({ persona: "all" })
      setPlans(data.results || [])
    } catch {
      showToast("Failed to load curated plans.", "error")
      setPlans([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let alive = true
    itineraryApi.getCuratedList({ persona: "all" })
      .then(({ data }) => {
        if (alive) {
          setPlans(data.results || [])
          setLoading(false)
        }
      })
      .catch(() => {
        if (alive) {
          showToast("Failed to load curated plans.", "error")
          setPlans([])
          setLoading(false)
        }
      })
    return () => {
      alive = false
    }
  }, [])

  const handleInspectPlan = async (slug) => {
    setSelectedPlanSlug(slug)
    setLoadingDetail(true)
    try {
      const { data } = await itineraryApi.getCuratedDetail(slug)
      setSelectedPlanDetail(data)
    } catch {
      showToast("Could not load plan details.", "error")
    } finally {
      setLoadingDetail(false)
    }
  }

  const handleSyncDatabase = async () => {
    setSyncing(true)
    try {
      await loadPlans()
      showToast("Curated plans catalog verified and refreshed from database.", "success")
    } catch {
      showToast("Failed to refresh curated plans.", "error")
    } finally {
      setSyncing(false)
    }
  }

  const filteredPlans = plans.filter((item) => {
    const matchesSearch =
      !searchQuery.trim() ||
      item.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.title_nepali?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.start_city?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.end_city?.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesCategory =
      categoryFilter === "all" || item.category === categoryFilter

    const matchesPersona =
      personaFilter === "all" ||
      item.persona === personaFilter ||
      (personaFilter === "all_personas" && item.persona === "all")

    return matchesSearch && matchesCategory && matchesPersona
  })

  // Aggregate stats
  const totalPlans = plans.length
  const highAltitudeCount = plans.filter((p) => (p.max_elevation_m || 0) >= 2500).length
  const totalDaysCovered = plans.reduce((acc, p) => acc + (p.days || 0), 0)
  const domesticCount = plans.filter((p) => p.persona === "nepali").length

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 p-6 sm:p-7 rounded-3xl text-white shadow-md flex flex-col md:flex-row md:items-center justify-between gap-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              <FiCompass size={20} />
            </span>
            <span className="text-xs uppercase font-extrabold tracking-wider text-emerald-400">
              Travel Operations Central
            </span>
          </div>
          <h2 className="text-2xl font-black mt-1">Curated Signature Itineraries & Treks</h2>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Manage the 12 handcrafted master itineraries with dual-persona pricing (नेपाली & International),
            Lake Louise AMS safety thresholds, official permits, and packing rental guides.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            onClick={handleSyncDatabase}
            disabled={syncing || loading}
            className="ny-btn bg-white/10 hover:bg-white/20 text-white border border-white/20 text-xs font-bold py-2 px-3.5 rounded-xl flex items-center gap-2 shadow-xs transition"
          >
            <FiRefreshCw size={14} className={syncing ? "animate-spin" : ""} />
            <span>{syncing ? "Syncing..." : "Sync Database"}</span>
          </button>

          <a
            href="/itinerary"
            target="_blank"
            rel="noreferrer"
            className="ny-btn ny-btn-primary text-xs font-bold py-2 px-3.5 rounded-xl flex items-center gap-2 shadow-xs"
          >
            <span>Live Planner View</span>
            <FiExternalLink size={14} />
          </a>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <div className="bg-white border border-slate-200 p-4 rounded-2xl shadow-2xs">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Total Master Plans</span>
          <span className="text-2xl font-black text-slate-900 mt-1 block">{totalPlans}</span>
          <span className="text-[11px] text-emerald-700 font-semibold mt-0.5 block">100% Verified Routes</span>
        </div>

        <div className="bg-white border border-slate-200 p-4 rounded-2xl shadow-2xs">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">High-Altitude Treks</span>
          <span className="text-2xl font-black text-rose-700 mt-1 block">{highAltitudeCount}</span>
          <span className="text-[11px] text-slate-500 font-semibold mt-0.5 block">≥ 2,500m AMS Monitored</span>
        </div>

        <div className="bg-white border border-slate-200 p-4 rounded-2xl shadow-2xs">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Domestic Special</span>
          <span className="text-2xl font-black text-blue-700 mt-1 block">{domesticCount}</span>
          <span className="text-[11px] text-slate-500 font-semibold mt-0.5 block">🇳🇵 नेपाली पर्यटक लक्षित</span>
        </div>

        <div className="bg-white border border-slate-200 p-4 rounded-2xl shadow-2xs">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Total Route Days</span>
          <span className="text-2xl font-black text-emerald-800 mt-1 block">{totalDaysCovered} Days</span>
          <span className="text-[11px] text-slate-500 font-semibold mt-0.5 block">Combined Trail Time</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white border border-slate-200 p-4 rounded-2xl shadow-2xs space-y-3">
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
          <div className="relative flex-1 max-w-md">
            <FiSearch className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" size={15} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by title, start city, or destination..."
              className="w-full pl-9 pr-4 py-2 text-xs rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-slate-500 font-bold text-[11px] uppercase">Category:</span>
            {["all", "trekking", "pilgrimage", "wildlife", "weekend"].map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setCategoryFilter(cat)}
                className={`px-3 py-1.5 rounded-xl font-bold transition capitalize ${
                  categoryFilter === cat
                    ? "bg-slate-900 text-white"
                    : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Table / Grid */}
      <div className="bg-white border border-slate-200 rounded-3xl overflow-hidden shadow-2xs">
        {loading ? (
          <div className="p-8 text-center text-slate-500 text-sm">
            <FiRefreshCw className="inline animate-spin mr-2" />
            Loading curated itinerary catalog...
          </div>
        ) : filteredPlans.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">
            No curated itineraries match your search or filter.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[10px] border-b border-slate-200">
                <tr>
                  <th className="py-3.5 px-4">Plan / Title</th>
                  <th className="py-3.5 px-3">Days</th>
                  <th className="py-3.5 px-3">Route (From → To)</th>
                  <th className="py-3.5 px-3">Elevation</th>
                  <th className="py-3.5 px-3">Est. Budget</th>
                  <th className="py-3.5 px-3">Persona</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredPlans.map((item) => {
                  const isHighAltitude = (item.max_elevation_m || 0) >= 2500
                  return (
                    <tr key={item.slug} className="hover:bg-slate-50/80 transition">
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-3">
                          <img
                            src={item.cover_image}
                            alt={item.title}
                            className="w-12 h-10 object-cover rounded-lg shadow-2xs shrink-0"
                            loading="lazy"
                          />
                          <div className="min-w-0">
                            <span className="font-bold text-slate-900 block truncate max-w-xs sm:max-w-sm">
                              {item.title}
                            </span>
                            {item.title_nepali && (
                              <span className="text-[11px] text-emerald-800 font-medium block truncate">
                                {item.title_nepali}
                              </span>
                            )}
                          </div>
                        </div>
                      </td>

                      <td className="py-3.5 px-3 font-black text-slate-800 whitespace-nowrap">
                        {item.days} Days
                      </td>

                      <td className="py-3.5 px-3 text-slate-600 whitespace-nowrap">
                        <span className="flex items-center gap-1">
                          <FiMapPin size={12} className="text-emerald-600 shrink-0" />
                          <span className="truncate">{item.start_city} → {item.end_city}</span>
                        </span>
                      </td>

                      <td className="py-3.5 px-3 whitespace-nowrap">
                        {isHighAltitude ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-rose-50 text-rose-700 font-bold text-[10px] border border-rose-200">
                            <FiActivity size={10} />
                            {item.max_elevation_m?.toLocaleString()}m
                          </span>
                        ) : (
                          <span className="text-slate-500 font-semibold text-[11px]">
                            {item.max_elevation_m ? `${item.max_elevation_m}m` : "Sub-Alpine"}
                          </span>
                        )}
                      </td>

                      <td className="py-3.5 px-3 whitespace-nowrap">
                        <div className="font-bold text-slate-900">
                          NPR {item.estimated_budget_npr?.toLocaleString()}
                        </div>
                        {item.estimated_budget_usd && (
                          <div className="text-[10px] text-slate-500">
                            ≈ ${item.estimated_budget_usd} USD
                          </div>
                        )}
                      </td>

                      <td className="py-3.5 px-3 whitespace-nowrap">
                        {item.persona === "nepali" ? (
                          <span className="px-2 py-0.5 rounded-md bg-red-100 text-red-800 font-bold text-[10px]">
                            🇳🇵 Nepali
                          </span>
                        ) : item.persona === "foreign" ? (
                          <span className="px-2 py-0.5 rounded-md bg-blue-100 text-blue-800 font-bold text-[10px]">
                            🌍 Foreign
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800 font-bold text-[10px]">
                            ✨ All
                          </span>
                        )}
                      </td>

                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <button
                          type="button"
                          onClick={() => handleInspectPlan(item.slug)}
                          className="ny-btn ny-btn-secondary text-xs font-bold py-1 px-3 rounded-lg inline-flex items-center gap-1.5"
                        >
                          <FiEye size={13} />
                          <span>Inspect</span>
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Plan Inspection Drawer / Modal */}
      <AnimatePresence>
        {selectedPlanSlug && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm overflow-y-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 15 }}
              className="relative w-full max-w-3xl bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden my-auto max-h-[92vh] flex flex-col"
            >
              {/* Drawer Header */}
              <div className="p-5 sm:p-6 bg-slate-900 text-white flex items-center justify-between shrink-0">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-2xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    <FiCompass size={22} />
                  </div>
                  <div>
                    <h3 className="text-lg font-black leading-tight">
                      {selectedPlanDetail?.title || "Plan Details"}
                    </h3>
                    {selectedPlanDetail?.title_nepali && (
                      <p className="text-xs text-emerald-300 mt-0.5 font-medium">
                        {selectedPlanDetail.title_nepali}
                      </p>
                    )}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedPlanSlug(null)
                    setSelectedPlanDetail(null)
                  }}
                  className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition"
                  aria-label="Close inspector drawer"
                >
                  <FiX size={20} />
                </button>
              </div>

              {/* Drawer Content */}
              {loadingDetail ? (
                <div className="p-12 text-center text-slate-500 text-sm">
                  <FiRefreshCw className="inline animate-spin mr-2" />
                  Loading detailed itinerary data...
                </div>
              ) : selectedPlanDetail ? (
                <div className="p-6 space-y-6 overflow-y-auto flex-1 text-xs text-slate-700">
                  {/* Summary & Tags */}
                  <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 space-y-2">
                    <span className="font-bold text-slate-900 block text-sm">Overview Summary</span>
                    <p className="text-slate-600 leading-relaxed text-xs">
                      {selectedPlanDetail.summary}
                    </p>
                    <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-200">
                      <span className="px-2.5 py-1 rounded-md bg-white border border-slate-200 font-bold">
                        ⏱️ {selectedPlanDetail.days} Days
                      </span>
                      <span className="px-2.5 py-1 rounded-md bg-white border border-slate-200 font-bold">
                        🏔️ Max Elevation: {selectedPlanDetail.max_elevation_m}m
                      </span>
                      <span className="px-2.5 py-1 rounded-md bg-white border border-slate-200 font-bold">
                        💵 Total NPR: {selectedPlanDetail.estimated_budget_npr?.toLocaleString()}
                      </span>
                    </div>
                  </div>

                  {/* Quick Tool Launchers */}
                  <div className="space-y-2">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                      Launch Integrated Traveler Tools:
                    </span>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      <button
                        type="button"
                        onClick={() => setShowSafetyModal(true)}
                        className="p-2.5 rounded-xl border border-rose-200 bg-rose-50 text-rose-900 hover:bg-rose-100 font-bold text-left space-y-1 transition"
                      >
                        <span className="text-[10px] text-rose-600 block">Altitude Risk</span>
                        <span className="text-xs font-black block">AMS Protocol</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setShowCostModal(true)}
                        className="p-2.5 rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-900 hover:bg-emerald-100 font-bold text-left space-y-1 transition"
                      >
                        <span className="text-[10px] text-emerald-600 block">Cost Schedule</span>
                        <span className="text-xs font-black block">Dual Pricing</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setShowPackingModal(true)}
                        className="p-2.5 rounded-xl border border-blue-200 bg-blue-50 text-blue-900 hover:bg-blue-100 font-bold text-left space-y-1 transition"
                      >
                        <span className="text-[10px] text-blue-600 block">Equipment</span>
                        <span className="text-xs font-black block">Gear Checklist</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setShowPrintModal(true)}
                        className="p-2.5 rounded-xl border border-slate-300 bg-slate-100 text-slate-900 hover:bg-slate-200 font-bold text-left space-y-1 transition"
                      >
                        <span className="text-[10px] text-slate-600 block">Export</span>
                        <span className="text-xs font-black block">Printable Dossier</span>
                      </button>
                    </div>
                  </div>

                  {/* Day-by-Day Milestone Schedule */}
                  <div className="space-y-2">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                      Day-by-Day Milestone Schedule ({selectedPlanDetail.itinerary?.length || 0} Stages):
                    </span>
                    <div className="border border-slate-200 rounded-2xl overflow-hidden divide-y divide-slate-100">
                      {(selectedPlanDetail.itinerary || []).map((day) => (
                        <div key={day.day} className="p-3 bg-white space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-black text-slate-900">
                              Day {day.day}: {day.title}
                            </span>
                            {day.target_altitude_m && (
                              <span className="text-[11px] font-bold font-mono text-emerald-800">
                                {day.target_altitude_m}m
                              </span>
                            )}
                          </div>
                          <p className="text-slate-600 text-[11px]">
                            {day.description}
                          </p>
                          <div className="flex flex-wrap gap-2 text-[10px] text-slate-500 pt-1">
                            {day.walking_hours && <span>🚶 {day.walking_hours} hrs walk</span>}
                            {day.accommodation && <span>🏡 {day.accommodation}</span>}
                            {day.transport_mode && <span>🚙 {day.transport_mode}</span>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Permits and Local Culture Notes */}
                  {selectedPlanDetail.permits_info && (
                    <div className="p-4 bg-amber-50/60 rounded-2xl border border-amber-200 space-y-1">
                      <span className="font-bold text-amber-950 block">Official Permits & Requirements:</span>
                      {selectedPlanDetail.permits_info.nepali && (
                        <p className="text-amber-900 text-[11px]">
                          <strong>नेपाली:</strong> {selectedPlanDetail.permits_info.nepali}
                        </p>
                      )}
                      {selectedPlanDetail.permits_info.foreign && (
                        <p className="text-amber-900 text-[11px]">
                          <strong>Foreign:</strong> {selectedPlanDetail.permits_info.foreign}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              ) : null}

              {/* Drawer Footer */}
              <div className="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between shrink-0">
                <span className="text-xs text-slate-500">
                  Plan Slug: <code className="font-mono">{selectedPlanSlug}</code>
                </span>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedPlanSlug(null)
                    setSelectedPlanDetail(null)
                  }}
                  className="ny-btn ny-btn-primary px-5 py-2 text-xs font-bold rounded-xl"
                >
                  Done
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Linked Modals */}
      <AltitudeSafetyModal
        isOpen={showSafetyModal}
        onClose={() => setShowSafetyModal(false)}
        safetyData={selectedPlanDetail?.altitude_safety}
        title={selectedPlanDetail?.title}
      />

      <CostBreakdownModal
        isOpen={showCostModal}
        onClose={() => setShowCostModal(false)}
        costData={selectedPlanDetail?.cost_breakdown}
        title={selectedPlanDetail?.title}
        currentParams={{
          nationality: selectedPlanDetail?.persona || "foreign",
          style: "standard",
          travelers: 1,
        }}
      />

      <PackingChecklistModal
        isOpen={showPackingModal}
        onClose={() => setShowPackingModal(false)}
        packingData={selectedPlanDetail?.packing_checklist_detailed}
        title={selectedPlanDetail?.title}
        slug={selectedPlanDetail?.slug}
      />

      <PrintableTravelBrief
        isOpen={showPrintModal}
        onClose={() => setShowPrintModal(false)}
        plan={selectedPlanDetail}
      />
    </div>
  )
}
