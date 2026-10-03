import { useCallback, useEffect, useState } from "react"
import {
  FiSave, FiSend, FiEye, FiCheck, FiRefreshCw, FiPlus, FiTrash2,
  FiPhone, FiAlertCircle, FiCompass, FiShield, FiMessageSquare,
  FiLayout, FiLayers, FiCheckCircle
} from "react-icons/fi"
import adminApi from "../../../api/adminApi"
import { notifyCmsUpdated } from "../../../hooks/usePublicConfig"
import useToast from "../../../hooks/useToast"

export default function CmsGlobalSectionEditor({ sectionId, initialSettings = {} }) {
  const { showToast } = useToast()
  const [loading, setLoading] = useState(false)
  const [busy, setBusy] = useState(false)
  const [data, setData] = useState({})
  const [status, setStatus] = useState("published")
  const [newTickerItem, setNewTickerItem] = useState("")
  const [newPromptItem, setNewPromptItem] = useState("")

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const res = await adminApi.getCMS("settings")
      const rows = res.data?.results || []
      const match = rows.find(r => r.key === sectionId || r.key === `global_${sectionId}`)
      if (match && match.value) {
        setData(match.value)
        setStatus(match.value.status || "published")
      } else if (initialSettings[sectionId]) {
        setData(initialSettings[sectionId])
        setStatus(initialSettings[sectionId].status || "published")
      }
    } catch {
      if (initialSettings[sectionId]) {
        setData(initialSettings[sectionId])
      }
    } finally {
      setLoading(false)
    }
  }, [sectionId, initialSettings])

  useEffect(() => {
    loadData()
  }, [loadData])

  const saveRecord = async (targetStatus) => {
    setBusy(true)
    const payloadValue = {
      ...data,
      status: targetStatus,
      updated_at: new Date().toISOString(),
      ...(targetStatus === "published" ? { published_at: new Date().toISOString() } : {})
    }

    try {
      // Find row id or update by key
      await adminApi.updateCMS({
        resource: "settings",
        key: sectionId,
        value: payloadValue,
        description: `CMS Managed ${sectionId} configuration`,
        is_public: true,
      })

      setStatus(targetStatus)
      setData(payloadValue)

      if (targetStatus === "published") {
        notifyCmsUpdated()
        showToast(`Published ${sectionId.replace('_', ' ')} live to the website!`, "success")
      } else {
        showToast(`Saved ${sectionId.replace('_', ' ')} as draft in database.`, "info")
      }
    } catch (err) {
      showToast(err.response?.data?.detail || "Could not save section configuration", "error")
    } finally {
      setBusy(false)
    }
  }

  const updateField = (field, val) => {
    setData(prev => ({ ...prev, [field]: val }))
  }

  const addTickerItem = () => {
    if (!newTickerItem.trim()) return
    const current = Array.isArray(data.items) ? data.items : []
    setData({ ...data, items: [...current, newTickerItem.trim()] })
    setNewTickerItem("")
  }

  const removeTickerItem = (index) => {
    const current = Array.isArray(data.items) ? data.items : []
    setData({ ...data, items: current.filter((_, i) => i !== index) })
  }

  const addPromptItem = () => {
    if (!newPromptItem.trim()) return
    const current = Array.isArray(data.quick_prompts) ? data.quick_prompts : []
    setData({ ...data, quick_prompts: [...current, newPromptItem.trim()] })
    setNewPromptItem("")
  }

  const removePromptItem = (index) => {
    const current = Array.isArray(data.quick_prompts) ? data.quick_prompts : []
    setData({ ...data, quick_prompts: current.filter((_, i) => i !== index) })
  }

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center text-slate-400">
        <FiRefreshCw className="animate-spin mr-2" /> Loading section settings…
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-[#0E1E1B] p-5 rounded-2xl border border-slate-200 dark:border-emerald-900/50 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-black capitalize text-slate-900 dark:text-white">
              {sectionId.replace('_', ' ')} Section
            </h2>
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                status === "published"
                  ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300/40"
                  : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border border-amber-300/40"
              }`}
            >
              {status === "published" ? "● Live on Website" : "Draft (Not Live)"}
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Configure appearance and content. Publishing immediately pushes changes to public website visitors.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            disabled={busy}
            onClick={() => saveRecord("draft")}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 transition"
          >
            <FiSave size={13} />
            <span>Save Draft</span>
          </button>

          <button
            type="button"
            disabled={busy}
            onClick={() => saveRecord("published")}
            className="inline-flex items-center gap-1.5 px-5 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-900/30 transition hover:scale-[1.02]"
          >
            <FiSend size={13} />
            <span>Publish to Website</span>
          </button>
        </div>
      </div>

      {/* Editor Body */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* Left: Input Form Controls (7 cols) */}
        <div className="lg:col-span-7 bg-white dark:bg-[#0E1E1B] p-6 rounded-2xl border border-slate-200 dark:border-emerald-900/50 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <span className="text-sm font-bold text-slate-800 dark:text-slate-200">Settings & Content</span>
            <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-slate-600 dark:text-slate-300">
              <input
                type="checkbox"
                checked={data.enabled !== false}
                onChange={(e) => updateField("enabled", e.target.checked)}
                className="rounded text-emerald-600 focus:ring-emerald-500"
              />
              <span>Enable on Public Site</span>
            </label>
          </div>

          {/* TOPBAR FORM */}
          {sectionId === "topbar" && (
            <div className="space-y-3.5 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  24/7 Emergency Helpline Number
                </label>
                <input
                  value={data.helpline || ""}
                  onChange={(e) => updateField("helpline", e.target.value)}
                  placeholder="1144 / +977-1-4247041"
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Helpline Label
                </label>
                <input
                  value={data.emergency_label || ""}
                  onChange={(e) => updateField("emergency_label", e.target.value)}
                  placeholder="24/7 Tourist Police Hotline"
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Seasonal Headline Notice
                </label>
                <input
                  value={data.notice || ""}
                  onChange={(e) => updateField("notice", e.target.value)}
                  placeholder="Autumn 2026 Trekking Season Open · Favorable weather across Annapurna & Everest circuits"
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Live Weather Summary Ticker
                </label>
                <input
                  value={data.weather_summary || ""}
                  onChange={(e) => updateField("weather_summary", e.target.value)}
                  placeholder="Kathmandu 21°C · Pokhara 23°C · Namche 9°C"
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Apply Button Label
                  </label>
                  <input
                    value={data.apply_button_label || ""}
                    onChange={(e) => updateField("apply_button_label", e.target.value)}
                    placeholder="Apply / Inquire"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Emergency Hub URL
                  </label>
                  <input
                    value={data.emergency_url || ""}
                    onChange={(e) => updateField("emergency_url", e.target.value)}
                    placeholder="/emergency"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  />
                </div>
              </div>
            </div>
          )}

          {/* NAVBAR FORM */}
          {sectionId === "navbar" && (
            <div className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Logo Brand Text
                  </label>
                  <input
                    value={data.logo_text || ""}
                    onChange={(e) => updateField("logo_text", e.target.value)}
                    placeholder="Nepal Yatra"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Logo Tagline
                  </label>
                  <input
                    value={data.logo_tagline || ""}
                    onChange={(e) => updateField("logo_tagline", e.target.value)}
                    placeholder="Discover the Himalayas"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Header CTA Button Label
                  </label>
                  <input
                    value={data.cta_label || ""}
                    onChange={(e) => updateField("cta_label", e.target.value)}
                    placeholder="Apply / Inquire"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    CTA Action
                  </label>
                  <select
                    value={data.cta_action || "open_modal"}
                    onChange={(e) => updateField("cta_action", e.target.value)}
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  >
                    <option value="open_modal">Open Admission / Inquiry Modal</option>
                    <option value="link">Navigate to URL</option>
                  </select>
                </div>
              </div>

              <div className="flex flex-wrap gap-4 pt-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={data.show_search !== false}
                    onChange={(e) => updateField("show_search", e.target.checked)}
                    className="rounded text-emerald-600"
                  />
                  <span>Show Smart Search Bar</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={data.show_theme_toggle !== false}
                    onChange={(e) => updateField("show_theme_toggle", e.target.checked)}
                    className="rounded text-emerald-600"
                  />
                  <span>Show Dark/Light Toggle</span>
                </label>
              </div>
            </div>
          )}

          {/* FOOTER FORM */}
          {sectionId === "footer" && (
            <div className="space-y-3.5 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Brand Name & Headline
                </label>
                <input
                  value={data.brand_name || ""}
                  onChange={(e) => updateField("brand_name", e.target.value)}
                  placeholder="Nepal Yatra"
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Footer Brand Description
                </label>
                <textarea
                  rows={2}
                  value={data.brand_description || ""}
                  onChange={(e) => updateField("brand_description", e.target.value)}
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white resize-none"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Helpline Contact Notice
                </label>
                <input
                  value={data.helpline_text || ""}
                  onChange={(e) => updateField("helpline_text", e.target.value)}
                  placeholder="Emergency Dispatch: 1144 (Tourist Police) · 100 (Police)"
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Copyright Notice
                </label>
                <input
                  value={data.copyright || ""}
                  onChange={(e) => updateField("copyright", e.target.value)}
                  placeholder="© 2026 Nepal Yatra Tourism Board. Government of Nepal. All rights reserved."
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                />
              </div>

              <div className="pt-2">
                <label className="flex items-center gap-2 cursor-pointer font-semibold">
                  <input
                    type="checkbox"
                    checked={data.show_newsletter !== false}
                    onChange={(e) => updateField("show_newsletter", e.target.checked)}
                    className="rounded text-emerald-600"
                  />
                  <span>Show Newsletter Subscription Form</span>
                </label>
              </div>
            </div>
          )}

          {/* CTA BANNERS FORM */}
          {sectionId === "cta_banners" && (
            <div className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Badge Label
                  </label>
                  <input
                    value={data.badge || ""}
                    onChange={(e) => updateField("badge", e.target.value)}
                    placeholder="Autumn 2026 Season"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Theme Gradient
                  </label>
                  <select
                    value={data.theme || "emerald"}
                    onChange={(e) => updateField("theme", e.target.value)}
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  >
                    <option value="emerald">Himalayan Emerald</option>
                    <option value="navy">Midnight Navy</option>
                    <option value="sunset">Himalayan Sunset</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Banner Headline
                </label>
                <input
                  value={data.title || ""}
                  onChange={(e) => updateField("title", e.target.value)}
                  placeholder="Experience Nepal Beyond the Beaten Path"
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Banner Subtitle / Description
                </label>
                <textarea
                  rows={2}
                  value={data.subtitle || ""}
                  onChange={(e) => updateField("subtitle", e.target.value)}
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Primary Button Text
                  </label>
                  <input
                    value={data.button_text || ""}
                    onChange={(e) => updateField("button_text", e.target.value)}
                    placeholder="Plan Your Expedition"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Primary Button URL
                  </label>
                  <input
                    value={data.button_url || ""}
                    onChange={(e) => updateField("button_url", e.target.value)}
                    placeholder="/itinerary"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  />
                </div>
              </div>
            </div>
          )}

          {/* APPLY NOW BUTTONS FORM */}
          {sectionId === "action_buttons" && (
            <div className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Primary Button Text
                  </label>
                  <input
                    value={data.primary_label || ""}
                    onChange={(e) => updateField("primary_label", e.target.value)}
                    placeholder="Apply / Inquire Now"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Primary Button Action
                  </label>
                  <select
                    value={data.primary_action || "open_modal"}
                    onChange={(e) => updateField("primary_action", e.target.value)}
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  >
                    <option value="open_modal">Open Admission / Inquiry Modal</option>
                    <option value="link">Navigate to URL</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Secondary Action Label
                </label>
                <input
                  value={data.secondary_label || ""}
                  onChange={(e) => updateField("secondary_label", e.target.value)}
                  placeholder="Find Verified Guides"
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                />
              </div>

              <div className="pt-2">
                <label className="flex items-center gap-2 cursor-pointer font-semibold">
                  <input
                    type="checkbox"
                    checked={data.floating_sos !== false}
                    onChange={(e) => updateField("floating_sos", e.target.checked)}
                    className="rounded text-rose-600"
                  />
                  <span>Show Floating 24/7 SOS Direct Hotline Button</span>
                </label>
              </div>
            </div>
          )}

          {/* TICKERS FORM */}
          {sectionId === "tickers" && (
            <div className="space-y-3.5 text-xs">
              <div className="flex items-center justify-between">
                <label className="font-semibold text-slate-700 dark:text-slate-300">
                  Marquee Items ({data.items?.length || 0})
                </label>
                <select
                  value={data.speed || "normal"}
                  onChange={(e) => updateField("speed", e.target.value)}
                  className="rounded border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-2 py-1 text-xs"
                >
                  <option value="slow">Slow Speed</option>
                  <option value="normal">Normal Speed</option>
                  <option value="fast">Fast Speed</option>
                </select>
              </div>

              <div className="flex gap-2">
                <input
                  value={newTickerItem}
                  onChange={(e) => setNewTickerItem(e.target.value)}
                  placeholder="Add breaking notice or weather alert..."
                  className="flex-1 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                />
                <button
                  type="button"
                  onClick={addTickerItem}
                  className="rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-2 font-bold flex items-center gap-1"
                >
                  <FiPlus size={14} /> Add
                </button>
              </div>

              <div className="space-y-1.5 max-h-56 overflow-y-auto">
                {Array.isArray(data.items) && data.items.map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                    <span className="truncate pr-2 text-slate-700 dark:text-slate-300">{item}</span>
                    <button
                      type="button"
                      onClick={() => removeTickerItem(idx)}
                      className="text-rose-500 hover:text-rose-700 p-1"
                    >
                      <FiTrash2 size={13} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* CHAT WIDGET FORM */}
          {sectionId === "chat_widget" && (
            <div className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Assistant Title
                  </label>
                  <input
                    value={data.title || ""}
                    onChange={(e) => updateField("title", e.target.value)}
                    placeholder="Himal AI Assistant"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Subtitle
                  </label>
                  <input
                    value={data.subtitle || ""}
                    onChange={(e) => updateField("subtitle", e.target.value)}
                    placeholder="Your Nepal Travel Companion"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Greeting Message
                </label>
                <textarea
                  rows={3}
                  value={data.greeting || ""}
                  onChange={(e) => updateField("greeting", e.target.value)}
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white resize-none"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Suggested Quick Questions
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    value={newPromptItem}
                    onChange={(e) => setNewPromptItem(e.target.value)}
                    placeholder="e.g. Best treks in October?"
                    className="flex-1 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  />
                  <button
                    type="button"
                    onClick={addPromptItem}
                    className="rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-2 font-bold flex items-center gap-1"
                  >
                    <FiPlus size={14} /> Add
                  </button>
                </div>

                <div className="flex flex-wrap gap-1.5">
                  {Array.isArray(data.quick_prompts) && data.quick_prompts.map((q, idx) => (
                    <span key={idx} className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 dark:bg-emerald-950 border border-emerald-200 dark:border-emerald-800 px-2.5 py-1 text-[11px] text-emerald-800 dark:text-emerald-300">
                      <span>{q}</span>
                      <button type="button" onClick={() => removePromptItem(idx)} className="text-rose-500 hover:text-rose-700">
                        <FiTrash2 size={11} />
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ADMISSION MODAL FORM */}
          {sectionId === "admission_modal" && (
            <div className="space-y-3.5 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Modal Title
                </label>
                <input
                  value={data.title || ""}
                  onChange={(e) => updateField("title", e.target.value)}
                  placeholder="Nepal Journey Inquiry & Booking Request"
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Subtitle / Instructions
                </label>
                <textarea
                  rows={2}
                  value={data.subtitle || ""}
                  onChange={(e) => updateField("subtitle", e.target.value)}
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white resize-none"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Submit Button Label
                </label>
                <input
                  value={data.button_label || ""}
                  onChange={(e) => updateField("button_label", e.target.value)}
                  placeholder="Submit Travel Inquiry"
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Confirmation Message
                </label>
                <textarea
                  rows={2}
                  value={data.success_message || ""}
                  onChange={(e) => updateField("success_message", e.target.value)}
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white resize-none"
                />
              </div>
            </div>
          )}

        </div>

        {/* Right: Live Interactive Mockup Preview (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
              <FiEye size={13} />
              <span>Live Public Preview</span>
            </span>
            <span className="text-[10px] text-slate-400">Renders as shown to travellers</span>
          </div>

          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-900 p-4 shadow-inner text-white overflow-hidden">
            {sectionId === "topbar" && (
              <div className="rounded-lg bg-[#06241e] border border-emerald-900/60 p-2.5 text-[11px] space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5 text-emerald-300 font-bold">
                    <FiPhone size={12} className="text-emerald-400" />
                    <span>{data.helpline || "1144"}</span>
                  </div>
                  <span className="text-emerald-200 truncate max-w-[160px] text-[10px]">
                    {data.notice || "Autumn 2026 Season"}
                  </span>
                  <span className="bg-emerald-600 text-white px-2 py-0.5 rounded text-[10px] font-bold">
                    {data.apply_button_label || "Apply"}
                  </span>
                </div>
              </div>
            )}

            {sectionId === "navbar" && (
              <div className="rounded-lg bg-[#063B32] border border-white/20 p-3 flex items-center justify-between">
                <div>
                  <span className="font-bold text-sm text-white">{data.logo_text || "Nepal Yatra"}</span>
                  <span className="block text-[10px] text-emerald-300">{data.logo_tagline || "Discover"}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="rounded bg-white/10 px-2 py-1 text-[10px] text-emerald-200">Destinations</span>
                  <button type="button" className="rounded-lg bg-emerald-500 text-slate-950 font-bold px-2.5 py-1 text-[11px]">
                    {data.cta_label || "Apply / Inquire"}
                  </button>
                </div>
              </div>
            )}

            {sectionId === "footer" && (
              <div className="rounded-lg bg-[#041d18] border border-emerald-900/60 p-4 space-y-3 text-xs">
                <div>
                  <span className="font-bold text-white text-sm">{data.brand_name || "Nepal Yatra"}</span>
                  <p className="text-emerald-200/80 text-[11px] mt-1 line-clamp-2">{data.brand_description}</p>
                </div>
                <div className="border-t border-emerald-950 pt-2 flex items-center justify-between text-[10px] text-emerald-300/70">
                  <span>{data.copyright || "© 2026 Nepal Yatra"}</span>
                  <span className="text-emerald-400 font-mono">1144 24/7 Helpline</span>
                </div>
              </div>
            )}

            {sectionId === "cta_banners" && (
              <div className="rounded-xl bg-gradient-to-r from-emerald-950 via-emerald-900 to-[#041d18] border border-emerald-700/40 p-4 space-y-2">
                <span className="inline-block px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-bold">
                  {data.badge || "Featured"}
                </span>
                <h4 className="font-bold text-white text-sm">{data.title || "Adventure Awaits"}</h4>
                <p className="text-[11px] text-emerald-200/80 line-clamp-2">{data.subtitle}</p>
                <button type="button" className="mt-2 rounded-lg bg-emerald-500 text-slate-950 font-bold px-3 py-1.5 text-xs">
                  {data.button_text || "Plan My Trip"}
                </button>
              </div>
            )}

            {sectionId === "action_buttons" && (
              <div className="p-4 bg-slate-950/80 rounded-xl flex items-center gap-2">
                <button type="button" className="rounded-full bg-emerald-600 text-white font-bold px-4 py-2 text-xs shadow-lg">
                  {data.primary_label || "Apply / Inquire Now"}
                </button>
                {data.floating_sos && (
                  <button type="button" className="rounded-full bg-rose-600 text-white font-bold px-3 py-2 text-xs">
                    1144 SOS
                  </button>
                )}
              </div>
            )}

            {sectionId === "tickers" && (
              <div className="rounded-lg bg-[#041d18] border border-emerald-900 p-2 text-xs overflow-hidden">
                <div className="flex items-center gap-2 text-emerald-300 text-[11px] truncate">
                  <span className="bg-emerald-800 text-white px-1.5 py-0.5 rounded text-[10px] font-bold">LIVE</span>
                  <span className="truncate">{data.items?.[0] || "Live Route Status"}</span>
                </div>
              </div>
            )}

            {sectionId === "chat_widget" && (
              <div className="rounded-xl bg-white text-slate-800 p-3 shadow-xl space-y-2 max-w-xs mx-auto">
                <div className="bg-[#0B3D91] text-white p-2.5 rounded-lg flex items-center justify-between">
                  <div>
                    <span className="font-bold text-xs">{data.title || "Himal AI Assistant"}</span>
                    <span className="block text-[10px] text-blue-200">{data.subtitle}</span>
                  </div>
                </div>
                <div className="p-2 bg-slate-100 rounded text-[11px] text-slate-700">
                  {data.greeting || "Namaste!"}
                </div>
                <div className="flex flex-wrap gap-1">
                  {Array.isArray(data.quick_prompts) && data.quick_prompts.slice(0, 2).map((q, i) => (
                    <span key={i} className="bg-blue-50 text-blue-800 text-[10px] px-2 py-0.5 rounded-full border border-blue-200">
                      {q}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {sectionId === "admission_modal" && (
              <div className="rounded-xl bg-white text-slate-800 p-4 shadow-xl space-y-3 max-w-xs mx-auto">
                <h4 className="font-bold text-sm text-slate-900">{data.title || "Trip Request"}</h4>
                <p className="text-[11px] text-slate-500">{data.subtitle}</p>
                <div className="space-y-1.5">
                  <div className="h-6 rounded bg-slate-100 border border-slate-200 text-[10px] px-2 flex items-center text-slate-400">Full Name</div>
                  <div className="h-6 rounded bg-slate-100 border border-slate-200 text-[10px] px-2 flex items-center text-slate-400">Email Address</div>
                  <div className="h-6 rounded bg-slate-100 border border-slate-200 text-[10px] px-2 flex items-center text-slate-400">Destination</div>
                </div>
                <button type="button" className="w-full rounded-lg bg-emerald-600 text-white font-bold py-1.5 text-xs">
                  {data.button_label || "Submit"}
                </button>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  )
}
