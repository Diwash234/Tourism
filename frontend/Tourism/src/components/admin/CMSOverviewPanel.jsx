import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { FiActivity, FiCheckCircle, FiExternalLink, FiFileText, FiImage, FiLayers, FiRadio, FiXCircle } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import configApi from "../../api/configApi"

/**
 * CMS Overview — the landing screen of Content & CMS.
 * Every number and status here comes from a real request made on mount;
 * nothing is simulated and no status is green unless the actual call
 * succeeded (brief: "Do not display fake green statuses").
 */

const timeAgo = (iso) => {
  if (!iso) return "unknown"
  const diff = Date.now() - new Date(iso).getTime()
  if (Number.isNaN(diff)) return "unknown"
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return "just now"
  if (mins < 60) return `${mins} min ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} hr ago`
  return `${Math.floor(hours / 24)} d ago`
}

export default function CMSOverviewPanel() {
  const [checks, setChecks] = useState({ publicSite: null, cmsApi: null, media: null, notices: null })
  const [counts, setCounts] = useState(null)
  const [recent, setRecent] = useState([])
  const [health, setHealth] = useState(null)

  useEffect(() => {
    let cancelled = false
    const run = async () => {
      const mark = (key, ok) => { if (!cancelled) setChecks((prev) => ({ ...prev, [key]: ok })) }

      // Real health probes — each status reflects an actual request result.
      configApi.getPublicConfig().then(() => mark("publicSite", true)).catch(() => mark("publicSite", false))
      adminApi.getMediaLibrary({ page_size: 12 })
        .then(({ data }) => { mark("media", true); if (!cancelled) setCounts((prev) => ({ ...(prev || {}), media: data.count ?? 0 })) })
        .catch(() => mark("media", false))
      adminApi.getVisitorDesk({})
        .then(({ data }) => {
          mark("notices", true)
          const rows = data.results || data || []
          if (!cancelled) setCounts((prev) => ({ ...(prev || {}), notices: Array.isArray(rows) ? rows.length : 0 }))
        })
        .catch(() => mark("notices", false))

      try {
        const [pagesRes, sectionsRes, navRes, healthRes] = await Promise.all([
          adminApi.getCMS("pages"),
          adminApi.getCMS("sections"),
          adminApi.getCMS("navigation"),
          adminApi.getCMSHealth().catch(() => null),
        ])
        if (cancelled) return
        mark("cmsApi", true)
        const pages = pagesRes.data.results || pagesRes.data || []
        const sections = sectionsRes.data.results || sectionsRes.data || []
        const nav = navRes.data.results || navRes.data || []
        setCounts((prev) => ({
          ...(prev || {}),
          pages: pages.length,
          published: pages.filter((p) => p.status === "published").length,
          drafts: pages.filter((p) => p.status === "draft").length,
          sections: sections.length,
          navigation: nav.length,
        }))
        // Recently changed — derived from real updated_at timestamps only.
        const label = (kind, row) => ({
          label: `${row.title || row.label || row.key || row.route || `#${row.id}`}`,
          kind,
          at: row.updated_at,
        })
        const merged = [
          ...pages.map((row) => label("Page", row)),
          ...sections.map((row) => label("Section", row)),
          ...nav.map((row) => label("Menu item", row)),
        ].filter((item) => item.at).sort((a, b) => new Date(b.at) - new Date(a.at)).slice(0, 8)
        setRecent(merged)
        if (healthRes) {
          const rows = healthRes.data.results || healthRes.data || []
          const warnings = rows.reduce((sum, row) => sum + (row.warning_count || 0), 0)
          const worst = [...rows].sort((a, b) => (b.warning_count || 0) - (a.warning_count || 0)).slice(0, 4)
          setHealth({ pagesChecked: rows.length, warnings, worst })
        }
      } catch {
        mark("cmsApi", false)
      }
    }
    const t = setTimeout(run, 0)
    return () => { cancelled = true; clearTimeout(t) }
  }, [])

  const statusPill = (state) =>
    state === null ? (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-700/60 px-2.5 py-1 text-[11px] font-bold text-slate-300">
        <FiActivity className="animate-pulse" /> Checking…
      </span>
    ) : state ? (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/20 px-2.5 py-1 text-[11px] font-black text-emerald-300">
        <FiCheckCircle /> Online
      </span>
    ) : (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-500/20 px-2.5 py-1 text-[11px] font-black text-rose-300">
        <FiXCircle /> Failed
      </span>
    )

  const stat = (icon, label, value) => (
    <div className="bg-slate-900/70 border border-slate-600/40 rounded-2xl p-4 flex items-center gap-3">
      <div className="p-2.5 rounded-xl bg-emerald-500/15 text-emerald-300">{icon}</div>
      <div className="min-w-0">
        <p className="text-[11px] uppercase font-bold text-slate-300 truncate">{label}</p>
        <p className="text-xl font-black text-white">{value ?? "—"}</p>
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-black text-emerald-950">CMS Overview</h2>
          <p className="text-sm text-emerald-900/60">Live status of the public Nepal Yatra website and everything the CMS controls. All values are fetched from the backend on load.</p>
        </div>
        <a
          href="/?as=traveller"
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-2 self-start rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-black text-white hover:bg-emerald-600"
        >
          <FiExternalLink /> Preview public website
        </a>
      </div>

      {/* Website status — real request results only */}
      <div className="bg-slate-900/70 border border-slate-600/40 rounded-2xl p-5">
        <h3 className="text-sm font-black uppercase tracking-wider text-slate-300 mb-3">Website status</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="flex items-center justify-between rounded-xl bg-slate-800/60 px-4 py-3"><span className="text-xs font-bold text-slate-200">Public website config</span>{statusPill(checks.publicSite)}</div>
          <div className="flex items-center justify-between rounded-xl bg-slate-800/60 px-4 py-3"><span className="text-xs font-bold text-slate-200">CMS API</span>{statusPill(checks.cmsApi)}</div>
          <div className="flex items-center justify-between rounded-xl bg-slate-800/60 px-4 py-3"><span className="text-xs font-bold text-slate-200">Media library</span>{statusPill(checks.media)}</div>
          <div className="flex items-center justify-between rounded-xl bg-slate-800/60 px-4 py-3"><span className="text-xs font-bold text-slate-200">Announcements</span>{statusPill(checks.notices)}</div>
        </div>
      </div>

      {/* Content counts */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {stat(<FiFileText size={18} />, "Pages", counts?.pages)}
        {stat(<FiCheckCircle size={18} />, "Published", counts?.published)}
        {stat(<FiLayers size={18} />, "Drafts", counts?.drafts)}
        {stat(<FiLayers size={18} />, "Sections", counts?.sections)}
        {stat(<FiImage size={18} />, "Media", counts?.media)}
        {stat(<FiRadio size={18} />, "Announcements", counts?.notices)}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recently changed */}
        <div className="bg-slate-900/70 border border-slate-600/40 rounded-2xl p-5">
          <h3 className="text-sm font-black uppercase tracking-wider text-slate-300 mb-3">Recently changed</h3>
          {recent.length === 0 ? (
            <p className="text-xs text-slate-400">No timestamped changes reported yet.</p>
          ) : (
            <ul className="space-y-2">
              {recent.map((item, i) => (
                <li key={`${item.kind}-${item.label}-${i}`} className="flex items-center justify-between gap-3 rounded-lg bg-slate-800/50 px-3 py-2">
                  <span className="min-w-0">
                    <span className="block truncate text-xs font-bold text-white">{item.label}</span>
                    <span className="text-[10px] uppercase font-black text-emerald-300/80">{item.kind}</span>
                  </span>
                  <span className="shrink-0 text-[11px] font-semibold text-slate-300">{timeAgo(item.at)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Content audit — from the real resource=health checks */}
        <div className="bg-slate-900/70 border border-slate-600/40 rounded-2xl p-5">
          <h3 className="text-sm font-black uppercase tracking-wider text-slate-300 mb-3">Content audit</h3>
          {health === null ? (
            <p className="text-xs text-slate-400">Loading audit…</p>
          ) : (
            <>
              <p className="text-xs text-slate-300">
                {health.pagesChecked} pages checked · <b className={health.warnings ? "text-amber-300" : "text-emerald-300"}>{health.warnings} open warnings</b>
              </p>
              <ul className="mt-3 space-y-2">
                {health.worst.filter((row) => (row.warning_count || 0) > 0).map((row) => (
                  <li key={row.page_id} className="rounded-lg bg-slate-800/50 px-3 py-2">
                    <span className="block truncate text-xs font-bold text-white">{row.title} <span className="font-medium text-slate-400">({row.route})</span></span>
                    <span className="text-[11px] text-amber-300/90">{(row.warnings || []).map((w) => w.message).join(" · ") || `${row.warning_count} warnings`}</span>
                  </li>
                ))}
                {health.warnings === 0 && <li className="text-xs text-emerald-300">No content warnings — every page passed its checks.</li>}
              </ul>
            </>
          )}
        </div>
      </div>

      {/* Quick actions */}
      <div className="bg-slate-900/70 border border-slate-600/40 rounded-2xl p-5">
        <h3 className="text-sm font-black uppercase tracking-wider text-slate-300 mb-3">Quick actions</h3>
        <div className="flex flex-wrap gap-2.5">
          {[
            ["/admin?section=cms", "Edit pages & menus"],
            ["/admin?section=media_library", "Manage images"],
            ["/admin?section=branding", "Branding & theme"],
            ["/admin?section=visitor_desk", "Announcements"],
            ["/admin?section=featured_destinations", "Featured content"],
          ].map(([href, text]) => (
            <Link key={href} to={href} className="rounded-xl bg-emerald-600 hover:bg-emerald-500 px-3.5 py-2 text-xs font-black text-white whitespace-nowrap">
              {text}
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
