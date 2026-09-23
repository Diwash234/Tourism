import { useEffect, useState } from "react"
import { notifyCmsUpdated } from "../../hooks/usePublicConfig"
import { FiImage, FiSave, FiTrash2, FiUpload, FiCheck, FiSliders, FiSun, FiGlobe } from "react-icons/fi"
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

export default function BrandingPanel() {
  const { showToast } = useToast()
  const [branding, setBranding] = useState({
    site_title: "Nepal Yatra",
    tagline: "Himalayan Journeys & Travel Planning",
    theme_preset: "himalayan",
    primary_color: "#C8102E",
    secondary_color: "#0B3D91",
  })
  const [assets, setAssets] = useState({})
  const [presets, setPresets] = useState({})
  const [busy, setBusy] = useState(false)

  const load = async () => {
    try {
      const { data } = await adminApi.getBranding()
      setBranding((prev) => ({
        site_title: "Nepal Yatra",
        tagline: "Himalayan Journeys & Travel Planning",
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
      const allowed = [...textFields, ...socialFields].reduce(
        (value, [key]) => ({ ...value, [key]: branding[key] || "" }),
        {
          theme_preset: branding.theme_preset || "himalayan",
          site_title: branding.site_title || "Nepal Yatra",
          tagline: branding.tagline || "Himalayan Journeys & Travel Planning",
          primary_color: branding.primary_color || "#C8102E",
          secondary_color: branding.secondary_color || "#0B3D91",
        }
      )
      const { data } = await adminApi.updateBranding(allowed)
      setBranding(data.branding)

      // Notify all public config listeners to update logo and headers globally across the platform
      notifyCmsUpdated()
      showToast("Portal Branding & Heading updated globally across all pages!", "success")
    } catch (error) {
      showToast("Branding save failed", "error")
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

  return (
    <div className="space-y-6 text-slate-100">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-950 p-6 rounded-3xl border border-slate-800 shadow-xl">
        <div>
          <span className="px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-bold uppercase tracking-wider">
            Admin Branding & Identity Desk
          </span>
          <h2 className="text-2xl font-black text-white mt-1">Portal Heading, Logo & Theme Control</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Update the main brand name ("Nepal Yatra"), tagline, logo assets, and color palettes. Changes update globally across all user & admin views.
          </p>
        </div>

        <button
          disabled={busy}
          onClick={save}
          className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-2xl font-black text-xs flex items-center gap-2 shadow-lg shadow-emerald-600/20 transition-all whitespace-nowrap"
        >
          <FiSave size={16} /> {busy ? "Publishing..." : "Publish Branding & Heading"}
        </button>
      </div>

      {/* Live Brand Preview Card — mirrors the published traveller header using
          the draft values below, so admins see exactly what will ship. */}
      <div className="p-6 rounded-3xl bg-white border border-[#E5E0D5] space-y-3 shadow-xl">
        <span className="text-[10px] font-black uppercase text-[#697675] block tracking-wider">Live Logo & Header Preview</span>
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
              Book Now
            </span>
            <span className="px-3 py-1.5 rounded-xl border font-black text-xs" style={{ color: branding.secondary_color || "#0B3D91", borderColor: branding.secondary_color || "#0B3D91" }}>
              Explore
            </span>
          </div>
        </div>
        <p className="text-[11px] text-[#697675]">
          Preview updates as you type and uses the same brand tokens (<code>--brand-primary</code>/<code>--brand-secondary</code>) the live site reads after you publish.
        </p>
      </div>

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
                    <p className="text-[10px] text-slate-400">
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
            💡 <b>Vector Guarantee:</b> When no custom image file is uploaded, the platform renders the geometric <b>Nepal Yatra</b> vector emblem (Himalayan peak + golden travel path + crimson flag accent).
          </p>
        </section>
      </div>

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
