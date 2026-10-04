import { useEffect, useState } from "react"
import { notifyCmsUpdated } from "../../hooks/usePublicConfig"
import { FiImage, FiSave, FiTrash2, FiUpload, FiGlobe, FiLayout, FiLayers, FiLink2, FiType, FiMaximize, FiGrid, FiPlus, FiX, FiCheckCircle } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"
import TourismLogo, { NepalYatraSymbol } from "../branding/TourismLogo"

const textFields = [
  ["site_title", "Portal Heading / Site Name *"],
  ["tagline", "Tagline / Subtitle"],
  ["footer_text", "Footer Copyright & Summary"],
  ["contact_address", "Official Support Address / City"],
  ["contact_email", "Official Contact Email"],
  ["contact_phone", "Official Support Phone"],
]

const socialFields = [
  ["facebook_url", "Facebook Page URL"],
  ["instagram_url", "Instagram Profile URL"],
  ["twitter_url", "X / Twitter URL"],
  ["youtube_url", "YouTube Channel URL"],
]

// Every layout option is an allowlisted choice — the admin designs
// the site structure, the code just renders the chosen variant.
const CHOICE_GROUPS = [
  {
    group: "Header & Navigation",
    icon: FiLayout,
    fields: [
      ["header_style", "Header Behaviour", [
        ["sticky", "Sticky — follows the scroll"],
        ["static", "Static — scrolls away"],
        ["floating", "Floating — rounded, margin"],
      ]],
      ["header_layout", "Header Layout", [
        ["spread", "Spread — links across the bar"],
        ["centered", "Centered"],
        ["compact", "Compact — tight spacing"],
      ]],
      ["nav_style", "Menu Item Style", [
        ["default", "Default"],
        ["tabs", "Tabs"],
        ["pills", "Pills"],
      ]],
    ],
  },
  {
    group: "Page Structure",
    icon: FiLayers,
    fields: [
      ["sidebar_position", "Sidebar Position", [
        ["left", "Left side"],
        ["right", "Right side"],
        ["hidden", "Hidden (full-width content)"],
      ]],
      ["page_width", "Content Width", [
        ["fluid", "Fluid — full width"],
        ["boxed", "Boxed — max width centered"],
      ]],
      ["card_style", "Card Appearance", [
        ["elevated", "Elevated — soft shadow"],
        ["outlined", "Outlined — border only"],
        ["flat", "Flat — minimal"],
      ]],
    ],
  },
  {
    group: "Typography & Density",
    icon: FiType,
    fields: [
      ["font_scale", "Text Size", [
        ["compact", "Compact — denser text"],
        ["normal", "Normal"],
        ["large", "Large — easier reading"],
      ]],
      ["footer_columns", "Footer Columns", [
        ["2", "2 Columns"],
        ["3", "3 Columns"],
        ["4", "4 Columns"],
      ]],
    ],
  },
]

const TOGGLES = [
  ["show_breadcrumbs", "Breadcrumbs on inner pages"],
  ["show_hero", "Hero banner on destination pages"],
  ["show_announcement_bar", "Announcement bar at the very top"],
  ["show_social_footer", "Social icons in the footer"],
]

const TABS = [
  ["identity", "Identity & Content", FiGlobe],
  ["structure", "Structure & Layout", FiLayout],
  ["organization", "Organization & Links", FiLink2],
]

export default function BrandingPanel() {
  const { showToast } = useToast()
  const [tab, setTab] = useState("identity")
  const [branding, setBranding] = useState({
    site_title: "Nepal Yatra",
    tagline: "Himalayan Journeys & Travel Planning",
    theme_preset: "himalayan",
    primary_color: "#C8102E",
    secondary_color: "#0B3D91",
    header_style: "sticky",
    header_layout: "spread",
    nav_style: "default",
    sidebar_position: "left",
    page_width: "fluid",
    card_style: "elevated",
    font_scale: "normal",
    footer_columns: "3",
    show_breadcrumbs: true,
    show_hero: true,
    show_announcement_bar: false,
    show_social_footer: true,
    announcement_bar_text: "",
    footer_heading: "",
    quick_links: [],
    footer_sections: [],
  })
  const [assets, setAssets] = useState({})
  const [_presets, setPresets] = useState({})
  const [busy, setBusy] = useState(false)
  const [newLink, setNewLink] = useState({ label: "", url: "" })
  const [newSection, setNewSection] = useState({ heading: "", content: "" })

  const load = async () => {
    try {
      const { data } = await adminApi.getBranding()
      setBranding((_prev) => ({
        site_title: "Nepal Yatra",
        tagline: "Himalayan Journeys & Travel Planning",
        header_style: "sticky",
        header_layout: "spread",
        nav_style: "default",
        sidebar_position: "left",
        page_width: "fluid",
        card_style: "elevated",
        font_scale: "normal",
        footer_columns: "3",
        show_breadcrumbs: true,
        show_hero: true,
        show_announcement_bar: false,
        show_social_footer: true,
        ...data.branding,
      }))
      setAssets(data.assets || {})
      setPresets(data.presets || {})
    } catch (error) {
      showToast("Branding settings loaded with defaults.", "info")
    }
  }

  useEffect(() => {
    // Deferred one tick so the loader's synchronous setLoading(true) runs
    // outside the effect flush (react-hooks/set-state-in-effect).
    const t = setTimeout(() => load(), 0)
    return () => clearTimeout(t)
  }, [])

  const save = async () => {
    setBusy(true)
    try {
      const allowed = {
        ...[...textFields, ...socialFields].reduce(
          (value, [key]) => ({ ...value, [key]: branding[key] || "" }),
          {}
        ),
        theme_preset: branding.theme_preset || "himalayan",
        site_title: branding.site_title || "Nepal Yatra",
        tagline: branding.tagline || "Himalayan Journeys & Travel Planning",
        primary_color: branding.primary_color || "#C8102E",
        secondary_color: branding.secondary_color || "#0B3D91",
      }
      // Structural choices
      CHOICE_GROUPS.forEach(({ fields }) => {
        fields.forEach(([key]) => {
          if (branding[key]) allowed[key] = branding[key]
        })
      })
      // Toggles
      TOGGLES.forEach(([key]) => {
        allowed[key] = Boolean(branding[key])
      })
      // Structural text
      allowed.announcement_bar_text = (branding.announcement_bar_text || "").slice(0, 300)
      allowed.footer_heading = (branding.footer_heading || "").slice(0, 300)
      // Organized collections
      allowed.quick_links = Array.isArray(branding.quick_links) ? branding.quick_links : []
      allowed.footer_sections = Array.isArray(branding.footer_sections) ? branding.footer_sections : []

      const { data } = await adminApi.updateBranding(allowed)
      setBranding((prev) => ({ ...prev, ...data.branding }))

      // Notify all public config listeners to update logo and headers globally across the platform
      notifyCmsUpdated()
      showToast("Branding, structure & organization published globally!", "success")
    } catch (error) {
      showToast(error.response?.data?.detail || "Branding save failed", "error")
    } finally {
      setBusy(false)
    }
  }

  const upload = async (kind, file) => {
    if (!file) return
    const body = new FormData()
    body.append("kind", kind)
    body.append("file", file)
    body.append("alt_text", kind === "logo" ? branding.site_title || "Nepal Yatra logo" : "Website icon")
    try {
      await adminApi.uploadBrandingAsset(body)
      notifyCmsUpdated()
      showToast(`${kind.toUpperCase()} asset uploaded successfully!`, "success")
      load()
    } catch (error) {
      showToast(error.response?.data?.detail || "Asset upload failed", "error")
    }
  }

  const remove = async (kind) => {
    if (!window.confirm(`Remove the current ${kind}? The system will fall back to the vector emblem.`)) return
    try {
      await adminApi.deleteBrandingAsset(kind)
      notifyCmsUpdated()
      showToast(`${kind} removed. Reverted to default vector logo.`, "info")
      load()
    } catch (error) {
      showToast("Asset removal failed", "error")
    }
  }

  // --- Organization helpers -------------------------------------------------
  const addQuickLink = () => {
    const label = newLink.label.trim()
    const url = newLink.url.trim()
    if (!label || !url) {
      showToast("Both a label and a URL are required.", "error")
      return
    }
    setBranding({
      ...branding,
      quick_links: [...(branding.quick_links || []), { label, url }],
    })
    setNewLink({ label: "", url: "" })
  }

  const removeQuickLink = (index) => {
    setBranding({
      ...branding,
      quick_links: (branding.quick_links || []).filter((_, i) => i !== index),
    })
  }

  const addFooterSection = () => {
    const heading = newSection.heading.trim()
    const content = newSection.content.trim()
    if (!heading || !content) {
      showToast("Both a heading and content are required.", "error")
      return
    }
    setBranding({
      ...branding,
      footer_sections: [...(branding.footer_sections || []), { heading, content }],
    })
    setNewSection({ heading: "", content: "" })
  }

  const removeFooterSection = (index) => {
    setBranding({
      ...branding,
      footer_sections: (branding.footer_sections || []).filter((_, i) => i !== index),
    })
  }

  const choiceLabel = (group, fieldKey, value) => {
    const g = CHOICE_GROUPS.find((grp) => grp.fields.some(([k]) => k === fieldKey))
    const f = g?.fields.find(([k]) => k === fieldKey)
    const opt = f?.[2].find(([v]) => v === value)
    return opt ? opt[1] : value
  }

  return (
    <div className="space-y-6 text-slate-100">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-950 p-6 rounded-3xl border border-slate-800 shadow-xl">
        <div>
          <span className="px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-bold uppercase tracking-wider">
            Admin Settings Desk
          </span>
          <h2 className="text-2xl font-black text-white mt-1">Portal Settings, Structure & Organization</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Update the brand name, theme, page structure (header, footer, layout) and site organization (quick links, footer sections). No code needed — everything publishes live.
          </p>
        </div>

        <button
          disabled={busy}
          onClick={save}
          className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-2xl font-black text-xs flex items-center gap-2 shadow-lg shadow-emerald-600/20 transition-all whitespace-nowrap"
        >
          <FiSave size={16} /> {busy ? "Publishing..." : "Publish All Settings"}
        </button>
      </div>

      {/* Section Tabs */}
      <div className="flex flex-wrap gap-2">
        {TABS.map(([key, label, Icon]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-4 py-2.5 rounded-2xl font-black text-xs flex items-center gap-2 transition-all border ${
              tab === key
                ? "bg-amber-500 text-slate-950 border-amber-400 shadow-lg shadow-amber-500/20"
                : "bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700"
            }`}
          >
            <Icon size={15} /> {label}
          </button>
        ))}
      </div>

      {/* Live Brand Preview — mirrors the published traveller header using
          the draft values below, so admins see exactly what will ship. */}
      <div className="p-6 rounded-3xl bg-white border border-[#E5E0D5] space-y-3 shadow-xl">
        <span className="text-xs font-black uppercase text-[#697675] block tracking-wider">
          Live Preview — {choiceLabel(null, "header_style", branding.header_style)} header · {choiceLabel(null, "card_style", branding.card_style)} cards · {choiceLabel(null, "page_width", branding.page_width)} layout
        </span>
        <div
          className="p-5 rounded-2xl border border-[#E5E0D5] flex flex-wrap items-center justify-between gap-4"
          style={{ background: "var(--brand-surface, #ffffff)" }}
        >
          <div className="flex items-center gap-3 min-w-0">
            <TourismLogo size="md" />
            <div className="min-w-0">
              <p className="font-black text-lg leading-tight truncate" style={{ color: branding.secondary_color || "#0B3D91" }}>
                {branding.site_title || "Nepal Yatra"}
              </p>
              <p className="text-xs text-[#697675] truncate">{branding.tagline || "Himalayan Journeys & Travel Planning"}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1.5 rounded-xl text-white font-black text-xs" style={{ background: branding.primary_color || "#C8102E" }}>
              Request booking
            </span>
            <span className="px-3 py-1.5 rounded-xl border font-black text-xs" style={{ color: branding.secondary_color || "#0B3D91", borderColor: branding.secondary_color || "#0B3D91" }}>
              Explore
            </span>
          </div>
        </div>
        {branding.show_announcement_bar && branding.announcement_bar_text && (
          <div className="px-4 py-2 rounded-xl text-xs font-bold text-white text-center" style={{ background: branding.primary_color || "#C8102E" }}>
            {branding.announcement_bar_text}
          </div>
        )}
        <p className="text-[11px] text-[#697675]">
          Preview updates as you type and uses the same brand tokens (<code>--brand-primary</code>/<code>--brand-secondary</code>) the live site reads after you publish.
        </p>
      </div>

      {/* ===================== TAB: IDENTITY & CONTENT ===================== */}
      {tab === "identity" && (
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Portal Name & Identity Fields */}
          <section className="bg-slate-950 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-xl">
            <h3 className="font-black text-lg text-white flex items-center gap-2">
              <FiGlobe className="text-amber-400" /> Portal Heading & Contact Information
            </h3>
            <div className="grid sm:grid-cols-2 gap-3 text-xs">
              {textFields.map(([key, label]) => (
                <label key={key} className={`block font-bold text-slate-300 ${key === "footer_text" ? "sm:col-span-2" : ""}`}>
                  {label}
                  {key === "footer_text" ? (
                    <textarea
                      rows="3"
                      className="input-field mt-1 text-slate-100 bg-slate-900 border-slate-700"
                      value={branding[key] || ""}
                      onChange={(e) => setBranding({ ...branding, [key]: e.target.value })}
                    />
                  ) : (
                    <input
                      type="text"
                      className="input-field mt-1 text-slate-100 bg-slate-900 border-slate-700"
                      value={branding[key] || ""}
                      onChange={(e) => setBranding({ ...branding, [key]: e.target.value })}
                    />
                  )}
                </label>
              ))}
            </div>

            <h4 className="font-bold text-sm text-amber-300 pt-2 border-t border-slate-800">Official Social Media Links</h4>
            <div className="grid sm:grid-cols-2 gap-3 text-xs">
              {socialFields.map(([key, label]) => (
                <label key={key} className="block font-bold text-slate-300">
                  {label}
                  <input
                    type="url"
                    placeholder="https://"
                    className="input-field mt-1 text-slate-100 bg-slate-900 border-slate-700"
                    value={branding[key] || ""}
                    onChange={(e) => setBranding({ ...branding, [key]: e.target.value })}
                  />
                </label>
              ))}
            </div>
          </section>

          {/* Logo & Favicon Upload Desk */}
          <section className="bg-slate-950 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-xl">
            <h3 className="font-black text-lg text-white flex items-center gap-2">
              <FiImage className="text-amber-400" /> Logo Asset & Favicon Upload
            </h3>

            <div className="grid sm:grid-cols-2 gap-4">
              {["logo", "favicon"].map((kind) => (
                <div key={kind} className="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-3">
                  <div className="flex gap-3 items-center">
                    {assets[kind]?.url ? (
                      <img src={assets[kind].url} alt={kind} className="w-16 h-16 object-contain bg-white rounded-xl p-1 shrink-0" />
                    ) : (
                      <div className="w-16 h-16 grid place-items-center bg-slate-800 border border-slate-700 rounded-xl text-amber-400 shrink-0">
                        <NepalYatraSymbol size={36} />
                      </div>
                    )}
                    <div className="space-y-1">
                      <b className="capitalize text-white block text-sm">{kind === "logo" ? "Primary Brand Logo" : "Browser Favicon"}</b>
                      <p className="text-xs text-slate-400">
                        {assets[kind] ? `${assets[kind].width}×${assets[kind].height} px` : "Using vector emblem"}
                      </p>
                      <div className="flex gap-2 pt-1">
                        <label className="cursor-pointer px-3 py-1.5 bg-sky-700 hover:bg-sky-600 rounded-xl text-xs font-bold text-white flex items-center gap-1">
                          <FiUpload size={12} /> Upload
                          <input
                            type="file"
                            accept="image/png,image/jpeg,image/svg+xml,image/webp,image/x-icon"
                            className="hidden"
                            onChange={(e) => upload(kind, e.target.files?.[0])}
                          />
                        </label>
                        {assets[kind] && (
                          <button
                            onClick={() => remove(kind)}
                            className="p-1.5 bg-rose-900/80 hover:bg-rose-800 text-rose-200 rounded-xl"
                            title="Remove custom asset"
                          >
                            <FiTrash2 size={14} />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <p className="text-[11px] text-slate-400 bg-slate-900 p-3 rounded-2xl border border-slate-800 leading-relaxed">
              🏔️ <b>Vector Guarantee:</b> When no custom image file is uploaded, the platform renders the geometric <b>Nepal Yatra</b> vector emblem (Himalayan peak + golden travel path + crimson flag accent).
            </p>

            {/* Theme presets */}
            <h4 className="font-bold text-sm text-amber-300 pt-2 border-t border-slate-800">Theme Presets</h4>
            <div className="grid grid-cols-3 gap-2">
              {Object.entries(_presets || {}).map(([key, preset]) => (
                <button
                  key={key}
                  onClick={() => setBranding({ ...branding, theme_preset: key, ...preset })}
                  className={`p-3 rounded-2xl border text-left transition-all ${
                    branding.theme_preset === key
                      ? "border-amber-400 bg-amber-500/10"
                      : "border-slate-700 bg-slate-900 hover:border-slate-600"
                  }`}
                >
                  <div className="flex gap-1 mb-1">
                    <span className="w-4 h-4 rounded-full" style={{ background: preset.primary_color }} />
                    <span className="w-4 h-4 rounded-full" style={{ background: preset.secondary_color }} />
                    <span className="w-4 h-4 rounded-full" style={{ background: preset.background_color }} />
                  </div>
                  <span className="capitalize text-[11px] font-bold text-slate-200">{key}</span>
                </button>
              ))}
            </div>
          </section>
        </div>
      )}

      {/* ===================== TAB: STRUCTURE & LAYOUT ===================== */}
      {tab === "structure" && (
        <div className="space-y-6">
          <div className="grid lg:grid-cols-2 gap-6">
            {CHOICE_GROUPS.map(({ group, icon: GroupIcon, fields }) => (
              <section key={group} className="bg-slate-950 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-xl">
                <h3 className="font-black text-lg text-white flex items-center gap-2">
                  <GroupIcon className="text-amber-400" /> {group}
                </h3>
                <div className="space-y-4">
                  {fields.map(([key, label, options]) => (
                    <div key={key}>
                      <span className="block text-xs font-bold text-slate-300 mb-2">
                        {label}
                        <span className="text-slate-500 font-normal"> — currently: {choiceLabel(null, key, branding[key])}</span>
                      </span>
                      <div className="grid grid-cols-3 gap-2">
                        {options.map(([value, optionLabel]) => (
                          <button
                            key={value}
                            onClick={() => setBranding({ ...branding, [key]: value })}
                            className={`px-2 py-2 rounded-xl border text-[11px] font-bold transition-all ${
                              branding[key] === value
                                ? "border-amber-400 bg-amber-500/10 text-amber-200"
                                : "border-slate-700 bg-slate-900 text-slate-400 hover:border-slate-600"
                            }`}
                          >
                            {optionLabel.split(" — ")[0]}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            ))}
          </div>

          {/* Visibility toggles */}
          <section className="bg-slate-950 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-xl">
            <h3 className="font-black text-lg text-white flex items-center gap-2">
              <FiMaximize className="text-amber-400" /> Site Element Visibility
            </h3>
            <p className="text-[11px] text-slate-400">
              Show or hide built-in site elements across the user-facing website. Toggles apply immediately on publish.
            </p>
            <div className="grid sm:grid-cols-2 gap-3">
              {TOGGLES.map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setBranding({ ...branding, [key]: !branding[key] })}
                  className={`flex items-center justify-between gap-3 p-4 rounded-2xl border text-left transition-all ${
                    branding[key]
                      ? "border-emerald-500/50 bg-emerald-500/10"
                      : "border-slate-700 bg-slate-900"
                  }`}
                >
                  <span className="text-xs font-bold text-slate-200">{label}</span>
                  <span className={`w-10 h-5 rounded-full p-0.5 transition-all ${branding[key] ? "bg-emerald-500" : "bg-slate-700"}`}>
                    <span className={`block w-4 h-4 rounded-full bg-white transition-all ${branding[key] ? "translate-x-5" : ""}`} />
                  </span>
                </button>
              ))}
            </div>

            <div className="grid sm:grid-cols-2 gap-3 pt-2 border-t border-slate-800">
              <label className="block text-xs font-bold text-slate-300">
                Announcement bar text (shown when the bar is on)
                <input
                  type="text"
                  maxLength={300}
                  placeholder="e.g. Dashain special — 15% off all trekking packages"
                  className="input-field mt-1 text-slate-100 bg-slate-900 border-slate-700"
                  value={branding.announcement_bar_text || ""}
                  onChange={(e) => setBranding({ ...branding, announcement_bar_text: e.target.value })}
                />
              </label>
              <label className="block text-xs font-bold text-slate-300">
                Footer heading
                <input
                  type="text"
                  maxLength={300}
                  placeholder="e.g. Explore the Himalayas"
                  className="input-field mt-1 text-slate-100 bg-slate-900 border-slate-700"
                  value={branding.footer_heading || ""}
                  onChange={(e) => setBranding({ ...branding, footer_heading: e.target.value })}
                />
              </label>
            </div>
          </section>
        </div>
      )}

      {/* ===================== TAB: ORGANIZATION & LINKS ===================== */}
      {tab === "organization" && (
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Quick links manager */}
          <section className="bg-slate-950 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-xl">
            <h3 className="font-black text-lg text-white flex items-center gap-2">
              <FiLink2 className="text-amber-400" /> Quick Links Manager
            </h3>
            <p className="text-[11px] text-slate-400">
              Add up to 12 quick links. They render in the header menu and footer so admins can promote any page, booking form, or partner site without a code change.
            </p>

            <div className="space-y-2">
              {(branding.quick_links || []).map((link, index) => (
                <div key={index} className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-2xl p-3">
                  <FiCheckCircle size={14} className="text-emerald-400 shrink-0" />
                  <div className="min-w-0 flex-1">
                    <b className="text-xs text-white block truncate">{link.label}</b>
                    <span className="text-[10px] text-slate-400 block truncate">{link.url}</span>
                  </div>
                  <button
                    onClick={() => removeQuickLink(index)}
                    className="p-1.5 bg-rose-900/80 hover:bg-rose-800 text-rose-200 rounded-xl shrink-0"
                    title="Remove link"
                  >
                    <FiX size={13} />
                  </button>
                </div>
              ))}
              {(branding.quick_links || []).length === 0 && (
                <p className="text-xs text-slate-500 text-center py-4 border border-dashed border-slate-800 rounded-2xl">
                  No quick links yet — add the first one below.
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800">
              <input
                type="text"
                placeholder="Label (e.g. Book a Flight)"
                maxLength={60}
                className="input-field text-slate-100 bg-slate-900 border-slate-700"
                value={newLink.label}
                onChange={(e) => setNewLink({ ...newLink, label: e.target.value })}
              />
              <input
                type="url"
                placeholder="https://…"
                maxLength={500}
                className="input-field text-slate-100 bg-slate-900 border-slate-700"
                value={newLink.url}
                onChange={(e) => setNewLink({ ...newLink, url: e.target.value })}
                onKeyDown={(e) => e.key === "Enter" && addQuickLink()}
              />
            </div>
            <button
              onClick={addQuickLink}
              disabled={(branding.quick_links || []).length >= 12}
              className="w-full px-4 py-2.5 bg-sky-700 hover:bg-sky-600 disabled:opacity-40 text-white rounded-2xl font-black text-xs flex items-center justify-center gap-2 transition-all"
            >
              <FiPlus size={14} /> Add Quick Link ({(branding.quick_links || []).length}/12)
            </button>
          </section>

          {/* Footer sections manager */}
          <section className="bg-slate-950 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-xl">
            <h3 className="font-black text-lg text-white flex items-center gap-2">
              <FiGrid className="text-amber-400" /> Footer Sections Manager
            </h3>
            <p className="text-[11px] text-slate-400">
              Build the footer column-by-column. Each section becomes a footer block with its own heading and rich text — organize contact info, payment partners, or regional offices without touching code.
            </p>

            <div className="space-y-2">
              {(branding.footer_sections || []).map((section, index) => (
                <div key={index} className="bg-slate-900 border border-slate-800 rounded-2xl p-3 space-y-1">
                  <div className="flex items-center gap-2">
                    <FiGrid size={13} className="text-amber-400 shrink-0" />
                    <b className="text-xs text-white flex-1 truncate">{section.heading}</b>
                    <button
                      onClick={() => removeFooterSection(index)}
                      className="p-1.5 bg-rose-900/80 hover:bg-rose-800 text-rose-200 rounded-xl shrink-0"
                      title="Remove section"
                    >
                      <FiX size={13} />
                    </button>
                  </div>
                  <p className="text-[10px] text-slate-400 line-clamp-2">{section.content}</p>
                </div>
              ))}
              {(branding.footer_sections || []).length === 0 && (
                <p className="text-xs text-slate-500 text-center py-4 border border-dashed border-slate-800 rounded-2xl">
                  No footer sections yet — add the first one below.
                </p>
              )}
            </div>

            <div className="space-y-2 pt-2 border-t border-slate-800">
              <input
                type="text"
                placeholder="Section heading (e.g. Payment Partners)"
                maxLength={60}
                className="input-field text-slate-100 bg-slate-900 border-slate-700"
                value={newSection.heading}
                onChange={(e) => setNewSection({ ...newSection, heading: e.target.value })}
              />
              <textarea
                rows={2}
                placeholder="Section content (e.g. We accept Visa, Mastercard, eSewa, Khalti…)"
                maxLength={500}
                className="input-field text-slate-100 bg-slate-900 border-slate-700"
                value={newSection.content}
                onChange={(e) => setNewSection({ ...newSection, content: e.target.value })}
              />
            </div>
            <button
              onClick={addFooterSection}
              disabled={(branding.footer_sections || []).length >= 12}
              className="w-full px-4 py-2.5 bg-sky-700 hover:bg-sky-600 disabled:opacity-40 text-white rounded-2xl font-black text-xs flex items-center justify-center gap-2 transition-all"
            >
              <FiPlus size={14} /> Add Footer Section ({(branding.footer_sections || []).length}/12)
            </button>
          </section>
        </div>
      )}

      {/* Submit Button */}
      <div className="flex justify-end pt-2">
        <button
          disabled={busy}
          onClick={save}
          className="px-8 py-3.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-2xl font-black text-sm flex items-center gap-2 shadow-xl shadow-emerald-600/25 transition-all whitespace-nowrap"
        >
          <FiSave size={18} /> {busy ? "Publishing..." : "Publish Portal Branding & Heading"}
        </button>
      </div>
    </div>
  )
}
