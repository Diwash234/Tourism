import { useEffect, useState } from "react"
import { FiClock, FiEye, FiFilePlus, FiRefreshCw, FiRotateCcw, FiSave, FiSend, FiX } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

const resources = ["settings", "pages", "sections", "navigation", "translations"]
const templates = {
  settings: { key: "", value: {}, description: "", is_public: true },
  pages: { route: "/", key: "new-page", title: "New page", meta_description: "", is_enabled: true, status: "draft" },
  sections: { page_id: null, key: "new-section", title: "New section", subtitle: "", body: "", image_url: "", cta_text: "", cta_url: "", icon: "", layout_variant: "default", config: {}, display_order: 0, is_visible: true, status: "draft" },
  navigation: { location: "navbar", label: "New link", route: "/", icon: "", parent_id: null, allowed_roles: [], display_order: 0, is_active: true },
  translations: { target_resource: "pages", object_id: null, language_code: "ne", content: { title: "" } },
}
const clean = (row) => Object.fromEntries(Object.entries(row || {}).filter(([key]) => !["updated_at", "published_at", "scheduled_publish_at"].includes(key)))
const displayName = (row) => row.title || row.label || row.key || row.route || `Record #${row.id}`

export default function CMSPanel() {
  const { showToast } = useToast()
  const [resource, setResource] = useState("pages")
  const [rows, setRows] = useState([])
  const [selected, setSelected] = useState(null)
  const [json, setJson] = useState("")
  const [history, setHistory] = useState([])
  const [preview, setPreview] = useState(null)
  const [scheduleAt, setScheduleAt] = useState("")
  const [busy, setBusy] = useState(false)

  const load = async (keepId) => {
    try {
      const { data } = await adminApi.getCMS(resource)
      setRows(data.results || [])
      if (keepId) {
        const current = (data.results || []).find(row => row.id === keepId)
        if (current) choose(current)
      }
    } catch (error) { showToast(error.response?.data?.detail || "Could not load CMS records", "error") }
  }
  useEffect(() => { setSelected(null); setPreview(null); setHistory([]); load() }, [resource])

  const choose = (row) => {
    setSelected(row)
    setJson(JSON.stringify(clean(row), null, 2))
    setPreview(null)
    setHistory([])
  }
  const createNew = () => {
    const row = { ...templates[resource], id: null }
    setSelected(row)
    setJson(JSON.stringify(clean(row), null, 2))
    setHistory([])
    setPreview(null)
  }
  const payload = () => {
    const parsed = JSON.parse(json)
    delete parsed.id
    return parsed
  }
  const execute = async (operation, success) => {
    setBusy(true)
    try {
      const response = await operation()
      showToast(response.data?.message || success, "success")
      const id = response.data?.id || selected?.id
      await load(id)
      return response
    } catch (error) {
      showToast(error instanceof SyntaxError ? "Structured data is not valid JSON" : error.response?.data?.detail || "CMS action failed", "error")
    } finally { setBusy(false) }
  }
  const save = () => execute(
    () => selected.id ? adminApi.updateCMS({ ...payload(), resource, id: selected.id }) : adminApi.createCMS({ ...payload(), resource }),
    "Draft saved"
  )
  const workflow = (action, extra = {}) => execute(
    () => adminApi.runCMSAction({ resource, id: selected.id, action, ...extra }),
    `${action} complete`
  )
  const showPreview = async () => {
    if (!selected?.id) return showToast("Save this draft before previewing it", "info")
    try { setPreview((await adminApi.getCMS(resource, { id: selected.id, preview: true })).data.preview) }
    catch (error) { showToast(error.response?.data?.detail || "Preview failed", "error") }
  }
  const showHistory = async () => {
    if (!selected?.id) return
    try { setHistory((await adminApi.getCMS(resource, { id: selected.id, history: true })).data.results || []) }
    catch { showToast("Revision history unavailable", "error") }
  }
  const rollback = async (revisionId) => {
    if (!window.confirm("Restore this revision as a new revision? The current version remains in history.")) return
    await workflow("rollback", { revision_id: revisionId })
    showHistory()
  }

  const supportsWorkflow = ["pages", "sections"].includes(resource) && selected?.id
  return <div className="space-y-4 text-slate-100">
    <header><h2 className="text-2xl font-black">Content publishing studio</h2><p className="text-xs text-slate-400">Safe structured content with draft preview, scheduled publication, immutable revisions, and rollback.</p></header>
    <div className="grid xl:grid-cols-[220px_300px_1fr] gap-4">
      <aside className="bg-slate-950 border border-slate-700 rounded-2xl p-3 h-fit">
        {resources.map(item => <button key={item} onClick={() => setResource(item)} className={`block w-full text-left capitalize px-3 py-2.5 rounded-xl mb-1 ${resource === item ? "bg-amber-400 text-slate-950 font-black" : "text-slate-300 hover:bg-slate-800"}`}>{item}</button>)}
        <button onClick={createNew} className="mt-4 w-full px-3 py-2.5 bg-emerald-700 rounded-xl text-sm font-bold flex items-center justify-center gap-2"><FiFilePlus/> New {resource.slice(0,-1)}</button>
      </aside>

      <section className="bg-slate-950 border border-slate-700 rounded-2xl overflow-hidden h-fit max-h-[72vh]">
        <div className="p-3 border-b border-slate-800 flex justify-between"><b className="capitalize">{resource}</b><button onClick={() => load()} title="Refresh"><FiRefreshCw/></button></div>
        <div className="overflow-y-auto max-h-[65vh] p-2 space-y-1">{rows.map(row => <button onClick={() => choose(row)} key={row.id} className={`block w-full text-left p-3 rounded-xl text-xs ${selected?.id === row.id ? "bg-slate-700 ring-1 ring-amber-400" : "bg-slate-900 hover:bg-slate-800"}`}><span className="font-bold text-white">{displayName(row)}</span><span className="flex justify-between mt-1 text-[10px] text-slate-500"><span>#{row.id}</span>{row.status && <span className={row.status === "published" ? "text-emerald-300" : row.status === "scheduled" ? "text-sky-300" : "text-amber-300"}>{row.status}</span>}</span></button>)}</div>
      </section>

      <section className="bg-slate-950 border border-slate-700 rounded-2xl p-4 min-w-0">
        {!selected ? <p className="text-slate-500 py-20 text-center">Select a record or create a new draft.</p> : <div className="space-y-3">
          <div className="flex flex-wrap gap-2 items-center"><b className="mr-auto">{selected.id ? displayName(selected) : `New ${resource.slice(0,-1)}`}</b><button disabled={busy} onClick={save} className="px-3 py-2 bg-emerald-700 rounded-lg text-xs font-bold flex gap-1"><FiSave/> Save</button>{selected.id && <button onClick={showPreview} className="px-3 py-2 bg-sky-700 rounded-lg text-xs font-bold flex gap-1"><FiEye/> Preview</button>}{selected.id && <button onClick={showHistory} className="px-3 py-2 bg-slate-700 rounded-lg text-xs font-bold flex gap-1"><FiClock/> History</button>}</div>
          <textarea rows="20" spellCheck="false" value={json} onChange={event => setJson(event.target.value)} className="w-full rounded-xl bg-slate-900 border border-slate-700 text-emerald-300 font-mono text-xs p-3"/>
          <p className="text-[11px] text-slate-500">Only allowlisted structured fields are saved. Routes, colors, icons, and publication state are validated by the backend; executable HTML or scripts are not accepted as configuration.</p>
          {supportsWorkflow && <div className="border-t border-slate-800 pt-3 flex flex-wrap gap-2"><button onClick={() => workflow(selected.status === "published" ? "unpublish" : "publish")} className={`px-3 py-2 rounded-lg text-xs font-bold flex gap-1 ${selected.status === "published" ? "bg-amber-700" : "bg-purple-700"}`}><FiSend/> {selected.status === "published" ? "Return to draft" : "Publish now"}</button><input type="datetime-local" value={scheduleAt} onChange={event => setScheduleAt(event.target.value)} className="bg-slate-900 border border-slate-700 rounded-lg px-2 text-xs"/><button disabled={!scheduleAt} onClick={() => workflow("schedule", { scheduled_publish_at: new Date(scheduleAt).toISOString() })} className="px-3 py-2 rounded-lg bg-sky-700 disabled:opacity-40 text-xs font-bold">Schedule</button></div>}
        </div>}
      </section>
    </div>

    {preview && <div className="fixed inset-0 z-[80] bg-black/75 grid place-items-center p-4"><div className="bg-white text-slate-900 rounded-2xl max-w-3xl w-full max-h-[85vh] overflow-y-auto p-6"><div className="flex justify-between border-b pb-3"><div><span className="text-[10px] uppercase font-black text-amber-700">Administrative draft preview</span><h2 className="text-3xl font-black">{displayName(preview)}</h2></div><button onClick={() => setPreview(null)}><FiX size={22}/></button></div>{preview.meta_description && <p className="text-slate-500 mt-2">{preview.meta_description}</p>}{preview.sections?.map(section => <article key={section.id} className="py-6 border-b"><h3 className="text-xl font-bold">{section.title}</h3><p className="text-slate-500">{section.subtitle}</p><p className="mt-3 whitespace-pre-wrap">{section.body}</p>{section.cta_text && <span className="inline-block mt-3 bg-emerald-700 text-white px-4 py-2 rounded-lg">{section.cta_text}</span>}</article>)}{!preview.sections && <pre className="mt-5 text-xs bg-slate-100 p-4 rounded-xl overflow-auto">{JSON.stringify(preview, null, 2)}</pre>}</div></div>}

    {!!history.length && <div className="fixed inset-0 z-[80] bg-black/75 flex justify-end"><aside className="bg-slate-950 border-l border-slate-700 w-full max-w-lg p-5 overflow-y-auto"><div className="flex justify-between"><h3 className="text-xl font-black">Revision history</h3><button onClick={() => setHistory([])}><FiX/></button></div><p className="text-xs text-slate-500 mt-1 mb-4">Rollback creates a new revision and never destroys history.</p>{history.map(revision => <div key={revision.id} className="bg-slate-900 rounded-xl p-3 mb-2 text-xs"><div className="flex justify-between"><b>Revision {revision.revision_number} · {revision.action}</b><button onClick={() => rollback(revision.id)} className="text-amber-300 flex gap-1"><FiRotateCcw/> Restore</button></div><p className="text-slate-500 mt-1">{new Date(revision.created_at).toLocaleString()} · {revision.created_by || "system"}</p></div>)}</aside></div>}
  </div>
}
