import { useCallback, useEffect, useMemo, useState } from "react"
import { Link } from "react-router-dom"
import {
  FiSearch, FiCheckCircle, FiXCircle, FiArchive, FiRefreshCw, FiEdit3,
  FiGitMerge, FiAlertTriangle, FiLayers, FiClock, FiEye, FiActivity
} from "react-icons/fi"
import axiosClient from "../../api/axiosClient"
import useToast from "../../hooks/useToast"
import { AdminPagination, AdminStatusBadge } from "./AdminPrimitives"

const STATUS_COLORS = {
  approved: "bg-emerald-500/15 text-emerald-300 border-emerald-400/40",
  draft: "bg-slate-500/15 text-slate-300 border-slate-400/40",
  submitted: "bg-amber-500/15 text-amber-300 border-amber-400/40",
  pending: "bg-amber-500/15 text-amber-300 border-amber-400/40",
  rejected: "bg-rose-500/15 text-rose-300 border-rose-400/40",
  archived: "bg-slate-600/20 text-slate-400 border-slate-500/40",
}

function StatusPill({ status }) {
  return (
    <span className={`text-[11px] px-2 py-0.5 rounded-full border ${STATUS_COLORS[status] || STATUS_COLORS.draft}`}>
      {status}
    </span>
  )
}

function SectionCard({ title, icon, count, children }) {
  return (
    <div className="bg-slate-900/70 border border-slate-600/40 rounded-2xl shadow-xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-white font-bold flex items-center gap-2">{icon}{title}</h3>
        {count !== undefined && <span className="text-xs text-slate-400">{count} records</span>}
      </div>
      {children}
    </div>
  )
}

export default function ContentLifecyclePanel() {
  const { showToast } = useToast()

  // ---- All content table state ----
  const [rows, setRows] = useState([])
  const [meta, setMeta] = useState({ count: 0, pages: 1, page: 1 })
  const [q, setQ] = useState("")
  const [filters, setFilters] = useState({ status: "", district: "", provenance: "", missing: "", ordering: "-updated_at" })
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState([])
  const [bulkReason, setBulkReason] = useState("")

  // ---- Approvals / conflicts / duplicates / integrity ----
  const [approvals, setApprovals] = useState(null)
  const [conflicts, setConflicts] = useState(null)
  const [dupes, setDupes] = useState(null)
  const [dupeFilter, setDupeFilter] = useState("high")
  const [integrity, setIntegrity] = useState(null)
  const [revisionsFor, setRevisionsFor] = useState(null)
  const [revisions, setRevisions] = useState(null)
  const [subTab, setSubTab] = useState("content")

  const loadContent = useCallback(() => {
    const params = { page, page_size: 25, ...filters }
    if (q.trim()) params.q = q.trim()
    Object.keys(params).forEach((k) => params[k] === "" && delete params[k])
    axiosClient.get("/admin/destinations", { params })
      .then(({ data }) => { setRows(data.results); setMeta(data); })
      .catch(() => showToast("Could not load content table.", "error"))
      .finally(() => setLoading(false))
  }, [q, filters, page, showToast])

  const loadApprovals = useCallback(() => {
    axiosClient.get("/admin/approvals/")
      .then(({ data }) => setApprovals(data))
      .catch(() => setApprovals(null)) // editors without approve capability: silently hide
  }, [])
  const loadConflicts = useCallback(() => {
    axiosClient.get("/admin/import-conflicts/")
      .then(({ data }) => setConflicts(data))
      .catch(() => setConflicts(null))
  }, [])
  const loadDupes = useCallback(() => {
    axiosClient.get("/admin/duplicates/", { params: { confidence: dupeFilter, limit: 50 } })
      .then(({ data }) => setDupes(data))
      .catch(() => showToast("Could not load duplicate candidates.", "error"))
  }, [dupeFilter, showToast])
  const loadIntegrity = useCallback(() => {
    axiosClient.get("/admin/data-integrity/")
      .then(({ data }) => setIntegrity(data))
      .catch(() => showToast("Could not load data integrity counts.", "error"))
  }, [showToast])

  useEffect(() => { loadContent() }, [loadContent])
  useEffect(() => {
    if (subTab === "approvals") loadApprovals()
    if (subTab === "conflicts") loadConflicts()
    if (subTab === "duplicates") loadDupes()
    if (subTab === "quality") loadIntegrity()
  }, [subTab, loadApprovals, loadConflicts, loadDupes, loadIntegrity])

  const [preview, setPreview] = useState(null)

  const runLifecycle = async (row, action) => {
    const reason = window.prompt(`Reason for '${action}' on "${row.name}":`)
    if (reason === null) return
    try {
      const { data } = await axiosClient.post(`/admin/destinations/${row.id}/lifecycle/`, { action, reason })
      showToast(`${action}: now ${data.public ? "PUBLIC" : "not public"}.`, "success")
      loadContent()
    } catch (e) {
      showToast(e.response?.data?.detail || `${action} failed.`, "error")
    }
  }

  const openPreview = async (row) => {
    try {
      const { data } = await axiosClient.get(`/admin/destinations/${row.id}/preview/`)
      setPreview(data)
    } catch {
      showToast("Preview failed.", "error")
    }
  }

  const runBulk = async (action) => {
    if (!selected.length) return showToast("Select rows first.", "error")
    if (!bulkReason.trim()) return showToast("A reason is required for bulk operations.", "error")
    if (action === "delete" && !window.confirm(`Permanently delete ${selected.length} records? This cannot be undone.`)) return
    try {
      const { data } = await axiosClient.post("/admin/destinations/bulk/", {
        action, ids: selected, reason: bulkReason.trim(), confirm: action === "delete" ? "true" : undefined,
      })
      showToast(`Bulk ${action}: ${data.count} records updated.`, "success")
      setSelected([])
      loadContent()
    } catch (e) {
      showToast(e.response?.data?.detail || `Bulk ${action} failed.`, "error")
    }
  }

  const resolveConflict = async (id, action) => {
    const reason = window.prompt(`Reason for '${action}' (required):`)
    if (!reason || !reason.trim()) return
    try {
      await axiosClient.post("/admin/import-conflicts/", { id, action, reason: reason.trim() })
      showToast(`Conflict ${action}ed.`, "success")
      loadConflicts()
    } catch (e) {
      showToast(e.response?.data?.detail || "Resolve failed.", "error")
    }
  }

  const reviewProposal = async (id, action) => {
    const note = window.prompt(`Review note for '${action}':`) || ""
    try {
      await axiosClient.post("/admin/approvals/", { id, action, review_note: note })
      showToast(`Proposal ${action}.`, "success")
      loadApprovals()
      loadContent()
    } catch (e) {
      showToast(e.response?.data?.detail || "Review failed.", "error")
    }
  }

  const dupeDecision = async (pair, verdict) => {
    const reason = window.prompt(`Reason for '${verdict}' (required):`)
    if (!reason || !reason.trim()) return
    let survivor_id
    if (verdict === "merge") {
      const choice = window.prompt(`Which record survives? Enter the surviving id (${pair[0]} or ${pair[1]}):`)
      survivor_id = parseInt(choice, 10)
      if (![pair[0], pair[1]].includes(survivor_id)) return showToast("Invalid survivor id.", "error")
    }
    try {
      await axiosClient.post("/admin/duplicates/decision/", { a: pair[0], b: pair[1], verdict, reason: reason.trim(), survivor_id })
      showToast(verdict === "merge" ? "Merged." : "Pair dismissed.", "success")
      loadDupes()
    } catch (e) {
      showToast(e.response?.data?.detail || "Decision failed.", "error")
    }
  }

  const openRevisions = async (id) => {
    setRevisionsFor(id)
    const { data } = await axiosClient.get("/admin/destinations/revisions/", { params: { destination: id } })
    setRevisions(data)
  }

  const restoreRevision = async (revisionId) => {
    const reason = window.prompt("Reason for restore (required):")
    if (!reason || !reason.trim()) return
    try {
      const { data } = await axiosClient.post("/admin/destinations/revisions/", {
        destination: revisionsFor, action: "restore", revision_id: revisionId, reason: reason.trim(),
      })
      showToast(`Restored: ${data.changed.join(", ")}`, "success")
      setRevisions(null); setRevisionsFor(null); loadContent()
    } catch (e) {
      showToast(e.response?.data?.detail || "Restore failed.", "error")
    }
  }

  const qualityCards = useMemo(() => {
    if (!integrity) return []
    return [
      ["Total", integrity.total_records, {}],
      ["Published", integrity.published, { status: "approved" }],
      ["Draft", integrity.draft, { status: "draft" }],
      ["Pending review", integrity.pending_review, { status: "pending" }],
      ["Rejected", integrity.rejected, { status: "rejected" }],
      ["Archived", integrity.archived, { status: "archived" }],
      ["Missing coordinates", integrity.missing_coordinates, { missing: "coordinates" }],
      ["Invalid coordinates", integrity.invalid_coordinates, {}],
      ["Missing description", integrity.missing_description, { missing: "description" }],
      ["Missing images", integrity.missing_images, { missing: "images" }],
      ["Unverified", integrity.unverified, {}],
      ["Stale verification", integrity.stale_verification, {}],
      ["Import conflicts", integrity.import_conflicts_pending, { tab: "conflicts" }],
      ["Proposals pending", integrity.proposals_pending, { tab: "approvals" }],
    ]
  }, [integrity])

  const applyQualityFilter = (target) => {
    if (target.tab) { setSubTab(target.tab); return }
    setFilters((f) => ({ ...f, status: target.status ?? "", missing: target.missing ?? "" }))
    setSubTab("content")
    setPage(1)
  }

  const TABS = [["content", "All Content", <FiLayers key="i" />], ["approvals", "Approval Center", <FiCheckCircle key="i" />],
    ["conflicts", "Import Conflicts", <FiAlertTriangle key="i" />], ["duplicates", "Duplicate Review", <FiGitMerge key="i" />],
    ["quality", "Data Quality", <FiActivity key="i" />]]

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-2">
        {TABS.map(([id, label, icon]) => (
          <button key={id} onClick={() => setSubTab(id)}
            className={`px-4 py-2 rounded-xl text-sm font-semibold flex items-center gap-2 border transition-all ${subTab === id ? "bg-amber-400/20 text-amber-300 border-amber-400/50" : "bg-slate-900/60 text-slate-300 border-slate-600/40 hover:border-slate-500"}`}>
            {icon}{label}
          </button>
        ))}
      </div>

      {subTab === "content" && (
        <SectionCard title="All Content — Destinations" icon={<FiLayers />} count={meta.count}>
          <div className="flex flex-wrap gap-2">
            {[["", "All"], ["draft", "Draft"], ["pending", "Pending Review"], ["approved", "Published"],
              ["rejected", "Rejected"], ["archived", "Archived"]].map(([value, label]) => {
              const n = meta.status_counts
                ? (value === "" ? meta.count : meta.status_counts[value])
                : null
              return (
                <button key={value || "all"} onClick={() => { setFilters((f) => ({ ...f, status: value })); setPage(1) }}
                  className={`text-xs px-3 py-1.5 rounded-lg border ${filters.status === value ? "bg-amber-400/20 text-amber-300 border-amber-400/50" : "border-slate-600/50 text-slate-300 hover:border-slate-400"}`}>
                  {label}{n != null ? ` ${n}` : ""}
                </button>
              )
            })}
          </div>
          <div className="flex flex-wrap gap-2 items-center">
            <div className="relative flex-1 min-w-[220px]">
              <FiSearch className="absolute left-3 top-3 text-slate-400" />
              <input value={q} onChange={(e) => { setLoading(true); setQ(e.target.value); setPage(1) }}
                onKeyDown={(e) => e.key === "Enter" && loadContent()}
                placeholder="Search id, name, slug, address, district, description, category…"
                className="input-field pl-9 w-full" />
            </div>
            {[["status", ["", "All statuses"], ["approved", "Published"], ["draft", "Draft"], ["pending", "Pending"], ["submitted", "Submitted"], ["rejected", "Rejected"], ["archived", "Archived"]],
              ["provenance", ["", "Any provenance"], ["manual", "Admin (manual)"], ["imported", "Imported"], ["user_suggested", "User suggested"]],
              ["missing", ["", "No quality filter"], ["coordinates", "Missing coordinates"], ["description", "Missing description"], ["images", "Missing images"]],
              ["ordering", [["-updated_at", "Recently updated"], ["name", "Name A→Z"], ["-created_at", "Newest first"]]]].map(([key, opts]) => (
              <select key={key} value={filters[key]} className="input-field"
                onChange={(e) => { setLoading(true); setFilters((f) => ({ ...f, [key]: e.target.value })); setPage(1) }}>
                {opts.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            ))}
            <input value={filters.district} onChange={(e) => { setLoading(true); setFilters((f) => ({ ...f, district: e.target.value })); setPage(1) }}
              placeholder="District" className="input-field w-32" />
          </div>

          {selected.length > 0 && (
            <div className="flex flex-wrap gap-2 items-center bg-slate-800/60 border border-slate-600/40 rounded-xl p-3">
              <span className="text-xs text-slate-300">{selected.length} selected</span>
              <input value={bulkReason} onChange={(e) => setBulkReason(e.target.value)}
                placeholder="Reason (required)" className="input-field flex-1 min-w-[160px]" />
              {[["publish", "Publish", FiCheckCircle], ["unpublish", "Unpublish", FiEye], ["archive", "Archive", FiArchive],
                ["restore", "Restore", FiRefreshCw], ["verify", "Verify", FiCheckCircle], ["unverify", "Unverify", FiXCircle],
                ["delete", "Delete", FiXCircle]].map(([action, label, Icon]) => (
                <button key={action} onClick={() => runBulk(action)}
                  className={`text-xs px-3 py-1.5 rounded-lg border flex items-center gap-1 ${action === "delete" ? "border-rose-400/50 text-rose-300" : "border-slate-500/50 text-slate-200 hover:border-amber-400/50"}`}>
                  <Icon size={13} />{label}
                </button>
              ))}
            </div>
          )}

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-400 text-xs uppercase border-b border-slate-700">
                  <th className="p-2"><input type="checkbox" onChange={(e) => setSelected(e.target.checked ? rows.map((r) => r.id) : [])} /></th>
                  <th className="p-2">Name</th><th className="p-2">District</th><th className="p-2">Category</th>
                  <th className="p-2">Status</th><th className="p-2">Provenance</th><th className="p-2">Coords</th>
                  <th className="p-2">Flags</th><th className="p-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading && <tr><td colSpan={9} className="p-4 text-slate-400">Loading…</td></tr>}
                {!loading && rows.map((r) => (
                  <tr key={r.id} className="border-b border-slate-800 hover:bg-slate-800/40">
                    <td className="p-2"><input type="checkbox" checked={selected.includes(r.id)}
                      onChange={(e) => setSelected((s) => e.target.checked ? [...s, r.id] : s.filter((x) => x !== r.id))} /></td>
                    <td className="p-2 text-white">#{r.id} {r.name}</td>
                    <td className="p-2 text-slate-300">{r.district}</td>
                    <td className="p-2 text-slate-300">{r.category}</td>
                    <td className="p-2"><StatusPill status={r.status} />{!r.is_active && <span className="ml-1 text-[10px] text-slate-500">inactive</span>}</td>
                    <td className="p-2 text-slate-400 text-xs">{r.provenance}</td>
                    <td className="p-2 text-xs text-slate-400">{r.latitude != null ? `${r.latitude.toFixed(4)}, ${r.longitude?.toFixed(4)}` : "—"} <span className={r.coordinate_status === "VERIFIED" ? "text-emerald-400" : "text-amber-400"}>{r.coordinate_status === "VERIFIED" ? "✓" : "?"}</span></td>
                    <td className="p-2 text-xs">
                      {!r.has_description && <span className="text-amber-400 mr-1">no-desc</span>}
                      {r.image_count === 0 && <span className="text-amber-400 mr-1">no-img</span>}
                      {r.pending_conflicts > 0 && <span className="text-rose-400 mr-1">{r.pending_conflicts}⚠</span>}
                      {r.pending_proposals > 0 && <span className="text-amber-300">{r.pending_proposals}📝</span>}
                    </td>
                    <td className="p-2 space-y-1">
                      <span className={`block text-[10px] font-bold ${r.public ? "text-emerald-400" : "text-slate-500"}`}>
                        Public: {r.public ? "YES" : "NO"}
                      </span>
                      <div className="flex flex-wrap gap-1">
                        <Link className="text-amber-300 text-xs flex items-center gap-1" to={`/admin?section=data_explorer&resource=destinations&open=${r.id}`}><FiEdit3 size={11} />Edit</Link>
                        {r.status === "approved" && r.is_active
                          ? <button onClick={() => runLifecycle(r, "unpublish")} className="text-slate-300 text-xs border border-slate-600 rounded px-1.5">Unpublish</button>
                          : <button onClick={() => runLifecycle(r, "publish")} className="text-emerald-300 text-xs border border-emerald-500/50 rounded px-1.5">Publish</button>}
                        {r.status === "archived"
                          ? <button onClick={() => runLifecycle(r, "restore")} className="text-sky-300 text-xs border border-sky-500/50 rounded px-1.5">Restore</button>
                          : <button onClick={() => runLifecycle(r, "archive")} className="text-slate-400 text-xs border border-slate-600 rounded px-1.5">Archive</button>}
                        <button onClick={() => openPreview(r)} className="text-slate-300 text-xs border border-slate-600 rounded px-1.5">Preview</button>
                        {r.public && <a href={`/destinations/${r.slug}`} target="_blank" rel="noreferrer" className="text-emerald-400 text-xs border border-emerald-500/40 rounded px-1.5">View ↗</a>}
                        <button onClick={() => openRevisions(r.id)} className="text-slate-400 text-xs flex items-center gap-1 hover:text-white"><FiClock size={11} />History</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <AdminPagination page={meta.page} pages={meta.pages} onChange={(p) => { setLoading(true); setPage(p) }} />
        </SectionCard>
      )}

      {subTab === "approvals" && (
        <SectionCard title="Approval Center" icon={<FiCheckCircle />} count={approvals?.pending ?? 0}>
          {!approvals && <p className="text-slate-400 text-sm">You do not have approval permission.</p>}
          {approvals?.results?.length === 0 && <p className="text-slate-400 text-sm">Nothing is waiting for approval. 🎉</p>}
          {approvals?.results?.map((p) => (
            <div key={p.id} className="border border-slate-700 rounded-xl p-4 space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-white font-semibold">{p.destination.name} <span className="text-slate-500 text-xs">#{p.destination.id}</span></span>
                <span className="text-xs text-slate-400">by {p.submitted_by || "system"} · {new Date(p.created_at).toLocaleString()}</span>
              </div>
              <table className="w-full text-xs">
                <tbody>
                  {p.diff.map((d) => (
                    <tr key={d.field} className="border-b border-slate-800">
                      <td className="p-1 text-slate-400">{d.field}</td>
                      <td className="p-1 text-rose-300 line-through">{String(d.old ?? "").slice(0, 80)}</td>
                      <td className="p-1 text-emerald-300">{String(d.new ?? "").slice(0, 80)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {p.reason && <p className="text-xs text-slate-400">Reason: {p.reason}</p>}
              <div className="flex gap-2">
                <button onClick={() => reviewProposal(p.id, "approve")} className="text-xs px-3 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-400/50">Approve & Publish</button>
                <button onClick={() => reviewProposal(p.id, "reject")} className="text-xs px-3 py-1.5 rounded-lg bg-rose-500/20 text-rose-300 border border-rose-400/50">Reject</button>
                <button onClick={() => reviewProposal(p.id, "send_back")} className="text-xs px-3 py-1.5 rounded-lg bg-slate-700/40 text-slate-200 border border-slate-500/50">Send back</button>
              </div>
            </div>
          ))}
        </SectionCard>
      )}

      {subTab === "conflicts" && (
        <SectionCard title="Import Conflicts" icon={<FiAlertTriangle />} count={conflicts?.pending_total ?? 0}>
          {!conflicts && <p className="text-slate-400 text-sm">Conflicts unavailable (permission).</p>}
          {conflicts?.results?.length === 0 && <p className="text-slate-400 text-sm">No pending conflicts.</p>}
          {conflicts?.results?.map((c) => (
            <div key={c.id} className="border border-slate-700 rounded-xl p-4 space-y-1">
              <div className="text-white text-sm font-semibold">{c.destination.name} <span className="text-slate-500">#{c.destination.id}</span> — field <code className="text-amber-300">{c.field}</code></div>
              <div className="text-xs"><span className="text-slate-400">current (admin):</span> <span className="text-emerald-300">{c.current_value}</span></div>
              <div className="text-xs"><span className="text-slate-400">incoming ({c.source}):</span> <span className="text-rose-300">{c.incoming_value}</span></div>
              <div className="flex gap-2 pt-1">
                <button onClick={() => resolveConflict(c.id, "keep")} className="text-xs px-3 py-1 rounded-lg border border-slate-500/50 text-slate-200">Keep current</button>
                <button onClick={() => resolveConflict(c.id, "accept")} className="text-xs px-3 py-1 rounded-lg border border-emerald-400/50 text-emerald-300">Accept incoming</button>
              </div>
            </div>
          ))}
        </SectionCard>
      )}

      {subTab === "duplicates" && (
        <SectionCard title="Duplicate Review" icon={<FiGitMerge />} count={dupes?.count}>
          <div className="flex gap-2">
            {["high", "medium", "needs_review"].map((t) => (
              <button key={t} onClick={() => setDupeFilter(t)}
                className={`text-xs px-3 py-1.5 rounded-lg border ${dupeFilter === t ? "bg-amber-400/20 text-amber-300 border-amber-400/50" : "border-slate-600 text-slate-300"}`}>
                {t} ({dupes?.tier_counts?.[t] ?? "…"})
              </button>
            ))}
          </div>
          {dupes?.results?.length === 0 && <p className="text-slate-400 text-sm">No candidates in this tier.</p>}
          {dupes?.results?.map((r) => (
            <div key={r.pair.join("-")} className="border border-slate-700 rounded-xl p-4">
              <div className="flex flex-wrap justify-between text-sm">
                <span className="text-white">#{r.pair[0]} {r.a.name} <span className="text-slate-500">({r.a.district})</span></span>
                <span className="text-white">#{r.pair[1]} {r.b.name} <span className="text-slate-500">({r.b.district})</span></span>
              </div>
              <div className="text-xs text-slate-400 mt-1">{r.evidence} · <AdminStatusBadge value={r.confidence} /></div>
              <div className="flex gap-2 mt-2">
                <button onClick={() => dupeDecision(r.pair, "merge")} className="text-xs px-3 py-1 rounded-lg border border-emerald-400/50 text-emerald-300">Merge…</button>
                <button onClick={() => dupeDecision(r.pair, "not_duplicate")} className="text-xs px-3 py-1 rounded-lg border border-slate-500/50 text-slate-200">Not a duplicate</button>
              </div>
            </div>
          ))}
        </SectionCard>
      )}

      {subTab === "quality" && (
        <SectionCard title="Data Quality" icon={<FiAlertTriangle />}>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {qualityCards.map(([label, value, target]) => (
              <button key={label} onClick={() => applyQualityFilter(target)}
                className="bg-slate-800/60 border border-slate-600/40 rounded-xl p-3 text-left hover:border-amber-400/50">
                <div className="text-2xl font-black text-white">{value ?? "…"}</div>
                <div className="text-xs text-slate-400">{label}</div>
              </button>
            ))}
          </div>
          {integrity && (
            <div className="text-xs text-slate-400">
              Provenance: {integrity.provenance?.manual ?? 0} admin · {integrity.provenance?.imported ?? 0} imported · {integrity.provenance?.user_suggested ?? 0} user-suggested
            </div>
          )}
        </SectionCard>
      )}

      {preview && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setPreview(null)}>
          <div className="bg-slate-900 border border-slate-600 rounded-2xl p-5 max-w-2xl w-full space-y-3 max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center">
              <h3 className="text-white font-bold">Public preview — {preview.preview?.name}</h3>
              <span className={`text-xs px-2 py-1 rounded-full border ${preview.public ? "text-emerald-300 border-emerald-400/50" : "text-amber-300 border-amber-400/50"}`}>
                {preview.public ? "PUBLIC" : "NOT PUBLIC"}
              </span>
            </div>
            {!preview.public && (
              <div className="bg-slate-800/70 border border-slate-700 rounded-xl p-3 text-sm">
                <div className="text-amber-300 font-semibold">Why isn&apos;t this public?</div>
                <div className="text-slate-300">{preview.not_public_reason}</div>
              </div>
            )}
            {preview.public && preview.public_url && (
              <a className="text-emerald-400 text-sm underline" href={preview.public_url} target="_blank" rel="noreferrer">
                View on public website ↗
              </a>
            )}
            <pre className="text-xs text-slate-300 bg-slate-950/60 rounded-xl p-3 overflow-x-auto">{JSON.stringify(preview.preview, null, 1).slice(0, 3000)}</pre>
          </div>
        </div>
      )}

      {revisions && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setRevisions(null)}>
          <div className="bg-slate-900 border border-slate-600 rounded-2xl p-5 max-w-lg w-full space-y-3" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-white font-bold">Revision history — destination #{revisionsFor}</h3>
            {revisions.results?.length === 0 && <p className="text-slate-400 text-sm">No revisions recorded yet.</p>}
            {revisions.results?.map((r) => (
              <div key={r.id} className="flex justify-between items-center border-b border-slate-800 pb-2">
                <div className="text-sm text-slate-200">v{r.revision_number} · {r.action} <span className="text-slate-500 text-xs">by {r.created_by} · {new Date(r.created_at).toLocaleString()}</span></div>
                <button onClick={() => restoreRevision(r.id)} className="text-xs px-2 py-1 rounded-lg border border-amber-400/50 text-amber-300">Restore</button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
