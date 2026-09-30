import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiCompass,
  FiCalendar,
  FiMapPin,
  FiDollarSign,
  FiCheckCircle,
  FiArrowRight,
  FiAward,
  FiShield,
  FiEye,
  FiChevronDown,
  FiChevronUp,
  FiInfo,
  FiLayers,
  FiActivity,
  FiCheck,
  FiX,
  FiCheckSquare,
  FiSearch
} from "react-icons/fi"
import itineraryApi from "../../api/itineraryApi"
import useToast from "../../hooks/useToast"
import CuratedCompareModal from "./CuratedCompareModal"
import AltitudeSafetyModal from "./AltitudeSafetyModal"
import CostBreakdownModal from "./CostBreakdownModal"
import PackingChecklistModal from "./PackingChecklistModal"
import LocalTrailSecrets from "./LocalTrailSecrets"
import PrintableTravelBrief from "./PrintableTravelBrief"
import TippingAndCurrencyGuide from "./TippingAndCurrencyGuide"

const PERSONA_TABS = [
  { id: "all", label: "All Journeys", labelNe: "सबै यात्रा", icon: "✨" },
  { id: "nepali", label: "Domestic Explorer", labelNe: "नेपाली आन्तरिक", icon: "🇳🇵" },
  { id: "foreign", label: "International", labelNe: "विदेशी पर्यटक", icon: "🌍" },
  { id: "trekking", label: "Himalayan Treks", labelNe: "हिमाल पदयात्रा", icon: "🏔️" },
  { id: "pilgrimage", label: "Pilgrimage", labelNe: "धार्मिक यात्रा", icon: "🕉️" },
  { id: "wildlife", label: "Wildlife Safari", labelNe: "जङ्गल सफारी", icon: "🌿" },
  { id: "weekend", label: "Weekend Escapes", labelNe: "सप्ताहन्त", icon: "⚡" },
]

export default function CuratedItineraryShowcase({ onSelectPlan, currentNationality = "foreign" }) {
  const { showToast } = useToast()
  const [activeTab, setActiveTab] = useState("all")
  const [itineraries, setItineraries] = useState([])
  const [loading, setLoading] = useState(true)
  const [expandedSlug, setExpandedSlug] = useState(null)
  const [loadingSlug, setLoadingSlug] = useState(null)

  // Comparison State
  const [selectedSlugs, setSelectedSlugs] = useState([])
  const [compareData, setCompareData] = useState(null)
  const [isCompareOpen, setIsCompareOpen] = useState(false)
  const [loadingCompare, setLoadingCompare] = useState(false)

  // Safety Modal State
  const [activeSafetyData, setActiveSafetyData] = useState(null)
  const [activeSafetyTitle, setActiveSafetyTitle] = useState("")
  const [isSafetyOpen, setIsSafetyOpen] = useState(false)

  // Cost Modal State
  const [activeCostData, setActiveCostData] = useState(null)
  const [activeCostTitle, setActiveCostTitle] = useState("")
  const [isCostOpen, setIsCostOpen] = useState(false)
  const [costParams, setCostParams] = useState({
    nationality: currentNationality || "nepali",
    style: "standard",
    travelers: 1,
  })
  const [activeCostSlug, setActiveCostSlug] = useState(null)

  // Packing Modal State
  const [activePackingData, setActivePackingData] = useState(null)
  const [activePackingTitle, setActivePackingTitle] = useState("")
  const [activePackingSlug, setActivePackingSlug] = useState("")
  const [isPackingOpen, setIsPackingOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")

  // Human Trail Wisdom, Offline Print & Tipping States
  const [isSecretsOpen, setIsSecretsOpen] = useState(false)
  const [isTippingOpen, setIsTippingOpen] = useState(false)
  const [isPrintOpen, setIsPrintOpen] = useState(false)
  const [activePrintPlan, setActivePrintPlan] = useState(null)
  const [loadingPrintSlug, setLoadingPrintSlug] = useState(null)

  const handleOpenPrintBrief = async (slug, title) => {
    setLoadingPrintSlug(slug)
    try {
      const { data } = await itineraryApi.getCuratedDetail(slug)
      setActivePrintPlan(data)
      setIsPrintOpen(true)
    } catch (err) {
      showToast("Unable to open offline field brief", "error")
    } finally {
      setLoadingPrintSlug(null)
    }
  }

  useEffect(() => {
    let alive = true
    setLoading(true)
    const isCategory = ["trekking", "pilgrimage", "wildlife", "weekend"].includes(activeTab)
    const params = isCategory ? { category: activeTab } : { persona: activeTab }

    itineraryApi
      .getCuratedList(params)
      .then(({ data }) => {
        if (!alive) return
        setItineraries(data.results || [])
        setLoading(false)
      })
      .catch(() => {
        if (!alive) return
        setItineraries([])
        setLoading(false)
      })

    return () => {
      alive = false
    }
  }, [activeTab])

  const handleLoadPlan = async (slug) => {
    setLoadingSlug(slug)
    try {
      const { data } = await itineraryApi.loadCuratedPlanner(slug, {
        nationality: currentNationality,
      })
      if (onSelectPlan) {
        onSelectPlan(data)
        showToast(`Loaded curated plan: ${data.title}`, "success")
        // Smoothly scroll down to the generated plan
        const planEl = document.getElementById("itinerary-plan-results")
        if (planEl) {
          planEl.scrollIntoView({ behavior: "smooth", block: "start" })
        }
      }
    } catch {
      showToast("Could not load this curated itinerary into planner.", "error")
    } finally {
      setLoadingSlug(null)
    }
  }

  // Toggle selection for comparison
  const toggleSelectForCompare = (slug) => {
    if (selectedSlugs.includes(slug)) {
      setSelectedSlugs((prev) => prev.filter((s) => s !== slug))
    } else {
      if (selectedSlugs.length >= 3) {
        showToast("You can compare up to 3 itineraries simultaneously.", "warning")
        return
      }
      setSelectedSlugs((prev) => [...prev, slug])
      showToast("Added to comparison drawer", "info")
    }
  }

  // Open comparison modal
  const handleOpenComparison = async () => {
    if (selectedSlugs.length < 2) {
      showToast("Select at least 2 itineraries to compare.", "info")
      return
    }
    setLoadingCompare(true)
    try {
      const { data } = await itineraryApi.compareCurated({
        slugs: selectedSlugs.join(","),
        nationality: currentNationality,
      })
      setCompareData(data)
      setIsCompareOpen(true)
    } catch {
      showToast("Could not load comparative data.", "error")
    } finally {
      setLoadingCompare(false)
    }
  }

  // Open Safety Modal
  const handleOpenSafety = async (slug, title) => {
    try {
      const { data } = await itineraryApi.getCuratedSafety(slug)
      setActiveSafetyData(data.safety)
      setActiveSafetyTitle(data.title || title)
      setIsSafetyOpen(true)
    } catch {
      showToast("Could not load altitude safety analysis.", "error")
    }
  }

  // Open Cost Breakdown Modal
  const handleOpenCost = async (slug, title, overrides = {}) => {
    setActiveCostSlug(slug)
    setActiveCostTitle(title)
    const nextParams = { ...costParams, ...overrides }
    setCostParams(nextParams)
    try {
      const { data } = await itineraryApi.getCuratedDetail(slug, nextParams)
      if (data.cost_breakdown) {
        setActiveCostData(data.cost_breakdown)
        setIsCostOpen(true)
      }
    } catch {
      showToast("Could not load cost breakdown.", "error")
    }
  }

  // Open Packing Checklist Modal
  const handleOpenPacking = async (slug, title) => {
    setActivePackingSlug(slug)
    setActivePackingTitle(title)
    try {
      const { data } = await itineraryApi.getCuratedPacking(slug)
      setActivePackingData(data.packing)
      setIsPackingOpen(true)
    } catch {
      showToast("Could not load gear & packing checklist.", "error")
    }
  }

  // Recompute cost when modal parameters change
  const handleChangeCostParams = (newParams) => {
    if (activeCostSlug) {
      handleOpenCost(activeCostSlug, activeCostTitle, newParams)
    }
  }

  const filteredItineraries = itineraries.filter((item) => {
    if (!searchQuery.trim()) return true
    const q = searchQuery.toLowerCase()
    return (
      item.title?.toLowerCase().includes(q) ||
      item.title_nepali?.toLowerCase().includes(q) ||
      item.summary?.toLowerCase().includes(q) ||
      item.start_city?.toLowerCase().includes(q) ||
      item.end_city?.toLowerCase().includes(q) ||
      item.category?.toLowerCase().includes(q)
    )
  })

  return (
    <section className="ny-panel p-5 sm:p-7 mb-8 border border-[var(--ny-border)] bg-gradient-to-b from-white to-slate-50/60 rounded-2xl shadow-sm">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[var(--ny-border)] pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-100 text-emerald-800 text-sm font-bold">
              ★
            </span>
            <p className="ny-kicker text-emerald-700 font-bold uppercase tracking-wider text-xs">
              Curated Signature Journeys · विशेष सम्पादित यात्रा योजनाहरू
            </p>
          </div>
          <h2 className="mt-1 text-2xl font-bold tracking-tight text-[var(--ny-text-primary)]">
            Explore Handcrafted Nepal Itineraries
          </h2>
          <p className="mt-1 text-sm text-[var(--ny-text-secondary)]">
            Verified day-by-day plans designed for both Nepalese domestic explorers and international trekkers,
            with official permits, real elevations, and local transport options.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 self-start md:self-auto">
          {/* Comparison Bar Button */}
          {selectedSlugs.length > 0 && (
            <button
              type="button"
              disabled={loadingCompare}
              onClick={handleOpenComparison}
              className="ny-btn ny-btn-primary flex items-center gap-2 text-xs font-bold py-1.5 px-3 rounded-xl shadow-md animate-pulse"
            >
              <FiLayers size={14} />
              <span>Compare Selected ({selectedSlugs.length})</span>
            </button>
          )}

          <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl text-xs font-semibold text-slate-700">
            <span className="px-2 py-1 bg-white rounded-lg shadow-xs text-emerald-800">100% Verified Routes</span>
            <span className="px-2 py-1">Dual Persona: 🇳🇵 Nepali & 🌍 Foreign</span>
          </div>

          <button
            type="button"
            onClick={() => setIsSecretsOpen(true)}
            className="ny-btn bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-300 text-xs font-bold py-1.5 px-3 rounded-xl flex items-center gap-1.5 shadow-2xs transition"
            title="Read authentic Sherpa trail rules, Dal Bhat culture, and Devanagari phrasebook"
          >
            <span>🏔️</span>
            <span>Trail Wisdom & Etiquette</span>
          </button>

          <button
            type="button"
            onClick={() => setIsTippingOpen(true)}
            className="ny-btn bg-emerald-50 hover:bg-emerald-100 text-emerald-900 border border-emerald-300 text-xs font-bold py-1.5 px-3 rounded-xl flex items-center gap-1.5 shadow-2xs transition"
            title="Guide & porter tipping norms, envelope customs, and mountain cash realities"
          >
            <span>💵</span>
            <span>Tipping & Cash Guide</span>
          </button>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="mt-4 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <FiSearch className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" size={15} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search journeys (e.g. Everest, Pokhara, Mustang, Safari, Rara)…"
            className="w-full pl-9 pr-8 py-2 text-xs rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500 shadow-2xs"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery("")}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              <FiX size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Persona & Category Tabs */}
      <div className="mt-4 flex gap-2 overflow-x-auto pb-2 scrollbar-none" role="tablist">
        {PERSONA_TABS.map((tab) => {
          const active = activeTab === tab.id
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 whitespace-nowrap rounded-xl px-3.5 py-2 text-xs font-semibold transition shadow-2xs ${
                active
                  ? "bg-emerald-700 text-white shadow-sm"
                  : "bg-white border border-slate-200 text-slate-700 hover:border-emerald-500 hover:text-emerald-700"
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
              <span className="text-[10px] opacity-80 hidden sm:inline">({tab.labelNe})</span>
            </button>
          )
        })}
      </div>

      {/* Itinerary Cards Grid */}
      <div className="mt-6">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[1, 2, 3].map((n) => (
              <div key={n} className="h-80 rounded-xl bg-slate-100 animate-pulse" />
            ))}
          </div>
        ) : filteredItineraries.length === 0 ? (
          <div className="text-center py-12 text-slate-500 text-sm">
            No curated itineraries match your search or filter.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredItineraries.map((item) => {
              const isExpanded = expandedSlug === item.slug
              const isLoading = loadingSlug === item.slug
              const isDomestic = item.persona === "nepali"
              const isForeignOnly = item.persona === "foreign"
              const isSelected = selectedSlugs.includes(item.slug)
              const hasHighAltitude = (item.max_elevation_m || 0) >= 2500

              return (
                <div
                  key={item.slug}
                  className={`group flex flex-col justify-between overflow-hidden rounded-xl border bg-white shadow-sm hover:shadow-md transition ${
                    isSelected ? "border-amber-500 ring-2 ring-amber-400/40" : "border-slate-200"
                  }`}
                >
                  <div>
                    {/* Card Cover Header */}
                    <div className="relative h-48 w-full overflow-hidden bg-slate-100">
                      <img
                        src={item.cover_image}
                        alt={item.title}
                        className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                        loading="lazy"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />

                      {/* Top Badges */}
                      <div className="absolute top-3 left-3 flex flex-wrap gap-1.5">
                        <span className="rounded-md bg-black/60 backdrop-blur-xs px-2.5 py-1 text-[11px] font-bold text-white uppercase tracking-wider">
                          {item.days} Days
                        </span>
                        {isDomestic && (
                          <span className="rounded-md bg-red-600 px-2 py-1 text-[10px] font-bold text-white">
                            🇳🇵 नेपाली पर्यटक विशेष
                          </span>
                        )}
                        {isForeignOnly && (
                          <span className="rounded-md bg-blue-600 px-2 py-1 text-[10px] font-bold text-white">
                            🌍 International Iconic
                          </span>
                        )}
                        {!isDomestic && !isForeignOnly && (
                          <span className="rounded-md bg-emerald-600 px-2 py-1 text-[10px] font-bold text-white">
                            🇳🇵 & 🌍 All Travelers
                          </span>
                        )}
                      </div>

                      {/* Top Right: Compare Checkbox */}
                      <div className="absolute top-3 right-3 flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => toggleSelectForCompare(item.slug)}
                          className={`flex items-center gap-1 text-[11px] font-bold px-2 py-1 rounded-md backdrop-blur-xs transition ${
                            isSelected
                              ? "bg-amber-400 text-slate-950 font-black shadow-sm"
                              : "bg-black/60 text-white hover:bg-black/80"
                          }`}
                          title="Select to compare side-by-side"
                        >
                          {isSelected ? <FiCheck size={12} /> : <FiLayers size={12} />}
                          <span>{isSelected ? "Comparing" : "Compare"}</span>
                        </button>
                      </div>

                      {/* Title & Nepali Title Overlay */}
                      <div className="absolute bottom-3 left-3 right-3 text-white">
                        <h3 className="text-base font-bold leading-snug drop-shadow-sm line-clamp-2">
                          {item.title}
                        </h3>
                        {item.title_nepali && (
                          <p className="text-xs text-emerald-200 line-clamp-1 drop-shadow-xs mt-0.5">
                            {item.title_nepali}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Content Section */}
                    <div className="p-4 space-y-3">
                      <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">
                        {item.summary}
                      </p>

                      {/* Meta Pills */}
                      <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-600 border-y border-slate-100 py-2.5">
                        <div className="flex items-center gap-1.5">
                          <FiMapPin className="text-emerald-600 shrink-0" size={13} />
                          <span className="truncate">{item.start_city} → {item.end_city}</span>
                        </div>
                        <div className="flex items-center gap-1.5 justify-end">
                          <FiCompass className="text-emerald-600 shrink-0" size={13} />
                          <span>Max {item.max_elevation_m ? `${item.max_elevation_m.toLocaleString()}m` : "Sub-Alpine"}</span>
                        </div>
                      </div>

                      {/* Feature Tags & Quick Modals */}
                      <div className="flex flex-wrap gap-1.5 pt-0.5">
                        {hasHighAltitude && (
                          <button
                            type="button"
                            onClick={() => handleOpenSafety(item.slug, item.title)}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-rose-50 border border-rose-200 text-rose-700 text-[10px] font-bold hover:bg-rose-100 transition"
                            title="Open Altitude Safety & AMS Guidelines"
                          >
                            <FiActivity size={11} />
                            <span>AMS & Altitude Guide ({item.max_elevation_m}m)</span>
                          </button>
                        )}

                        <button
                          type="button"
                          onClick={() => handleOpenCost(item.slug, item.title)}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-50 border border-emerald-200 text-emerald-700 text-[10px] font-bold hover:bg-emerald-100 transition"
                          title="Open Itemized Cost Calculator"
                        >
                          <FiDollarSign size={11} />
                          <span>Cost Calculator</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => handleOpenPacking(item.slug, item.title)}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-blue-50 border border-blue-200 text-blue-700 text-[10px] font-bold hover:bg-blue-100 transition"
                          title="Open Interactive Gear & Packing Checklist"
                        >
                          <FiCheckSquare size={11} />
                          <span>Gear Checklist</span>
                        </button>

                        <button
                          type="button"
                          disabled={loadingPrintSlug === item.slug}
                          onClick={() => handleOpenPrintBrief(item.slug, item.title)}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-100 border border-slate-300 text-slate-800 text-[10px] font-bold hover:bg-slate-200 transition"
                          title="Generate printable field dossier & emergency SOS card"
                        >
                          <span>🖨️</span>
                          <span>{loadingPrintSlug === item.slug ? "Preparing…" : "Field Dossier"}</span>
                        </button>
                      </div>

                      {/* Highlights */}
                      {item.highlights && item.highlights.length > 0 && (
                        <div className="space-y-1">
                          <p className="text-[11px] font-bold text-slate-700 uppercase tracking-wider">
                            Key Highlights:
                          </p>
                          <ul className="space-y-1">
                            {item.highlights.slice(0, 2).map((hl, idx) => (
                              <li key={idx} className="flex items-start gap-1.5 text-xs text-slate-600">
                                <span className="text-emerald-600 font-bold shrink-0">✓</span>
                                <span className="line-clamp-1">{hl}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Expandable Details Drawer */}
                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden space-y-2.5 pt-2 text-xs border-t border-slate-100"
                          >
                            {item.permits_info && (
                              <div className="bg-slate-50 p-2.5 rounded-lg space-y-1">
                                <span className="font-bold text-slate-800 flex items-center gap-1">
                                  <FiShield size={12} className="text-emerald-600" />
                                  Permits & Fees Guidance:
                                </span>
                                {item.permits_info.nepali && (
                                  <p className="text-slate-600 text-[11px]">
                                    <strong className="text-red-700">नेपाली:</strong> {item.permits_info.nepali}
                                  </p>
                                )}
                                {item.permits_info.foreign && (
                                  <p className="text-slate-600 text-[11px]">
                                    <strong className="text-blue-700">Foreign:</strong> {item.permits_info.foreign}
                                  </p>
                                )}
                              </div>
                            )}

                            {item.local_food_recommendations && (
                              <div className="text-slate-600 text-[11px]">
                                <strong className="text-slate-800">Local Cuisine:</strong> {item.local_food_recommendations}
                              </div>
                            )}

                            {item.transport_info && (
                              <div className="text-slate-600 text-[11px]">
                                <strong className="text-slate-800">Transport:</strong> {item.transport_info}
                              </div>
                            )}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </div>

                  {/* Footer & Actions */}
                  <div className="p-4 pt-0 space-y-2.5">
                    {/* Budget Display */}
                    <div className="flex items-center justify-between border-t border-slate-100 pt-3">
                      <div>
                        <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Estimated Budget</span>
                        <div className="flex items-baseline gap-1.5">
                          <span className="text-sm font-bold text-slate-900">
                            NPR {item.estimated_budget_npr?.toLocaleString()}
                          </span>
                          {item.estimated_budget_usd && (
                            <span className="text-xs text-slate-500">
                              (≈ ${item.estimated_budget_usd})
                            </span>
                          )}
                        </div>
                      </div>

                      <button
                        type="button"
                        onClick={() => setExpandedSlug(isExpanded ? null : item.slug)}
                        className="text-xs font-semibold text-emerald-700 hover:text-emerald-900 flex items-center gap-1"
                      >
                        {isExpanded ? (
                          <>Less <FiChevronUp size={14} /></>
                        ) : (
                          <>Details <FiChevronDown size={14} /></>
                        )}
                      </button>
                    </div>

                    {/* Primary Button */}
                    <button
                      type="button"
                      disabled={isLoading}
                      onClick={() => handleLoadPlan(item.slug)}
                      className="w-full ny-btn ny-btn-primary flex items-center justify-center gap-2 py-2 text-xs font-bold rounded-xl transition"
                    >
                      {isLoading ? (
                        <>Loading Milestones…</>
                      ) : (
                        <>
                          <span>Load into Planner (योजना लोड गर्नुहोस्)</span>
                          <FiArrowRight size={14} />
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Comparison Modal */}
      <CuratedCompareModal
        isOpen={isCompareOpen}
        onClose={() => setIsCompareOpen(false)}
        comparisonData={compareData}
        onSelectItinerary={handleLoadPlan}
        onRemoveFromCompare={(slug) => {
          setSelectedSlugs((prev) => prev.filter((s) => s !== slug))
          if (compareData) {
            setCompareData({
              ...compareData,
              comparison: compareData.comparison.filter((c) => c.slug !== slug),
            })
          }
        }}
      />

      {/* Altitude Safety & AMS Modal */}
      <AltitudeSafetyModal
        isOpen={isSafetyOpen}
        onClose={() => setIsSafetyOpen(false)}
        safetyData={activeSafetyData}
        title={activeSafetyTitle}
      />

      {/* Cost Breakdown & Currency Modal */}
      <CostBreakdownModal
        isOpen={isCostOpen}
        onClose={() => setIsCostOpen(false)}
        costData={activeCostData}
        title={activeCostTitle}
        onChangeParameters={handleChangeCostParams}
        currentParams={costParams}
      />

      {/* Packing Checklist & Local Rental Modal */}
      <PackingChecklistModal
        isOpen={isPackingOpen}
        onClose={() => setIsPackingOpen(false)}
        packingData={activePackingData}
        title={activePackingTitle}
        slug={activePackingSlug}
      />

      {/* Local Trail Secrets & Mountain Wisdom */}
      <LocalTrailSecrets
        isOpen={isSecretsOpen}
        onClose={() => setIsSecretsOpen(false)}
      />

      {/* Tipping & Mountain Cash Guide */}
      <TippingAndCurrencyGuide
        isOpen={isTippingOpen}
        onClose={() => setIsTippingOpen(false)}
      />

      {/* Printable Travel Brief & SOS Field Dossier */}
      <PrintableTravelBrief
        isOpen={isPrintOpen}
        onClose={() => setIsPrintOpen(false)}
        plan={activePrintPlan}
      />
    </section>
  )
}
