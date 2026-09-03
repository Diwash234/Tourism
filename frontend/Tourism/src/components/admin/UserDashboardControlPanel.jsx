import { useEffect, useState } from "react"
import {
  FiSliders,
  FiEye,
  FiEyeOff,
  FiVolume2,
  FiCheck,
  FiRefreshCw,
  FiToggleLeft,
  FiToggleRight,
  FiSave,
  FiLayout,
  FiActivity,
  FiZap,
} from "react-icons/fi"
import adminApi from "../../api/adminApi"
import configApi from "../../api/configApi"
import useToast from "../../hooks/useToast"

const DEFAULT_BLOCKS = [
  { key: "national-symbols", name: "Nepal National Symbols & Identity", description: "Shows coat of arms, rhododendron, Himalayan peaks, and cultural heritage symbols.", defaultEnabled: true },
  { key: "hero", name: "Welcome Hero & AI Search", description: "Personalized greeting with quick AI destination search bar.", defaultEnabled: true },
  { key: "weather-budget", name: "Live Weather & Budget Cards", description: "Real-time weather for current location and budget overview cards.", defaultEnabled: true },
  { key: "alerts", name: "Travel Alerts & Emergency Bulletins", description: "Active safety warnings, monsoon alerts, and road closures.", defaultEnabled: true },
  { key: "recommendations", name: "AI Personalized Recommendations", description: "Multi-stage MMR recommendation engine cards with diversity reasons.", defaultEnabled: true },
  { key: "trending", name: "Trending Nepal Destinations", description: "Featured places grid with cover photos and quick explore actions.", defaultEnabled: true },
  { key: "favorites", name: "Favorite Saved Places", description: "User's bookmarked destinations and quick access cards.", defaultEnabled: true },
  { key: "hotels", name: "Recommended Hotels & Stays", description: "Curated hotel stays near user's targeted locations.", defaultEnabled: true },
  { key: "culture", name: "Nepal Culture & Local Experiences", description: "Authentic local experiences, heritage tours, and cultural guides.", defaultEnabled: true },
  { key: "highlights", name: "Nepal Highlights & Marquee", description: "Interactive province marquee and why-visit-Nepal showcase.", defaultEnabled: true },
  { key: "safety", name: "Safety & Emergency Radar", description: "Heuristic safety score, earthquake status, and nearby hospital/police counts.", defaultEnabled: true },
  { key: "budget-summary", name: "Budget Expenditure Breakdown", description: "Detailed breakdown of logged travel expenses by category.", defaultEnabled: true },
  { key: "community-photos", name: "Community Photo Contribution Desk", description: "Destination photo search, upload studio, and community gallery.", defaultEnabled: true },
]

export default function UserDashboardControlPanel() {
  const { showToast } = useToast()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [blocksState, setBlocksState] = useState(
    Object.fromEntries(DEFAULT_BLOCKS.map((b) => [b.key, b.defaultEnabled]))
  )
  const [announcement, setAnnouncement] = useState("")
  const [announcementType, setAnnouncementType] = useState("info")
  const [enableFeedbackPrompt, setEnableFeedbackPrompt] = useState(true)
  const [enableAIReplanning, setEnableAIReplanning] = useState(true)
  const [enablePhotoUploads, setEnablePhotoUploads] = useState(true)

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    setLoading(true)
    try {
      const { data } = await configApi.getPublicConfig()
      const dashboardPage = data?.pages?.find((p) => p.key === "dashboard")
      if (dashboardPage?.sections?.length) {
        const activeKeys = new Set(dashboardPage.sections.map((s) => s.key))
        const newState = {}
        DEFAULT_BLOCKS.forEach((b) => {
          newState[b.key] = activeKeys.has(b.key)
        })
        setBlocksState(newState)
      }
      if (data?.visitor_notice) {
        setAnnouncement(data.visitor_notice.message || "")
        setAnnouncementType(data.visitor_notice.type || "info")
      }
    } catch (err) {
      console.log("Error loading dashboard config:", err)
    } finally {
      setLoading(false)
    }
  }

  const handleToggleBlock = (key) => {
    setBlocksState((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const handleSaveConfig = async () => {
    setSaving(true)
    try {
      const activeSections = DEFAULT_BLOCKS.filter((b) => blocksState[b.key]).map((b) => ({
        key: b.key,
        title: b.name,
      }))

      await adminApi.updateCMS({
        page_key: "dashboard",
        sections: activeSections,
      })

      if (announcement.trim()) {
        await adminApi.updateVisitorDesk({
          notice_message: announcement.trim(),
          notice_type: announcementType,
          notice_active: true,
        })
      }

      showToast("User Dashboard layout & settings published live!", "success")
    } catch (err) {
      showToast(err.response?.data?.detail || "Could not publish dashboard configuration", "error")
    } finally {
      setSaving(false)
    }
  }

  const activeCount = Object.values(blocksState).filter(Boolean).length

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-700 p-6 rounded-3xl text-white shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="px-3 py-1 rounded-full bg-amber-400 text-slate-950 text-xs font-black uppercase tracking-wider">
            User Experience Studio
          </span>
          <h2 className="text-2xl font-black mt-2 flex items-center gap-2">
            <FiLayout className="text-amber-400" /> User Dashboard Layout & Feature Controls
          </h2>
          <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
            Customize which components, engagement tools, AI replanning actions, and broadcast announcements appear on all traveler user dashboards in real time.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadConfig}
            disabled={loading}
            className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs flex items-center gap-2 border border-slate-600"
          >
            <FiRefreshCw className={loading ? "animate-spin" : ""} /> Refresh
          </button>
          <button
            onClick={handleSaveConfig}
            disabled={saving}
            className="px-6 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-black text-xs flex items-center gap-2 shadow-lg shadow-emerald-500/30 transition-all hover:scale-105"
          >
            <FiSave size={16} /> {saving ? "Publishing..." : "Publish Dashboard Layout Live"}
          </button>
        </div>
      </div>

      {/* Broadcast Notice Banner Studio */}
      <div className="bg-white border border-slate-200 p-6 rounded-3xl shadow-sm space-y-4">
        <h3 className="font-extrabold text-lg text-slate-900 flex items-center gap-2">
          <FiVolume2 className="text-amber-600" /> Traveler Broadcast Notice / Announcement
        </h3>
        <p className="text-xs text-slate-500">
          Publish a top banner notice visible on every user's dashboard (e.g. seasonal festival greetings, road closures, special offers).
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <div className="sm:col-span-3">
            <label className="text-xs font-bold text-slate-700 block mb-1">Notice Message</label>
            <input
              type="text"
              value={announcement}
              onChange={(e) => setAnnouncement(e.target.value)}
              placeholder="e.g. 🏔️ Autumn Trekking Season: Annapurna & Everest trails open with clear skies!"
              className="input-field text-xs"
            />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-700 block mb-1">Notice Type</label>
            <select
              value={announcementType}
              onChange={(e) => setAnnouncementType(e.target.value)}
              className="input-field text-xs"
            >
              <option value="info">ℹ️ Information (Blue)</option>
              <option value="warning">⚠️ Warning / Hazard (Amber)</option>
              <option value="success">🎉 Success / Festival (Green)</option>
              <option value="danger">🚨 Urgent Emergency (Red)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Engagement Feature Flags */}
      <div className="bg-white border border-slate-200 p-6 rounded-3xl shadow-sm space-y-4">
        <h3 className="font-extrabold text-lg text-slate-900 flex items-center gap-2">
          <FiZap className="text-emerald-700" /> Interactive Engagement & AI Feature Controls
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div
            onClick={() => setEnableAIReplanning(!enableAIReplanning)}
            className={`p-4 rounded-2xl border cursor-pointer transition-all flex items-center justify-between ${
              enableAIReplanning ? "bg-[#F7F8F5] border-[#2E6B5A]" : "bg-slate-50 border-slate-200 opacity-60"
            }`}
          >
            <div>
              <p className="font-bold text-xs text-slate-900">AI Itinerary Modification Bar</p>
              <p className="text-[11px] text-slate-500">Enable 1-click AI modification actions on user travel plans</p>
            </div>
            {enableAIReplanning ? <FiToggleRight size={24} className="text-emerald-700" /> : <FiToggleLeft size={24} className="text-slate-400" />}
          </div>

          <div
            onClick={() => setEnableFeedbackPrompt(!enableFeedbackPrompt)}
            className={`p-4 rounded-2xl border cursor-pointer transition-all flex items-center justify-between ${
              enableFeedbackPrompt ? "bg-emerald-50 border-emerald-300" : "bg-slate-50 border-slate-200 opacity-60"
            }`}
          >
            <div>
              <p className="font-bold text-xs text-slate-900">Traveler Feedback Prompt</p>
              <p className="text-[11px] text-slate-500">Show feedback trigger button and rating modal on dashboard</p>
            </div>
            {enableFeedbackPrompt ? <FiToggleRight size={24} className="text-emerald-600" /> : <FiToggleLeft size={24} className="text-slate-400" />}
          </div>

          <div
            onClick={() => setEnablePhotoUploads(!enablePhotoUploads)}
            className={`p-4 rounded-2xl border cursor-pointer transition-all flex items-center justify-between ${
              enablePhotoUploads ? "bg-amber-50 border-amber-300" : "bg-slate-50 border-slate-200 opacity-60"
            }`}
          >
            <div>
              <p className="font-bold text-xs text-slate-900">Community Photo Upload Desk</p>
              <p className="text-[11px] text-slate-500">Allow travelers to upload photos directly from dashboard</p>
            </div>
            {enablePhotoUploads ? <FiToggleRight size={24} className="text-amber-600" /> : <FiToggleLeft size={24} className="text-slate-400" />}
          </div>
        </div>
      </div>

      {/* Component Blocks Grid */}
      <div className="bg-white border border-slate-200 p-6 rounded-3xl shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-extrabold text-lg text-slate-900 flex items-center gap-2">
              <FiSliders className="text-emerald-600" /> User Dashboard Component Block Toggles
            </h3>
            <p className="text-xs text-slate-500">
              Active blocks ({activeCount} / {DEFAULT_BLOCKS.length}) will be rendered on the traveler's home dashboard page.
            </p>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => {
                const newState = {}
                DEFAULT_BLOCKS.forEach((b) => (newState[b.key] = true))
                setBlocksState(newState)
              }}
              className="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-xs font-bold text-slate-700"
            >
              Enable All
            </button>
            <button
              onClick={() => {
                const newState = {}
                DEFAULT_BLOCKS.forEach((b) => (newState[b.key] = false))
                setBlocksState(newState)
              }}
              className="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-xs font-bold text-slate-700"
            >
              Disable All
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
          {DEFAULT_BLOCKS.map((block) => {
            const enabled = blocksState[block.key]
            return (
              <div
                key={block.key}
                onClick={() => handleToggleBlock(block.key)}
                className={`p-4 rounded-2xl border cursor-pointer transition-all duration-200 flex flex-col justify-between space-y-3 ${
                  enabled
                    ? "bg-gradient-to-br from-emerald-50/50 to-white border-emerald-300 shadow-sm"
                    : "bg-slate-50 border-slate-200 opacity-60 hover:opacity-100"
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-extrabold text-sm text-slate-900">{block.name}</span>
                    {enabled ? (
                      <span className="px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800 text-[10px] font-black flex items-center gap-1">
                        <FiEye size={10} /> Active
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-md bg-slate-200 text-slate-600 text-[10px] font-bold flex items-center gap-1">
                        <FiEyeOff size={10} /> Hidden
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 line-clamp-2">{block.description}</p>
                </div>

                <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[10px]">
                  <span className="font-mono text-slate-400">Block key: {block.key}</span>
                  <span className={`font-bold ${enabled ? "text-emerald-700" : "text-slate-500"}`}>
                    {enabled ? "✓ Visible on Dashboard" : "Hidden"}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
