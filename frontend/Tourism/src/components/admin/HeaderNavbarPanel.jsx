import { useEffect, useState } from "react"
import { FiCheck, FiSave } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"
import { NAVBAR_FEATURES, resolveNavbarFeatures } from "../../utils/navbarFeatures"

/**
 * Header & Navbar controls (CMS brief §5) — enable/disable the visitor
 * header features: Search, Language switcher, Profile menu, Notifications
 * bell, Theme toggle.
 *
 * Stored as the public `navbar_features` SiteSetting row through the same
 * CMS API the Pages panel uses, so switches apply to the live site with no
 * rebuild. Every switch defaults to ON; turning one off never breaks auth —
 * login, signup and role portals are not toggleable.
 */
export default function HeaderNavbarPanel() {
  const { showToast } = useToast()
  const [settingId, setSettingId] = useState(null)
  const [draft, setDraft] = useState(() => resolveNavbarFeatures(null))
  const [saved, setSaved] = useState(() => resolveNavbarFeatures(null))
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const load = async () => {
    try {
      const res = await adminApi.getCMS("settings")
      const row = (res.data?.results || []).find((r) => r.key === "navbar_features")
      if (row) {
        setSettingId(row.id)
        const resolved = resolveNavbarFeatures(row.value)
        setDraft(resolved)
        setSaved(resolved)
      }
    } catch {
      showToast("Could not load header settings.", "error")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect flush.
    const t = setTimeout(() => { load() }, 0)
    return () => clearTimeout(t)
  }, [])

  const dirty = JSON.stringify(draft) !== JSON.stringify(saved)

  const save = async () => {
    if (saving || !dirty) return
    setSaving(true)
    try {
      const value = { ...draft }
      const res = settingId
        ? await adminApi.runCMSAction({ resource: "settings", id: settingId, value })
        : await adminApi.createCMS({ resource: "settings", key: "navbar_features", value, description: "Header & navbar feature switches", is_public: true })
      const savedRow = res.data?.record || value
      setSettingId(res.data?.id || settingId)
      const resolved = resolveNavbarFeatures(savedRow.value ?? savedRow)
      setSaved(resolved)
      setDraft(resolved)
      showToast(res.data?.message || "Header settings saved.", "success")
    } catch (err) {
      showToast(err.response?.data?.detail || "Save failed — please try again.", "error")
    } finally {
      setSaving(false)
    }
  }

  const toggle = (key) => setDraft({ ...draft, [key]: !draft[key] })

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="mr-auto">
          <h2 className="text-lg font-bold text-slate-900">Header &amp; Navbar</h2>
          <p className="text-xs text-slate-500">
            Choose which features appear in the visitor header. Changes apply to the live site immediately — no rebuild needed.
            Login, signup and staff portals always stay available.
          </p>
        </div>
        <button
          onClick={save}
          disabled={saving || !dirty}
          className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-700 px-3 py-1.5 text-xs font-bold text-white hover:bg-emerald-800 disabled:opacity-40"
        >
          {saving ? "Saving…" : dirty ? <><FiSave /> Save changes</> : <><FiCheck /> Saved</>}
        </button>
      </div>

      <div className="rounded-xl border border-emerald-200 bg-white divide-y divide-emerald-100">
        {loading ? (
          <p className="p-6 text-center text-sm text-slate-500">Loading header settings…</p>
        ) : (
          NAVBAR_FEATURES.map((feature) => (
            <div key={feature.key} className="flex items-center gap-3 px-4 py-3">
              <div className="min-w-0 flex-1">
                <p className="text-sm font-bold text-slate-800">{feature.label}</p>
                <p className="text-[11px] text-slate-500">{feature.description}</p>
              </div>
              <button
                onClick={() => toggle(feature.key)}
                role="switch"
                aria-checked={draft[feature.key]}
                aria-label={`${draft[feature.key] ? "Hide" : "Show"} ${feature.label}`}
                className={`relative h-6 w-11 shrink-0 rounded-full transition-colors ${draft[feature.key] ? "bg-emerald-600" : "bg-slate-300"}`}
              >
                <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all ${draft[feature.key] ? "left-[22px]" : "left-0.5"}`} />
              </button>
              <span className={`w-12 text-right text-[10px] font-bold ${draft[feature.key] ? "text-emerald-700" : "text-slate-400"}`}>
                {draft[feature.key] ? "Shown" : "Hidden"}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
