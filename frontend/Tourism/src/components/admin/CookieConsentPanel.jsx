import { useEffect, useState } from "react"
import { FiCheck, FiSave } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"
import { DEFAULT_COOKIE_MESSAGE, resolveCookieConsent } from "../../utils/cookieConsent"

/**
 * Cookie consent controls (CMS brief §17) — enable/disable the visitor
 * cookie banner and edit its message.
 *
 * Stored as the public `cookie_consent` SiteSetting row through the same
 * CMS API the Pages panel uses, so changes apply to the live site with no
 * rebuild. With no row saved yet, the banner shows with the default
 * message — turning it off here is what hides it.
 */
export default function CookieConsentPanel() {
  const { showToast } = useToast()
  const [settingId, setSettingId] = useState(null)
  const [draft, setDraft] = useState(() => resolveCookieConsent(null))
  const [saved, setSaved] = useState(() => resolveCookieConsent(null))
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const load = async () => {
    try {
      const res = await adminApi.getCMS("settings")
      const row = (res.data?.results || []).find((r) => r.key === "cookie_consent")
      if (row) {
        setSettingId(row.id)
        const resolved = resolveCookieConsent(row.value)
        setDraft(resolved)
        setSaved(resolved)
      }
    } catch {
      showToast("Could not load cookie consent settings.", "error")
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
      const value = { enabled: draft.enabled, message: draft.message.trim() }
      const res = settingId
        ? await adminApi.runCMSAction({ resource: "settings", id: settingId, value })
        : await adminApi.createCMS({ resource: "settings", key: "cookie_consent", value, description: "Visitor cookie consent banner", is_public: true })
      setSettingId(res.data?.id || settingId)
      const resolved = resolveCookieConsent(value)
      setSaved(resolved)
      setDraft(resolved)
      showToast(res.data?.message || "Cookie consent saved.", "success")
    } catch (err) {
      showToast(err.response?.data?.detail || "Save failed — please try again.", "error")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="mr-auto">
          <h2 className="text-lg font-bold text-slate-900">Cookie Consent</h2>
          <p className="text-xs text-slate-500">
            Control the cookie notice visitors see. Changes apply to the live site immediately — no rebuild needed.
            Visitors who accept will not see it again in their browser.
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
          <p className="p-6 text-center text-sm text-slate-500">Loading cookie consent settings…</p>
        ) : (
          <>
            <div className="flex items-center gap-3 px-4 py-3">
              <div className="min-w-0 flex-1">
                <p className="text-sm font-bold text-slate-800">Show cookie notice</p>
                <p className="text-[11px] text-slate-500">
                  The site uses essential cookies for sign-in, language and theme. Showing the notice keeps that transparent.
                </p>
              </div>
              <button
                onClick={() => setDraft({ ...draft, enabled: !draft.enabled })}
                role="switch"
                aria-checked={draft.enabled}
                aria-label={draft.enabled ? "Hide cookie notice" : "Show cookie notice"}
                className={`relative h-6 w-11 shrink-0 rounded-full transition-colors ${draft.enabled ? "bg-emerald-600" : "bg-slate-300"}`}
              >
                <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all ${draft.enabled ? "left-[22px]" : "left-0.5"}`} />
              </button>
              <span className={`w-12 text-right text-[10px] font-bold ${draft.enabled ? "text-emerald-700" : "text-slate-400"}`}>
                {draft.enabled ? "Shown" : "Hidden"}
              </span>
            </div>
            <label className="block px-4 py-3">
              <span className="text-[11px] font-bold uppercase tracking-wide text-slate-600">Notice message</span>
              <textarea
                value={draft.message}
                onChange={(event) => setDraft({ ...draft, message: event.target.value })}
                rows={3}
                placeholder={DEFAULT_COOKIE_MESSAGE}
                className="mt-1 w-full rounded-lg border border-emerald-200 px-2.5 py-1.5 text-sm focus:border-emerald-600 focus:outline-none"
              />
              <span className="mt-1 block text-[10px] text-slate-400">
                A link to the Privacy Policy is always added after the message. Clear the box to restore the default wording.
              </span>
            </label>
          </>
        )}
      </div>
    </div>
  )
}
