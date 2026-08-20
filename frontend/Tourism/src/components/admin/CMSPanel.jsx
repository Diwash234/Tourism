import { useEffect, useRef, useState } from "react"
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
  const [savedJson, setSavedJson] = useState("")
  const [history, setHistory] = useState([])
  const [preview, setPreview] = useState(null)
  const [scheduleAt, setScheduleAt] = useState("")
  const [busy, setBusy] = useState(false)
  const dirty = Boolean(selected) && json !== savedJson
  const dirtyRef = useRef(false)
  dirtyRef.current = dirty

  const confirmLeave = () => !dirtyRef.current || window.confirm("You have unsaved changes.\n\nStay on this record or discard the changes?")

  const applyRow = (row) => {
    const next = JSON.stringify(clean(row), null, 2)
    setSelected(row)
    setJson(next)
    setSavedJson(next)
    setPreview(null)
    setHistory([])
  }

  const load = async (keepId) => {
    try {
      const { data } = await adminApi.getCMS(resource)
      setRows(data.results || [])
      if (keepId) {
        const current = (data.results || []).find(row => row.id === keepId)
        if (current) applyRow(current)
      }
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not load CMS records", "error")
    }
  }

  useEffect(() => {
    setSelected(null)
    setPreview(null)
    setHistory([])
    setSavedJson("")
    setJson("")
    load()
  }, [resource])

  useEffect(() => {
    const onBeforeUnload = (event) => {
      if (!dirtyRef.current) return
      event.preventDefault()
      event.returnValue = ""
    }
    window.addEventListener("beforeunload", onBeforeUnload)
    return () => window.removeEventListener("beforeunload", onBeforeUnload)
  }, [])

  const switchResource = (next) => {
    if (next === resource) return
    if (!confirmLeave()) return
    dirtyRef.current = false
    setResource(next)
  }

  const choose = (row) => {
    if (!confirmLeave()) return
    applyRow(row)
  }

  const createNew = () => {
    if (!confirmLeave()) return
    applyRow({ ...templates[resource], id: null })
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
      dirtyRef.current = false
      const id = response.data?.id || selected?.id
      await load(id)
      return response
    } catch (error) {
      showToast(error instanceof SyntaxError ? "Structured data is not valid JSON" : error.response?.data?.detail || "CMS action failed", "error")
    } finally {
      setBusy(false)
    }
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
  return (
    <div className="space-y-4 text-slate-900">
      <header>
        <h2 className="text-2xl font-black">Pages, sections and navigation</h2>
        <p className="text-xs text-slate-500">Edit website content without code. Draft, preview, publish, and restore previous versions.</p>
        {dirty && <p className="mt-2 text-xs font-bold text-amber-700">You have unsaved changes.</p>}
      </header>
      <div className="grid xl:grid-cols-[220px_300px_1fr] gap-4">
        <aside className="bg-white border border-emerald-200 rounded-2xl p-3 h-fit">
          {resources.map(item => (
            <button
              key={item}
              onClick={() => switchResource(item)}
              className={`block w-full text-left capitalize px-3 py-2.5 rounded-xl mb-1 ${resource === item ? "bg-emerald-700 text-white font-black" : "text-slate-600 hover:bg-emerald-50"}`}
            >
              {item}
            </button>
          ))}
          <button onClick={createNew} className="mt-4 w-full px-3 py-2.5 bg-emerald-700 text-white rounded-xl text-sm font-bold flex items-center justify-center gap-2">
            <FiFilePlus /> New {resource.slice(0, -1)}
          </button>
        </aside>

        <section className="bg-white border border-emerald-200 rounded-2xl overflow-hidden h-fit max-h-[72vh]">
          <div className="p-3 border-b border-emerald-100 flex justify-between">
            <b className="capitalize">{resource} <span className="ml-1 text-xs font-normal text-emerald-700">({rows.length})</span></b>
            <button onClick={() => load()} title="Refresh"><FiRefreshCw /></button>
          </div>
          <div className="overflow-y-auto max-h-[65vh] p-2 space-y-1">
            {rows.length === 0 && <p className="p-6 text-center text-sm text-slate-500">No records found.</p>}
            {rows.map(row => (
              <button onClick={() => choose(row)} key={row.id} className={`block w-full text-left p-3 rounded-xl text-xs ${selected?.id === row.id ? "bg-emerald-50 ring-1 ring-emerald-600" : "bg-slate-50 hover:bg-emerald-50"}`}>
                <span className="font-bold text-slate-900">{displayName(row)}</span>
                <span className="flex justify-between mt-1 text-[10px] text-slate-500">
                  <span>#{row.id}</span>
                  {row.status && <span className={row.status === "published" ? "text-emerald-700" : row.status === "scheduled" ? "text-sky-700" : "text-amber-700"}>{row.status}</span>}
                </span>
              </button>
            ))}
          </div>
        </section>

        <section className="bg-white border border-emerald-200 rounded-2xl p-4 min-w-0">
          {!selected ? (
            <p className="text-slate-500 py-20 text-center">Select a record or create a new draft.</p>
          ) : (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2 items-center">
                <b className="mr-auto">{selected.id ? displayName(selected) : `New ${resource.slice(0, -1)}`}</b>
                <button disabled={busy} onClick={save} className="px-3 py-2 bg-emerald-700 text-white rounded-lg text-xs font-bold flex gap-1"><FiSave /> Save draft</button>
                {selected.id && <button onClick={showPreview} className="px-3 py-2 bg-sky-700 text-white rounded-lg text-xs font-bold flex gap-1"><FiEye /> Preview</button>}
                {selected.id && <button onClick={showHistory} className="px-3 py-2 bg-slate-700 text-white rounded-lg text-xs font-bold flex gap-1"><FiClock /> History</button>}
              </div>
              <CMSFriendlyEditor resource={resource} json={json} setJson={setJson} />
              <details className="rounded-xl border border-emerald-200 bg-emerald-50 p-3">
                <summary className="cursor-pointer text-xs font-black text-emerald-800">Advanced</summary>
                <textarea rows="8" spellCheck="false" value={json} onChange={event => setJson(event.target.value)} className="mt-3 w-full rounded-xl border border-emerald-200 bg-white text-emerald-900 font-mono text-xs p-3" />
              </details>
              <p className="text-[11px] text-slate-500">Use the fields above for normal editing. Code, HTML and scripts are not required.</p>
              {supportsWorkflow && (
                <div className="border-t border-emerald-100 pt-3 flex flex-wrap gap-2">
                  <button onClick={() => workflow(selected.status === "published" ? "unpublish" : "publish")} className={`px-3 py-2 rounded-lg text-xs font-bold flex gap-1 text-white ${selected.status === "published" ? "bg-amber-700" : "bg-emerald-800"}`}>
                    <FiSend /> {selected.status === "published" ? "Return to draft" : "Publish now"}
                  </button>
                  <input type="datetime-local" value={scheduleAt} onChange={event => setScheduleAt(event.target.value)} className="border border-emerald-200 rounded-lg px-2 text-xs" />
                  <button disabled={!scheduleAt} onClick={() => workflow("schedule", { scheduled_publish_at: new Date(scheduleAt).toISOString() })} className="px-3 py-2 rounded-lg bg-sky-700 disabled:opacity-40 text-xs font-bold text-white">Schedule</button>
                </div>
              )}
            </div>
          )}
        </section>
      </div>

      {preview && (
        <div className="fixed inset-0 z-[80] bg-black/75 grid place-items-center p-4">
          <div className="bg-white text-slate-900 rounded-2xl max-w-3xl w-full max-h-[85vh] overflow-y-auto p-6">
            <div className="flex justify-between border-b pb-3">
              <div>
                <span className="text-[10px] uppercase font-black text-emerald-700">Draft preview</span>
                <h2 className="text-3xl font-black">{displayName(preview)}</h2>
              </div>
              <button onClick={() => setPreview(null)}><FiX size={22} /></button>
            </div>
            {preview.meta_description && <p className="text-slate-500 mt-2">{preview.meta_description}</p>}
            {preview.sections?.map(section => (
              <article key={section.id} className="py-6 border-b">
                <h3 className="text-xl font-bold">{section.title}</h3>
                <p className="text-slate-500">{section.subtitle}</p>
                <p className="mt-3 whitespace-pre-wrap">{section.body}</p>
                {section.cta_text && <span className="inline-block mt-3 bg-emerald-700 text-white px-4 py-2 rounded-lg">{section.cta_text}</span>}
              </article>
            ))}
            {!preview.sections && <pre className="mt-5 text-xs bg-slate-100 p-4 rounded-xl overflow-auto">{JSON.stringify(preview, null, 2)}</pre>}
          </div>
        </div>
      )}

      {!!history.length && (
        <div className="fixed inset-0 z-[80] bg-black/75 flex justify-end">
          <aside className="bg-white border-l w-full max-w-lg p-5 overflow-y-auto">
            <div className="flex justify-between">
              <h3 className="text-xl font-black">Revision history</h3>
              <button onClick={() => setHistory([])}><FiX /></button>
            </div>
            <p className="text-xs text-slate-500 mt-1 mb-4">Restore creates a new revision and never destroys history.</p>
            {history.map(revision => (
              <div key={revision.id} className="bg-emerald-50 rounded-xl p-3 mb-2 text-xs">
                <div className="flex justify-between">
                  <b>Version {revision.revision_number} · {revision.action}</b>
                  <button onClick={() => rollback(revision.id)} className="text-emerald-800 flex gap-1 font-bold"><FiRotateCcw /> Restore</button>
                </div>
                <p className="text-slate-500 mt-1">{new Date(revision.created_at).toLocaleString()} · {revision.created_by || "system"}</p>
              </div>
            ))}
          </aside>
        </div>
      )}
    </div>
  )
}

function CMSFriendlyEditor({ resource, json, setJson }) {
  let value = {}
  try { value = JSON.parse(json || "{}") } catch {
    return <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">Fix the syntax in Advanced before using the form.</p>
  }
  const set = (key, next) => setJson(JSON.stringify({ ...value, [key]: next }, null, 2))
  const field = (key, label, type = "text") => (
    <label key={key} className="text-xs font-semibold text-slate-600">
      {label}
      {type === "textarea"
        ? <textarea rows="4" className="input-field mt-1" value={value[key] ?? ""} onChange={e => set(key, e.target.value)} />
        : type === "checkbox"
          ? <input type="checkbox" className="ml-3" checked={Boolean(value[key])} onChange={e => set(key, e.target.checked)} />
          : <input type={type} className="input-field mt-1" value={value[key] ?? ""} onChange={e => set(key, type === "number" ? Number(e.target.value) : e.target.value)} />}
    </label>
  )
  if (resource === "pages") return <div className="grid gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 sm:grid-cols-2">{field("title", "Page title")}{field("key", "Page key")}{field("route", "Page route")}{field("meta_description", "Search description", "textarea")}<label className="text-xs font-semibold text-slate-600">Publication status<select className="input-field mt-1" value={value.status || "draft"} onChange={e => set("status", e.target.value)}><option>draft</option><option>scheduled</option><option>published</option></select></label>{field("is_enabled", "Show this page", "checkbox")}</div>
  if (resource === "sections") return <div className="grid gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 sm:grid-cols-2">{field("page_id", "Parent page ID", "number")}{field("key", "Section key")}{field("title", "Section title")}{field("subtitle", "Subtitle")}{field("body", "Body content", "textarea")}{field("image_url", "Image URL")}{field("cta_text", "Button text")}{field("cta_url", "Button route")}{field("icon", "Icon")}{field("display_order", "Display order", "number")}{field("is_visible", "Visible", "checkbox")}</div>
  if (resource === "navigation") return <div className="grid gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 sm:grid-cols-2"><label className="text-xs font-semibold text-slate-600">Location<select className="input-field mt-1" value={value.location || "navbar"} onChange={e => set("location", e.target.value)}><option>navbar</option><option>sidebar</option><option>footer</option></select></label>{field("label", "Visible label")}{field("route", "Internal route")}{field("parent_id", "Parent item ID")}{field("icon", "Icon")}{field("display_order", "Display order", "number")}<label className="text-xs font-semibold text-slate-600">Allowed roles (comma separated)<input className="input-field mt-1" value={(value.allowed_roles || []).join(", ")} onChange={e => set("allowed_roles", e.target.value.split(",").map(x => x.trim()).filter(Boolean))} /></label>{field("is_active", "Active", "checkbox")}</div>
  if (resource === "translations") return <div className="grid gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 sm:grid-cols-2">{field("target_resource", "Target type")}{field("object_id", "Target record ID", "number")}{field("language_code", "Language code")}<label className="text-xs font-semibold text-slate-600">Translated fields<textarea rows="5" className="input-field mt-1 font-mono" value={JSON.stringify(value.content || {}, null, 2)} onChange={e => { try { set("content", JSON.parse(e.target.value)) } catch { /* keep until valid */ } }} /></label></div>
  return <div className="grid gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 sm:grid-cols-2">{field("key", "Setting key")}{field("description", "Description")}{field("is_public", "Public setting", "checkbox")}<label className="text-xs font-semibold text-slate-600">Structured value<textarea rows="6" className="input-field mt-1 font-mono" value={JSON.stringify(value.value || {}, null, 2)} onChange={e => { try { set("value", JSON.parse(e.target.value)) } catch { /* keep until valid */ } }} /></label></div>
}
