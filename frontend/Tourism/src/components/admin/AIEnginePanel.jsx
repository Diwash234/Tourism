import { useEffect, useState } from "react"
import {
  FiCpu, FiSliders, FiCheck, FiSave, FiSearch, FiShield,
  FiZap, FiCompass, FiDollarSign, FiAlertTriangle, FiCheckCircle, FiLock
} from "react-icons/fi"
import adminApi from "../../api/adminApi"
import destinationApi from "../../api/destinationApi"
import axiosClient from "../../api/axiosClient"
import useToast from "../../hooks/useToast"

const TABS = [
  ["general", "General & Models"],
  ["recommendations", "Recommendation Rules"],
  ["overrides", "Destination AI Overrides"],
  ["budget", "Budget Engine Rules"],
  ["risk", "Risk & Safety Thresholds"],
  ["assistant", "Assistant Instructions"],
]

export default function AIEnginePanel() {
  const { showToast } = useToast()
  const [activeTab, setActiveTab] = useState("general")
  const [busy, setBusy] = useState(false)

  // AI Configuration State
  const [aiConfig, setAiConfig] = useState({
    ai_enabled: true,
    model_provider: "fastapi_tf_idf_rf",
    temperature: 0.7,
    max_tokens: 1024,
    recommendation_weights: { budget: 25, activities: 20, season: 20, distance: 10, safety: 15, preferences: 10 },
    risk_thresholds: { low: 30, moderate: 60, high: 80, critical: 100 },
    assistant_prompt: "You are Himal AI, the official Nepal Travel Companion. Answer strictly using verified tourism dataset records.",
  })

  // Destination Overrides State
  const [destSearch, setDestSearch] = useState("")
  const [destResults, setDestSearchResults] = useState([])
  const [selectedDest, setSelectedDest] = useState(null)
  const [overrideStatus, setOverrideStatus] = useState("ALLOWED")
  const [overridePriority, setOverridePriority] = useState("NORMAL")
  const [overrideReason, setOverrideReason] = useState("")

  const loadAIConfig = async () => {
    try {
      const { data } = await adminApi.getCMS("settings", { key: "ai_engine_config" })
      if (data?.value) {
        setAiConfig((prev) => ({ ...prev, ...data.value }))
      }
    } catch {
      // Default initial config remains
    }
  }

  useEffect(() => {
    loadAIConfig()
  }, [])

  // Destination Search for AI Overrides
  useEffect(() => {
    if (!destSearch.trim() || destSearch.length < 2) {
      setDestSearchResults([])
      return
    }
    const timer = setTimeout(() => {
      destinationApi.getDestinations({ search: destSearch, page_size: 8 })
        .then(({ data }) => setDestSearchResults(data.results || data || []))
        .catch(() => setDestSearchResults([]))
    }, 250)
    return () => clearTimeout(timer)
  }, [destSearch])

  const handleSaveAIConfig = async () => {
    setBusy(true)
    try {
      await adminApi.updateCMS({
        resource: "settings",
        key: "ai_engine_config",
        value: aiConfig,
        description: "Central AI/ML Engine Configuration & Rules",
        is_public: true,
      })
      window.dispatchEvent(new Event("cms-updated"))
      showToast("Central AI Engine Configuration updated & published!", "success")
    } catch {
      showToast("Could not save AI configuration.", "error")
    } finally {
      setBusy(false)
    }
  }

  const handleSaveDestinationOverride = async () => {
    if (!selectedDest) return showToast("Select a destination first.", "error")
    try {
      await adminApi.updateAdminDestination(selectedDest.id, {
        ai_recommendation_status: overrideStatus,
        ai_priority_level: overridePriority,
        ai_override_reason: overrideReason,
      })
      showToast(`AI override saved for ${selectedDest.name} (${overrideStatus})`, "success")
      setSelectedDest(null)
      setDestSearch("")
    } catch {
      showToast("Could not save AI override.", "error")
    }
  }

  return (
    <div className="space-y-6 text-slate-100">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-950 p-6 rounded-3xl border border-slate-800 shadow-xl">
        <div>
          <span className="px-3 py-1 rounded-full bg-emerald-600/10 border border-[#1D5146]/30 text-purple-300 text-xs font-bold uppercase tracking-wider">
            Admin AI Control Center
          </span>
          <h2 className="text-2xl font-black text-white mt-1">Central AI/ML Engine Studio</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Configure recommendation weights, budget rules, risk thresholds, assistant prompts, and destination overrides.
          </p>
        </div>

        <button
          disabled={busy}
          onClick={handleSaveAIConfig}
          className="px-6 py-3 bg-amber-400 hover:bg-amber-500 text-slate-950 font-black text-xs rounded-2xl flex items-center gap-2 shadow-lg shadow-amber-400/20"
        >
          <FiSave size={16} /> {busy ? "Saving..." : "Publish AI Rules"}
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-3">
        {TABS.map(([id, label]) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === id ? "bg-[#102A2E] text-white shadow-lg shadow-purple-700/30" : "bg-slate-900 text-slate-400 hover:bg-slate-800"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Tab 1: General & Models */}
      {activeTab === "general" && (
        <div className="bg-slate-950 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-xl text-xs">
          <h3 className="text-lg font-black text-white">General AI Execution Settings</h3>
          <div className="grid sm:grid-cols-2 gap-4">
            <label className="font-bold text-slate-300 block">
              AI Engine Status
              <select
                value={aiConfig.ai_enabled ? "true" : "false"}
                onChange={(e) => setAiConfig({ ...aiConfig, ai_enabled: e.target.value === "true" })}
                className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white"
              >
                <option value="true">🟢 AI Enabled (Live Dataset & ML Pipeline Active)</option>
                <option value="false">🔴 AI Disabled (Strict Deterministic Ranking Fallback)</option>
              </select>
            </label>

            <label className="font-bold text-slate-300 block">
              ML Model Pipeline Provider
              <select
                value={aiConfig.model_provider}
                onChange={(e) => setAiConfig({ ...aiConfig, model_provider: e.target.value })}
                className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white"
              >
                <option value="fastapi_tf_idf_rf">FastAPI + TF-IDF Vectorizer + Random Forest Regressors</option>
                <option value="bundled_graphml_hybrid">Bundled GraphML NetworkX + DRF Engine</option>
              </select>
            </label>

            <label className="font-bold text-slate-300 block">
              Generation Temperature (Creativity)
              <input
                type="number"
                step="0.1"
                min="0.1"
                max="1.0"
                value={aiConfig.temperature}
                onChange={(e) => setAiConfig({ ...aiConfig, temperature: Number(e.target.value) })}
                className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white"
              />
            </label>

            <label className="font-bold text-slate-300 block">
              Maximum Output Tokens
              <input
                type="number"
                value={aiConfig.max_tokens}
                onChange={(e) => setAiConfig({ ...aiConfig, max_tokens: Number(e.target.value) })}
                className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white"
              />
            </label>
          </div>
        </div>
      )}

      {/* Tab 2: Recommendation Rules */}
      {activeTab === "recommendations" && (
        <div className="bg-slate-950 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-xl text-xs">
          <h3 className="text-lg font-black text-white">Recommendation Scoring Weights (%)</h3>
          <p className="text-slate-400">Adjust the relative influence of each feature on recommendation scores.</p>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(aiConfig.recommendation_weights || {}).map(([key, val]) => (
              <div key={key} className="p-3.5 rounded-2xl bg-slate-900 border border-slate-800 space-y-1">
                <div className="flex justify-between font-bold text-white capitalize">
                  <span>{key} Weight</span>
                  <span className="text-amber-400">{val}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="50"
                  value={val}
                  onChange={(e) => setAiConfig({
                    ...aiConfig,
                    recommendation_weights: { ...aiConfig.recommendation_weights, [key]: Number(e.target.value) }
                  })}
                  className="w-full accent-amber-400"
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Destination AI Overrides */}
      {activeTab === "overrides" && (
        <div className="bg-slate-950 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-xl text-xs">
          <div>
            <h3 className="text-lg font-black text-white">Destination AI Recommendation Overrides</h3>
            <p className="text-slate-400">Override AI recommendation engine behavior for specific destinations (e.g. Block closed places, promote seasonal highlights).</p>
          </div>

          <div className="space-y-3">
            <label className="font-bold text-amber-300 block">Search Destination to Override</label>
            {selectedDest ? (
              <div className="p-3 rounded-2xl bg-purple-950/40 border border-[#1D5146]/40 flex items-center justify-between">
                <div>
                  <p className="font-black text-sm text-white">{selectedDest.name}</p>
                  <p className="text-[11px] text-purple-200">📍 {selectedDest.city || selectedDest.district}, {selectedDest.province}</p>
                </div>
                <button type="button" onClick={() => setSelectedDest(null)} className="px-3 py-1 rounded-xl bg-slate-800 text-slate-300">Change</button>
              </div>
            ) : (
              <div className="relative">
                <input
                  type="text"
                  value={destSearch}
                  onChange={(e) => setDestSearch(e.target.value)}
                  placeholder="Search destination name (e.g., Everest, Annapurna, Phewa Lake)..."
                  className="w-full px-4 py-2.5 rounded-2xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-amber-400"
                />
                {destResults.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-1 rounded-2xl bg-slate-900 border border-slate-700 z-20 max-h-48 overflow-y-auto divide-y divide-slate-800">
                    {destResults.map((d) => (
                      <button
                        key={d.id}
                        type="button"
                        onClick={() => {
                          setSelectedDest(d)
                          setOverrideStatus(d.ai_recommendation_status || "ALLOWED")
                          setOverridePriority(d.ai_priority_level || "NORMAL")
                          setOverrideReason(d.ai_override_reason || "")
                          setDestSearchResults([])
                        }}
                        className="w-full text-left p-3 hover:bg-slate-800 flex justify-between items-center"
                      >
                        <span className="font-bold text-white">{d.name}</span>
                        <span className="text-[10px] text-slate-400">{d.city || d.district}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {selectedDest && (
              <div className="space-y-3 pt-2 border-t border-slate-800">
                <div className="grid sm:grid-cols-2 gap-3">
                  <label className="font-bold text-slate-300 block">AI Recommendation Status
                    <select
                      value={overrideStatus}
                      onChange={(e) => setOverrideStatus(e.target.value)}
                      className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white"
                    >
                      <option value="ALLOWED">🟢 ALLOWED (Normal Recommendation Pipeline)</option>
                      <option value="BLOCKED">🔴 BLOCKED (Prevent AI from Recommending)</option>
                      <option value="PRIORITY">⭐ PRIORITY (Boost in Top Results)</option>
                    </select>
                  </label>

                  <label className="font-bold text-slate-300 block">Priority Level
                    <select
                      value={overridePriority}
                      onChange={(e) => setOverridePriority(e.target.value)}
                      className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white"
                    >
                      <option value="LOW">Low</option>
                      <option value="NORMAL">Normal</option>
                      <option value="HIGH">High</option>
                      <option value="CRITICAL">Critical / Must Feature</option>
                    </select>
                  </label>
                </div>

                <label className="font-bold text-slate-300 block">Admin Override Reason / Audit Note
                  <textarea
                    rows="2"
                    value={overrideReason}
                    onChange={(e) => setOverrideReason(e.target.value)}
                    placeholder="e.g. Temporarily blocked due to trail maintenance / Featured seasonal festival..."
                    className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white"
                  />
                </label>

                <button
                  type="button"
                  onClick={handleSaveDestinationOverride}
                  className="px-5 py-2.5 rounded-2xl bg-amber-400 hover:bg-amber-500 text-slate-950 font-bold"
                >
                  Save Destination AI Override
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 4 & 5: Assistant Instructions & Risk Thresholds */}
      {activeTab === "assistant" && (
        <div className="bg-slate-950 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-xl text-xs">
          <h3 className="text-lg font-black text-white">Himal AI System Instructions & Safety Rules</h3>
          <label className="font-bold text-slate-300 block">System Prompt
            <textarea
              rows="5"
              value={aiConfig.assistant_prompt}
              onChange={(e) => setAiConfig({ ...aiConfig, assistant_prompt: e.target.value })}
              className="w-full mt-1 px-4 py-3 rounded-2xl bg-slate-900 border border-slate-700 text-white leading-relaxed font-mono"
            />
          </label>
        </div>
      )}
    </div>
  )
}
