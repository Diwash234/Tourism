import { useEffect, useRef, useState } from "react"
import { FiClock, FiEye, FiFilePlus, FiRefreshCw, FiRotateCcw, FiSave, FiSend, FiX } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"
import RichTextEditor from "./RichTextEditor"
import CMSBlock from "../cms/CMSBlock"

const resources = ["settings", "pages", "sections", "navigation", "translations"]
const sectionTypes = ["text", "heading", "image", "gallery", "cards", "faq", "cta", "map", "video", "audio", "marquee", "animation", "media", "form", "table", "figure", "testimonials", "contact", "breadcrumbs", "search"]
const fallbackTemplates = {
  blank: { label: "Blank" },
  destination: { label: "Destination Page" },
  hotel: { label: "Hotel Page" },
  travel_guide: { label: "Travel Guide" },
  gallery: { label: "Gallery" },
  information: { label: "Information Page" },
  landing: { label: "Landing Page" },
  footer: { label: "Site Footer" },
}
const templates = {
  settings: { key: "", value: {}, description: "", is_public: true },
  pages: { route: "/", key: "new-page", title: "New page", meta_description: "", seo_title: "", og_image_url: "", search_visible: true, is_enabled: true, status: "draft" },
  sections: { page_id: null, key: "new-section", title: "New section", subtitle: "", body: "", image_url: "", cta_text: "", cta_url: "", icon: "", section_type: "text", layout_variant: "default", config: {}, display_order: 0, is_visible: true, is_reusable: false, status: "draft" },
  navigation: { location: "navbar", label: "New link", route: "/", icon: "", parent_id: null, allowed_roles: [], display_order: 0, is_active: true },
  translations: { target_resource: "pages", object_id: null, language_code: "ne", content: { title: "" } },
}
const clean = (row) => Object.fromEntries(Object.entries(row || {}).filter(([key]) => !["updated_at", "published_at", "scheduled_publish_at"].includes(key)))
const displayName = (row) => {
  const name = row.title || row.label || row.key || row.route || `Record #${row.id}`
  if (row.page_title) return `${name} · ${row.page_title}`
  return name
}

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
  const [pageTemplate, setPageTemplate] = useState("blank")
  const [previewMode, setPreviewMode] = useState("desktop")
  const [previewKind, setPreviewKind] = useState("live")
  const [reusable, setReusable] = useState([])
  const [catalog, setCatalog] = useState(fallbackTemplates)
  const [cloneSource, setCloneSource] = useState("")
  const [builderTick, setBuilderTick] = useState(0)
  const [layoutUrl, setLayoutUrl] = useState("")
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

  const loadReusable = () => {
    adminApi.getCMS("sections", { reusable: true }).then(({ data }) => {
      const results = data.results || []
      setReusable(results)
      setCloneSource((current) => current || String(results[0]?.id || ""))
    }).catch(() => setReusable([]))
  }

  const load = async (keepId) => {
    try {
      const { data } = await adminApi.getCMS(resource)
      setRows(data.results || [])
      if (keepId) {
        const current = (data.results || []).find(row => row.id === keepId)
        if (current) applyRow(current)
      }
      if (resource === "sections" || resource === "pages") loadReusable()
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
    adminApi.getCMS("pages", { templates: true }).then(({ data }) => {
      if (data.templates) setCatalog(data.templates)
    }).catch(() => setCatalog(fallbackTemplates))
  }, [])

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
      const id = resource === "pages" ? (selected?.id || response.data?.id) : (response.data?.id || selected?.id)
      await load(id)
      setBuilderTick(value => value + 1)
      return response
    } catch (error) {
      showToast(error instanceof SyntaxError ? "Structured data is not valid JSON" : error.response?.data?.detail || "CMS action failed", "error")
    } finally {
      setBusy(false)
    }
  }

  const save = () => execute(
    () => selected.id
      ? adminApi.updateCMS({ ...payload(), resource, id: selected.id })
      : adminApi.createCMS({ ...payload(), resource, template: resource === "pages" ? pageTemplate : undefined }),
    "Draft saved"
  )

  const saveAndPublish = () => execute(
    async () => {
      const p = payload()
      p.status = "published"
      if (resource === "pages") p.is_enabled = true
      if (resource === "sections") p.is_visible = true
      if (resource === "navigation") p.is_active = true

      const res = selected.id
        ? await adminApi.updateCMS({ ...p, resource, id: selected.id })
        : await adminApi.createCMS({ ...p, resource, template: resource === "pages" ? pageTemplate : undefined })

      if (selected.id && ["pages", "sections"].includes(resource)) {
        await adminApi.runCMSAction({ resource, id: selected.id, action: "publish" })
      }

      window.dispatchEvent(new Event("cms-updated"))
      return res
    },
    "Published live to user site!"
  )
  const workflow = (action, extra = {}) => execute(
    () => adminApi.runCMSAction({ resource, id: selected.id, action, ...extra }),
    `${action} complete`
  )
  const showPreview = async () => {
    if (!selected?.id) return showToast("Save this draft before previewing it", "info")
    try {
      const data = (await adminApi.getCMS(resource, { id: selected.id, preview: true })).data.preview
      setPreview(data)
      setPreviewKind(data.route ? "live" : "draft")
    }
    catch (error) { showToast(error.response?.data?.detail || "Preview failed", "error") }
  }
  const travellerPreviewSrc = () => {
    const route = preview?.route || selected?.route || "/"
    try {
      const url = new URL(route, window.location.origin)
      url.searchParams.set("as", "traveller")
      return `${url.pathname}${url.search}`
    } catch {
      return "/?as=traveller"
    }
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
              className={`block w-full text-left capitalize px-3 py-2.5 rounded-xl mb-1 ${resource === item ? "bg-emerald-700 text-white font-black" : "text-slate-300 hover:bg-emerald-50"}`}
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
                <button disabled={busy} onClick={saveAndPublish} className="px-4 py-2 bg-amber-400 hover:bg-amber-500 text-slate-950 font-black rounded-lg text-xs flex gap-1 shadow"><FiSend /> Save & Publish Live</button>
                <button disabled={busy} onClick={save} className="px-3 py-2 bg-emerald-700 text-white rounded-lg text-xs font-bold flex gap-1"><FiSave /> Save draft</button>
                {selected.id && <button onClick={showPreview} className="px-3 py-2 bg-sky-700 text-white rounded-lg text-xs font-bold flex gap-1"><FiEye /> Preview</button>}
                {selected.id && <button onClick={showHistory} className="px-3 py-2 bg-slate-700 text-white rounded-lg text-xs font-bold flex gap-1"><FiClock /> History</button>}
              </div>
              {resource === "pages" && (
                <div className="grid gap-2 rounded-xl border border-emerald-100 bg-emerald-50 p-3 sm:grid-cols-[1fr_auto_auto]">
                  <label className="text-xs font-semibold text-slate-300">Page template
                    <select className="input-field mt-1" value={pageTemplate} onChange={event => setPageTemplate(event.target.value)}>
                      {Object.entries(catalog).map(([key, item]) => <option key={key} value={key}>{item.label || key}</option>)}
                    </select>
                  </label>
                  {selected.id && <button type="button" disabled={busy} onClick={() => workflow("apply_template", { template: pageTemplate })} className="self-end rounded-lg bg-white px-3 py-2 text-xs font-bold text-emerald-800">Add template sections</button>}
                  {selected.id && reusable.length > 0 && (
                    <div className="self-end flex gap-2">
                      <select className="input-field" value={cloneSource} onChange={event => setCloneSource(event.target.value)}>
                        {reusable.map(item => <option key={item.id} value={item.id}>{item.title || item.key}</option>)}
                      </select>
                      <button type="button" disabled={busy || !cloneSource} onClick={() => workflow("clone_reusable", { source_id: Number(cloneSource), page_id: selected.id })} className="rounded-lg bg-amber-100 px-3 py-2 text-xs font-bold text-amber-900">Add reusable</button>
                    </div>
                  )}
                  {selected.id && (
                    <label className="sm:col-span-3 text-xs font-semibold text-slate-300">Import layout JSON (HTTPS pack)
                      <div className="mt-1 flex gap-2">
                        <input className="input-field" value={layoutUrl} onChange={(e) => setLayoutUrl(e.target.value)} placeholder="https://example.com/layout.json" />
                        <button type="button" disabled={busy || !layoutUrl.startsWith("https://")} onClick={() => workflow("import_layout", { source_url: layoutUrl })} className="rounded-lg bg-sky-700 px-3 py-2 text-xs font-bold text-white">Import</button>
                      </div>
                    </label>
                  )}
                </div>
              )}
              <CMSFriendlyEditor resource={resource} json={json} setJson={setJson} />
              {resource === "pages" && selected.id && (
                <PageSectionBuilder pageId={selected.id} refreshKey={builderTick} onToast={showToast} />
              )}
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
          <div className="flex h-[90vh] w-full max-w-7xl flex-col rounded-2xl bg-slate-100 p-4">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <div className="mr-auto">
                <span className="text-[10px] uppercase font-black text-emerald-700">Preview as traveller</span>
                <h2 className="text-xl font-black text-slate-900">{preview.seo_title || displayName(preview)}</h2>
              </div>
              {[["live", "Live logged-out site"], ["draft", "Draft content"]].map(([id, label]) => (
                <button key={id} onClick={() => setPreviewKind(id)} className={`rounded-lg px-3 py-1 text-xs font-bold ${previewKind === id ? "bg-emerald-700 text-white" : "bg-white"}`}>{label}</button>
              ))}
              {[["desktop", "Desktop"], ["tablet", "Tablet"], ["mobile", "Mobile"]].map(([id, label]) => (
                <button key={id} onClick={() => setPreviewMode(id)} className={`rounded-lg px-2 py-1 text-xs font-bold ${previewMode === id ? "bg-slate-900 text-white" : "bg-white"}`}>{label}</button>
              ))}
              <button onClick={() => setPreview(null)}><FiX size={22} /></button>
            </div>
            <div className="flex min-h-0 flex-1 justify-center overflow-hidden">
              <div className={`overflow-hidden rounded-[1.5rem] border-8 border-slate-900 bg-white shadow-2xl ${previewMode === "mobile" ? "h-full w-[390px]" : previewMode === "tablet" ? "h-full w-[768px]" : "h-full w-full"}`}>
                {previewKind === "live" && preview.route ? (
                  <iframe title="Logged-out traveller preview" src={travellerPreviewSrc()} className="h-full w-full bg-white" />
                ) : (
                  <div className="h-full overflow-y-auto p-6 text-slate-900">
                    <p className="text-xs text-slate-500">Draft CMS content. Live site uses the published traveller page. Search visibility: {preview.search_visible === false ? "hidden" : "allowed"}.</p>
                    {preview.meta_description && <p className="mt-2 text-slate-500">{preview.meta_description}</p>}
                    {preview.og_image_url && <img src={preview.og_image_url} alt="" className="mt-4 max-h-48 w-full rounded-xl object-cover" />}
                    {preview.sections?.map(section => (
                      <article key={section.id} className="border-b py-6">
                        <p className="text-[10px] uppercase tracking-widest text-emerald-700">{section.section_type || "text"}</p>
                        <h3 className="text-xl font-bold">{section.title}</h3>
                        <p className="text-slate-500">{section.subtitle}</p>
                        {section.image_url && <img src={section.image_url} alt="" className="mt-3 max-h-56 w-full rounded-xl object-cover" />}
                        <div className="prose prose-sm mt-3" dangerouslySetInnerHTML={{ __html: section.body || "" }} />
                        {section.cta_text && <span className="mt-3 inline-block rounded-lg bg-emerald-700 px-4 py-2 text-white">{section.cta_text}</span>}
                      </article>
                    ))}
                    {!preview.sections && <div className="prose prose-sm mt-5" dangerouslySetInnerHTML={{ __html: preview.body || "" }} />}
                  </div>
                )}
              </div>
            </div>
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

function SectionConfigFields({ value, set }) {
  const config = value.config || {}
  const setConfig = (next) => set("config", { ...config, ...next })
  const type = value.section_type
  if (type === "form") {
    const fields = Array.isArray(config.fields) ? config.fields : []
    const updateField = (index, patch) => setConfig({ fields: fields.map((field, i) => i === index ? { ...field, ...patch } : field) })
    return (
      <div className="sm:col-span-2 space-y-2 rounded-xl border border-emerald-200 bg-white p-3">
        <p className="text-xs font-black text-emerald-800">Form fields (no code). Allowed: text, email, tel, textarea, select, checkbox.</p>
        {fields.map((field, index) => (
          <div key={index} className="grid gap-2 rounded-lg bg-emerald-50 p-2 sm:grid-cols-5">
            <input className="input-field" value={field.label || ""} onChange={(e) => updateField(index, { label: e.target.value })} placeholder="Label" />
            <input className="input-field" value={field.name || ""} onChange={(e) => updateField(index, { name: e.target.value })} placeholder="name" />
            <select className="input-field" value={field.field_type || "text"} onChange={(e) => updateField(index, { field_type: e.target.value })}>
              {["text", "email", "tel", "textarea", "select", "checkbox"].map((item) => <option key={item}>{item}</option>)}
            </select>
            <label className="flex items-center gap-2 text-xs font-bold"><input type="checkbox" checked={Boolean(field.required)} onChange={(e) => updateField(index, { required: e.target.checked })} /> Required</label>
            <button type="button" onClick={() => setConfig({ fields: fields.filter((_, i) => i !== index) })} className="rounded-lg bg-rose-100 text-xs font-bold text-rose-800">Remove</button>
            {field.field_type === "select" && (
              <input className="input-field sm:col-span-5" value={(field.options || []).join(", ")} onChange={(e) => updateField(index, { options: e.target.value.split(",").map((item) => item.trim()).filter(Boolean) })} placeholder="Select options, comma separated" />
            )}
          </div>
        ))}
        <button type="button" onClick={() => setConfig({ fields: [...fields, { name: `field_${fields.length + 1}`, label: "New field", field_type: "text", required: false }] })} className="rounded-lg bg-emerald-700 px-3 py-2 text-xs font-bold text-white">Add text field</button>
      </div>
    )
  }
  if (type === "table") {
    return (
      <div className="sm:col-span-2 grid gap-2 rounded-xl border border-emerald-200 bg-white p-3">
        <label className="text-xs font-semibold">Table headers (comma separated)
          <input className="input-field mt-1" value={(config.headers || []).join(", ")} onChange={(e) => setConfig({ headers: e.target.value.split(",").map((item) => item.trim()).filter(Boolean) })} />
        </label>
        <label className="text-xs font-semibold">Rows (one per line, cells separated by |)
          <textarea rows="4" className="input-field mt-1" value={(config.rows || []).map((row) => (Array.isArray(row) ? row : [row]).join(" | ")).join("\n")} onChange={(e) => setConfig({ rows: e.target.value.split("\n").map((line) => line.split("|").map((cell) => cell.trim())).filter((row) => row.some(Boolean)) })} />
        </label>
      </div>
    )
  }
  if (type === "breadcrumbs" || type === "testimonials") {
    const items = Array.isArray(config.items) ? config.items : []
    return (
      <label className="sm:col-span-2 text-xs font-semibold">{type === "breadcrumbs" ? "Breadcrumb labels (one per line)" : "Testimonial lines (one per line)"}
        <textarea rows="3" className="input-field mt-1" value={items.map((item) => item.label || item).join("\n")} onChange={(e) => setConfig({ items: e.target.value.split("\n").map((line) => line.trim()).filter(Boolean).map((label) => ({ label })) })} />
      </label>
    )
  }
  return null
}

function SeoSuite({ value }) {
  const title = value.seo_title || value.title || ""
  const description = value.meta_description || ""
  const checks = [
    [title.length >= 30 && title.length <= 60, `Title ${title.length}/60 characters`],
    [description.length >= 120 && description.length <= 160, `Description ${description.length}/160 characters`],
    [Boolean(value.og_image_url), "Social image set"],
    [value.search_visible !== false, "Visible to search engines"],
  ]
  return (
    <div className="sm:col-span-2 rounded-xl border border-emerald-200 bg-white p-3">
      <p className="text-xs font-black text-emerald-800">SEO checklist</p>
      <ul className="mt-2 grid gap-1 text-xs sm:grid-cols-2">
        {checks.map(([ok, label]) => (
          <li key={label} className={ok ? "text-emerald-700" : "text-amber-700"}>{ok ? "Ready" : "Needs work"} · {label}</li>
        ))}
      </ul>
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
    <label key={key} className="text-xs font-semibold text-slate-300">
      {label}
      {type === "textarea"
        ? <textarea rows="4" className="input-field mt-1" value={value[key] ?? ""} onChange={e => set(key, e.target.value)} />
        : type === "checkbox"
          ? <input type="checkbox" className="ml-3" checked={Boolean(value[key])} onChange={e => set(key, e.target.checked)} />
          : <input type={type} className="input-field mt-1" value={value[key] ?? ""} onChange={e => set(key, type === "number" ? Number(e.target.value) : e.target.value)} />}
    </label>
  )
  if (resource === "pages") return (
    <div className="grid gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 sm:grid-cols-2">
      {field("title", "Page title")}
      {field("seo_title", "SEO title")}
      {field("key", "Page key")}
      {field("route", "Page route")}
      {field("meta_description", "Search description", "textarea")}
      {field("og_image_url", "Social image URL")}
      <label className="text-xs font-semibold text-slate-300">Publication status
        <select className="input-field mt-1" value={value.status || "draft"} onChange={e => set("status", e.target.value)}>
          <option>draft</option><option>scheduled</option><option>published</option>
        </select>
      </label>
      {field("is_enabled", "Show this page", "checkbox")}
      {field("search_visible", "Allow search engines", "checkbox")}
      <SeoSuite value={value} />
    </div>
  )
  if (resource === "sections") return (
    <div className="space-y-4">
      <div className="grid gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 sm:grid-cols-2">
        {field("page_id", "Parent page ID", "number")}
        {field("key", "Section key")}
        {field("title", "Section title")}
        {field("subtitle", "Subtitle")}
        <label className="sm:col-span-2 text-xs font-semibold text-slate-300">Body content
          <RichTextEditor value={value.body || ""} onChange={html => set("body", html)} />
        </label>
        {field("image_url", "Image URL")}
        <label className="text-xs font-semibold text-slate-300">Media URL (HTTPS or /)
          <input className="input-field mt-1" value={value.config?.media_url || ""} onChange={e => set("config", { ...(value.config || {}), media_url: e.target.value })} />
        </label>
        <label className="text-xs font-semibold text-slate-300">Background Theme / Style
          <select className="input-field mt-1" value={value.config?.background_style || "clean-white"} onChange={e => set("config", { ...(value.config || {}), background_style: e.target.value })}>
            <option value="clean-white">Clean White (Standard Card)</option>
            <option value="gradient-emerald">Gradient Emerald (Himalayan Forest)</option>
            <option value="dark-slate">Dark Slate (Modern Dark Theme)</option>
            <option value="saffron-warm">Saffron Gold (Warm Cultural Accent)</option>
            <option value="hero-dark">Hero Dark (Cinematic Hero Banner)</option>
            <option value="border-accent">Border Accent (Gold Border Highlighting)</option>
          </select>
        </label>
        <label className="text-xs font-semibold text-slate-300">Padding & Spacing
          <select className="input-field mt-1" value={value.config?.padding_style || "medium"} onChange={e => set("config", { ...(value.config || {}), padding_style: e.target.value })}>
            <option value="compact">Compact (p-4)</option>
            <option value="medium">Medium (p-6)</option>
            <option value="spacious">Spacious (p-10)</option>
          </select>
        </label>
        <label className="text-xs font-semibold text-slate-300">Animation
          <select className="input-field mt-1" value={value.config?.effect || "none"} onChange={e => set("config", { ...(value.config || {}), effect: e.target.value })}>
            {["none", "marquee", "fade", "slide"].map(item => <option key={item}>{item}</option>)}
          </select>
        </label>
        <label className="text-xs font-semibold text-slate-300">Placement
          <select className="input-field mt-1" value={value.config?.placement || "main"} onChange={e => set("config", { ...(value.config || {}), placement: e.target.value })}>
            {["main", "hero", "sidebar", "footer"].map(item => <option key={item}>{item}</option>)}
          </select>
        </label>
        {field("cta_text", "Button text")}
        {field("cta_url", "Button route")}
        {field("icon", "Icon")}
        <SectionConfigFields value={value} set={set} />
        <label className="text-xs font-semibold text-slate-300">Section type
          <select className="input-field mt-1" value={value.section_type || "text"} onChange={e => set("section_type", e.target.value)}>
            {sectionTypes.map(type => <option key={type}>{type}</option>)}
          </select>
        </label>
        <label className="text-xs font-semibold text-slate-300">Layout Variant
          <select className="input-field mt-1" value={value.layout_variant || "default"} onChange={e => set("layout_variant", e.target.value)}>
            {["default", "compact", "wide", "cards", "hero", "split"].map(item => <option key={item}>{item}</option>)}
          </select>
        </label>
        {field("display_order", "Display order", "number")}
        {field("is_visible", "Visible on user page", "checkbox")}
        {field("is_reusable", "Reusable section", "checkbox")}
      </div>

      {/* Live Visual Section Preview */}
      <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
        <span className="text-[10px] font-black uppercase text-amber-400">Live Visual Section Preview</span>
        <div className="p-2">
          <CMSBlock section={value} />
        </div>
      </div>
    </div>
  )
  if (resource === "navigation") return <div className="grid gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 sm:grid-cols-2"><label className="text-xs font-semibold text-slate-300">Location<select className="input-field mt-1" value={value.location || "navbar"} onChange={e => set("location", e.target.value)}><option>navbar</option><option>sidebar</option><option>footer</option></select></label>{field("label", "Visible label")}{field("route", "Internal route")}{field("parent_id", "Parent item ID")}{field("icon", "Icon")}{field("display_order", "Display order", "number")}<label className="text-xs font-semibold text-slate-300">Allowed roles (comma separated)<input className="input-field mt-1" value={(value.allowed_roles || []).join(", ")} onChange={e => set("allowed_roles", e.target.value.split(",").map(x => x.trim()).filter(Boolean))} /></label>{field("is_active", "Active", "checkbox")}</div>
  if (resource === "translations") return <div className="grid gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 sm:grid-cols-2">{field("target_resource", "Target type")}{field("object_id", "Target record ID", "number")}{field("language_code", "Language code")}<label className="text-xs font-semibold text-slate-300">Translated fields<textarea rows="5" className="input-field mt-1 font-mono" value={JSON.stringify(value.content || {}, null, 2)} onChange={e => { try { set("content", JSON.parse(e.target.value)) } catch { /* keep until valid */ } }} /></label></div>
  return <div className="grid gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 sm:grid-cols-2">{field("key", "Setting key")}{field("description", "Description")}{field("is_public", "Public setting", "checkbox")}<label className="text-xs font-semibold text-slate-300">Structured value<textarea rows="6" className="input-field mt-1 font-mono" value={JSON.stringify(value.value || {}, null, 2)} onChange={e => { try { set("value", JSON.parse(e.target.value)) } catch { /* keep until valid */ } }} /></label></div>
}

function ContentBlocksBuilder({ sectionId, onToast }) {
  const [blocks, setBlocks] = useState([])
  const [loading, setLoading] = useState(false)
  const [editingBlock, setEditingBlock] = useState(null)
  const [showTypePicker, setShowTypePicker] = useState(false)

  const BLOCK_TYPES = [
    { type: "heading", label: "Heading", icon: "📌", desc: "H1, H2, H3 title heading" },
    { type: "subheading", label: "Subheading", icon: "✍️", desc: "Section subheading / tagline" },
    { type: "rich_text", label: "Rich Text", icon: "📝", desc: "Formatted rich HTML text" },
    { type: "image", label: "Image", icon: "🖼️", desc: "Single photo with caption & link" },
    { type: "gallery", label: "Image Gallery", icon: "🎨", desc: "Grid of multiple photography cards" },
    { type: "button", label: "Action Button", icon: "🔘", desc: "Call to action link button" },
    { type: "table", label: "Data Table", icon: "📊", desc: "Custom table with rows & columns" },
    { type: "video", label: "Video / Embed", icon: "🎥", desc: "YouTube / Vimeo embed" },
    { type: "map", label: "Interactive Map", icon: "🗺️", desc: "Coordinates & map pin" },
    { type: "destination_grid", label: "Destination Grid", icon: "🏔️", desc: "Live tourism destination cards" },
    { type: "hotel_grid", label: "Hotel Grid", icon: "🏨", desc: "Recommended hotels & lodges" },
    { type: "restaurant_grid", label: "Restaurant Grid", icon: "🍽️", desc: "Culinary & food spots" },
    { type: "statistics", label: "Statistics", icon: "📈", desc: "Key facts & metric numbers" },
    { type: "list", label: "List", icon: "📑", desc: "Bullet or numbered list items" },
    { type: "quote", label: "Quote", icon: "💬", desc: "Blockquote & citation" },
    { type: "alert", label: "Alert / Callout", icon: "⚠️", desc: "Notice, info or warning box" },
    { type: "divider", label: "Divider", icon: "➖", desc: "Horizontal section divider" },
    { type: "html", label: "Custom Safe HTML", icon: "💻", desc: "Sanitized HTML content" },
  ]

  const loadBlocks = async () => {
    if (!sectionId) return
    setLoading(true)
    try {
      const { data } = await adminApi.getSectionBlocks(sectionId)
      setBlocks(Array.isArray(data) ? data : [])
    } catch {
      setBlocks([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadBlocks() }, [sectionId])

  const addBlock = async (type) => {
    setShowTypePicker(false)
    try {
      const defaultData = {
        heading: { text: "New Heading", level: "h2", align: "left" },
        subheading: { text: "New Subheading", align: "left" },
        rich_text: { html: "<p>Write rich text content here...</p>" },
        image: { url: "/images/destinations/pokhara/fewatal.jpg", caption: "Photo caption", alt: "Photo" },
        gallery: { images: [{ url: "/images/destinations/pokhara/fewatal.jpg", caption: "Phewa Lake" }] },
        button: { label: "Explore Now", url: "/destinations", target: "_self", style: "primary" },
        table: { columns: ["Location", "District", "Altitude"], rows: [["Pokhara", "Kaski", "822m"], ["Kathmandu", "Kathmandu", "1400m"]] },
        video: { url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ", title: "Nepal Video Tour" },
        map: { latitude: 28.2096, longitude: 83.9856, zoom: 13, title: "Pokhara Lakeside" },
        statistics: { items: [{ number: "8,000+", label: "Himalayan Peaks" }, { number: "100+", label: "Attractions" }] },
        alert: { variant: "info", title: "Travel Notice", body: "Check weather forecast before trekking." },
        quote: { quote: "Nepal is not just a destination; it's a spiritual experience.", author: "Himalayan Guide" },
        list: { ordered: false, items: ["Verified Trail Routes", "Local Teahouse Stays", "Licensed Guides"] },
      }[type] || {}

      const { data } = await adminApi.createContentBlock(sectionId, {
        block_type: type,
        title: `New ${type.replace("_", " ")}`,
        data: defaultData,
        position: blocks.length,
      })
      onToast?.("Content block added", "success")
      loadBlocks()
      setEditingBlock(data)
    } catch (err) {
      onToast?.(err.response?.data?.detail || "Could not add block", "error")
    }
  }

  const saveBlock = async (block) => {
    try {
      await adminApi.updateContentBlock(block.id, block)
      onToast?.("Block updated!", "success")
      setEditingBlock(null)
      loadBlocks()
    } catch (err) {
      onToast?.(err.response?.data?.detail || "Could not save block", "error")
    }
  }

  const removeBlock = async (id) => {
    if (!window.confirm("Delete this content block?")) return
    try {
      await adminApi.deleteContentBlock(id)
      onToast?.("Block deleted", "success")
      loadBlocks()
    } catch {
      onToast?.("Could not delete block", "error")
    }
  }

  const moveBlock = (index, dir) => {
    const target = index + dir
    if (target < 0 || target >= blocks.length) return
    const copy = blocks.slice()
    const [moved] = copy.splice(index, 1)
    copy.splice(target, 0, moved)
    setBlocks(copy)
    adminApi.reorderContentBlocks({ items: copy.map((b, idx) => ({ id: b.id, position: idx })) })
  }

  return (
    <div className="space-y-3 rounded-2xl bg-slate-950 p-4 text-white border border-slate-800">
      <div className="flex justify-between items-center border-b border-slate-800 pb-2">
        <div>
          <h4 className="font-extrabold text-sm text-amber-400">Content Blocks Builder ({blocks.length})</h4>
          <p className="text-[11px] text-slate-400">Add, arrange, and edit rich structured content blocks inside this section.</p>
        </div>
        <button
          type="button"
          onClick={() => setShowTypePicker(!showTypePicker)}
          className="px-3 py-1.5 rounded-xl bg-amber-400 text-slate-950 font-black text-xs shadow hover:bg-amber-300"
        >
          {showTypePicker ? "Close Block Picker" : "+ Add Content Block"}
        </button>
      </div>

      {/* TYPE PICKER MODAL / GRID */}
      {showTypePicker && (
        <div className="p-3 rounded-2xl bg-slate-900 border border-slate-700 space-y-2">
          <p className="text-xs font-bold text-amber-300">Choose a Content Block Type to insert:</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
            {BLOCK_TYPES.map((bt) => (
              <button
                key={bt.type}
                type="button"
                onClick={() => addBlock(bt.type)}
                className="p-2.5 rounded-xl bg-slate-800 hover:bg-emerald-900 border border-slate-700 text-left transition space-y-1 group"
              >
                <div className="flex items-center gap-1.5">
                  <span>{bt.icon}</span>
                  <span className="font-extrabold text-xs text-white group-hover:text-amber-300">{bt.label}</span>
                </div>
                <p className="text-[10px] text-slate-400 line-clamp-2">{bt.desc}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* BLOCK LIST */}
      {loading ? (
        <p className="text-xs text-slate-400">Loading blocks…</p>
      ) : !blocks.length ? (
        <div className="p-4 rounded-xl border border-dashed border-slate-800 text-center text-xs text-slate-500">
          No content blocks added yet. Click <b>"+ Add Content Block"</b> above to build headings, rich text, images, tables, videos, and destination cards.
        </div>
      ) : (
        <div className="space-y-2">
          {blocks.map((b, idx) => (
            <div key={b.id} className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between gap-2 text-xs">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-amber-300 text-[10px] font-black uppercase">
                    {b.block_type}
                  </span>
                  <span className="font-bold text-white truncate max-w-xs">{b.title || b.data?.text || b.data?.label || `Block #${b.id}`}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <button type="button" onClick={() => moveBlock(idx, -1)} disabled={idx === 0} className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-30">↑</button>
                  <button type="button" onClick={() => moveBlock(idx, 1)} disabled={idx === blocks.length - 1} className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-30">↓</button>
                  <button type="button" onClick={() => setEditingBlock(editingBlock?.id === b.id ? null : { ...b })} className="px-2.5 py-1 rounded bg-amber-400 text-slate-950 font-bold hover:bg-amber-300">
                    {editingBlock?.id === b.id ? "Close" : "Edit"}
                  </button>
                  <button type="button" onClick={() => removeBlock(b.id)} className="px-2 py-1 rounded bg-rose-950 text-rose-300 hover:bg-rose-900 font-bold">Delete</button>
                </div>
              </div>

              {/* EDIT BLOCK FORM */}
              {editingBlock?.id === b.id && (
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-700 space-y-3 text-xs">
                  <div className="grid sm:grid-cols-2 gap-2">
                    <label className="block font-semibold text-slate-300">Block Title
                      <input className="input-field mt-1 bg-slate-900 text-white border-slate-700" value={editingBlock.title || ""} onChange={(e) => setEditingBlock({ ...editingBlock, title: e.target.value })} />
                    </label>
                    <label className="flex items-center gap-2 mt-5 font-semibold text-slate-300">
                      <input type="checkbox" checked={editingBlock.is_visible !== false} onChange={(e) => setEditingBlock({ ...editingBlock, is_visible: e.target.checked })} />
                      Visible on page
                    </label>
                  </div>

                  {/* TAILORED DATA FIELDS BY BLOCK TYPE */}
                  {editingBlock.block_type === "heading" && (
                    <div className="grid sm:grid-cols-3 gap-2">
                      <label className="block font-semibold text-slate-300">Heading Text
                        <input className="input-field mt-1 bg-slate-900 text-white border-slate-700" value={editingBlock.data?.text || ""} onChange={(e) => setEditingBlock({ ...editingBlock, data: { ...editingBlock.data, text: e.target.value } })} />
                      </label>
                      <label className="block font-semibold text-slate-300">Heading Level
                        <select className="input-field mt-1 bg-slate-900 text-white border-slate-700" value={editingBlock.data?.level || "h2"} onChange={(e) => setEditingBlock({ ...editingBlock, data: { ...editingBlock.data, level: e.target.value } })}>
                          <option value="h1">H1 (Main Title)</option>
                          <option value="h2">H2 (Section Heading)</option>
                          <option value="h3">H3 (Subheading)</option>
                          <option value="h4">H4 (Minor Heading)</option>
                        </select>
                      </label>
                      <label className="block font-semibold text-slate-300">Alignment
                        <select className="input-field mt-1 bg-slate-900 text-white border-slate-700" value={editingBlock.data?.align || "left"} onChange={(e) => setEditingBlock({ ...editingBlock, data: { ...editingBlock.data, align: e.target.value } })}>
                          <option value="left">Left</option>
                          <option value="center">Center</option>
                          <option value="right">Right</option>
                        </select>
                      </label>
                    </div>
                  )}

                  {editingBlock.block_type === "rich_text" && (
                    <label className="block font-semibold text-slate-300">Rich Text Body
                      <RichTextEditor value={editingBlock.data?.html || editingBlock.data?.text || ""} onChange={(html) => setEditingBlock({ ...editingBlock, data: { ...editingBlock.data, html } })} />
                    </label>
                  )}

                  {editingBlock.block_type === "image" && (
                    <div className="grid sm:grid-cols-2 gap-2">
                      <label className="block font-semibold text-slate-300">Image URL
                        <input className="input-field mt-1 bg-slate-900 text-white border-slate-700" value={editingBlock.data?.url || ""} onChange={(e) => setEditingBlock({ ...editingBlock, data: { ...editingBlock.data, url: e.target.value } })} placeholder="/images/... or https://..." />
                      </label>
                      <label className="block font-semibold text-slate-300">Caption
                        <input className="input-field mt-1 bg-slate-900 text-white border-slate-700" value={editingBlock.data?.caption || ""} onChange={(e) => setEditingBlock({ ...editingBlock, data: { ...editingBlock.data, caption: e.target.value } })} />
                      </label>
                      <label className="block font-semibold text-slate-300">Alt Text
                        <input className="input-field mt-1 bg-slate-900 text-white border-slate-700" value={editingBlock.data?.alt || ""} onChange={(e) => setEditingBlock({ ...editingBlock, data: { ...editingBlock.data, alt: e.target.value } })} />
                      </label>
                      <label className="block font-semibold text-slate-300">Link URL (optional)
                        <input className="input-field mt-1 bg-slate-900 text-white border-slate-700" value={editingBlock.data?.link || ""} onChange={(e) => setEditingBlock({ ...editingBlock, data: { ...editingBlock.data, link: e.target.value } })} />
                      </label>
                    </div>
                  )}

                  {editingBlock.block_type === "button" && (
                    <div className="grid sm:grid-cols-3 gap-2">
                      <label className="block font-semibold text-slate-300">Button Label
                        <input className="input-field mt-1 bg-slate-900 text-white border-slate-700" value={editingBlock.data?.label || ""} onChange={(e) => setEditingBlock({ ...editingBlock, data: { ...editingBlock.data, label: e.target.value } })} />
                      </label>
                      <label className="block font-semibold text-slate-300">Destination Route / URL
                        <input className="input-field mt-1 bg-slate-900 text-white border-slate-700" value={editingBlock.data?.url || ""} onChange={(e) => setEditingBlock({ ...editingBlock, data: { ...editingBlock.data, url: e.target.value } })} />
                      </label>
                      <label className="block font-semibold text-slate-300">Button Style
                        <select className="input-field mt-1 bg-slate-900 text-white border-slate-700" value={editingBlock.data?.style || "primary"} onChange={(e) => setEditingBlock({ ...editingBlock, data: { ...editingBlock.data, style: e.target.value } })}>
                          <option value="primary">Primary Emerald</option>
                          <option value="gold">Saffron Gold</option>
                          <option value="outline">Outline</option>
                        </select>
                      </label>
                    </div>
                  )}

                  {editingBlock.block_type === "table" && (
                    <div className="space-y-2">
                      <p className="font-bold text-amber-300">Table Data Builder</p>
                      <label className="block font-semibold text-slate-300">Columns (comma separated)
                        <input className="input-field mt-1 bg-slate-900 text-white border-slate-700" value={(editingBlock.data?.columns || []).join(", ")} onChange={(e) => setEditingBlock({ ...editingBlock, data: { ...editingBlock.data, columns: e.target.value.split(",").map(x => x.trim()).filter(Boolean) } })} />
                      </label>
                      <label className="block font-semibold text-slate-300">Rows JSON (array of arrays)
                        <textarea rows="4" className="input-field mt-1 font-mono bg-slate-900 text-white border-slate-700" value={JSON.stringify(editingBlock.data?.rows || [], null, 2)} onChange={(e) => { try { setEditingBlock({ ...editingBlock, data: { ...editingBlock.data, rows: JSON.parse(e.target.value) } }) } catch { /* keep */ } }} />
                      </label>
                    </div>
                  )}

                  {editingBlock.block_type === "video" && (
                    <div className="grid sm:grid-cols-2 gap-2">
                      <label className="block font-semibold text-slate-300">YouTube / Vimeo Embed URL
                        <input className="input-field mt-1 bg-slate-900 text-white border-slate-700" value={editingBlock.data?.url || ""} onChange={(e) => setEditingBlock({ ...editingBlock, data: { ...editingBlock.data, url: e.target.value } })} placeholder="https://www.youtube.com/watch?v=..." />
                      </label>
                      <label className="block font-semibold text-slate-300">Video Title
                        <input className="input-field mt-1 bg-slate-900 text-white border-slate-700" value={editingBlock.data?.title || ""} onChange={(e) => setEditingBlock({ ...editingBlock, data: { ...editingBlock.data, title: e.target.value } })} />
                      </label>
                    </div>
                  )}

                  {editingBlock.block_type === "alert" && (
                    <div className="grid sm:grid-cols-3 gap-2">
                      <label className="block font-semibold text-slate-300">Alert Variant
                        <select className="input-field mt-1 bg-slate-900 text-white border-slate-700" value={editingBlock.data?.variant || "info"} onChange={(e) => setEditingBlock({ ...editingBlock, data: { ...editingBlock.data, variant: e.target.value } })}>
                          <option value="info">Info (Blue)</option>
                          <option value="warning">Warning (Gold)</option>
                          <option value="danger">Danger (Red)</option>
                          <option value="success">Success (Emerald)</option>
                        </select>
                      </label>
                      <label className="block font-semibold text-slate-300">Alert Title
                        <input className="input-field mt-1 bg-slate-900 text-white border-slate-700" value={editingBlock.data?.title || ""} onChange={(e) => setEditingBlock({ ...editingBlock, data: { ...editingBlock.data, title: e.target.value } })} />
                      </label>
                      <label className="block font-semibold text-slate-300">Alert Message Body
                        <input className="input-field mt-1 bg-slate-900 text-white border-slate-700" value={editingBlock.data?.body || ""} onChange={(e) => setEditingBlock({ ...editingBlock, data: { ...editingBlock.data, body: e.target.value } })} />
                      </label>
                    </div>
                  )}

                  <div className="flex gap-2 justify-end pt-2 border-t border-slate-800">
                    <button type="button" onClick={() => setEditingBlock(null)} className="px-3 py-1.5 rounded bg-slate-800 text-slate-300 font-bold">Cancel</button>
                    <button type="button" onClick={() => saveBlock(editingBlock)} className="px-4 py-1.5 rounded bg-emerald-600 text-white font-black shadow hover:bg-emerald-500">Save Block</button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function PageSectionBuilder({ pageId, refreshKey, onToast }) {
  const [sections, setSections] = useState([])
  const [openId, setOpenId] = useState(null)
  const [draft, setDraft] = useState(null)
  const [previewId, setPreviewId] = useState(null)
  const dragFrom = useRef(null)

  const loadSections = async () => {
    try {
      const { data } = await adminApi.getCMS("sections", { page_id: pageId })
      setSections((data.results || []).slice().sort((a, b) => (a.display_order || 0) - (b.display_order || 0) || a.id - b.id))
    } catch {
      onToast("Could not load page sections", "error")
    }
  }

  useEffect(() => { loadSections() }, [pageId, refreshKey])

  const persist = async (next) => {
    setSections(next)
    try {
      await adminApi.runCMSAction({ resource: "pages", id: pageId, action: "reorder", section_ids: next.map(section => section.id) })
    } catch (error) {
      onToast(error.response?.data?.detail || "Could not save section order", "error")
      loadSections()
    }
  }

  const move = (index, direction) => {
    const target = index + direction
    if (target < 0 || target >= sections.length) return
    const next = sections.slice()
    const [item] = next.splice(index, 1)
    next.splice(target, 0, item)
    persist(next)
  }

  const onDrop = (index) => {
    const from = dragFrom.current
    dragFrom.current = null
    if (from == null || from === index) return
    const next = sections.slice()
    const [item] = next.splice(from, 1)
    next.splice(index, 0, item)
    persist(next)
  }

  const saveSection = async () => {
    if (!draft?.id) return
    try {
      await adminApi.updateCMS({
        resource: "sections",
        id: draft.id,
        ...draft,
        status: "published",
        is_visible: Boolean(draft.is_visible),
      })
      window.dispatchEvent(new Event("cms-updated"))
      onToast("Section saved & published live!", "success")
      setOpenId(null)
      setDraft(null)
      loadSections()
    } catch (error) {
      onToast(error.response?.data?.detail || "Could not save section", "error")
    }
  }

  const addSection = async () => {
    try {
      await adminApi.createCMS({
        resource: "sections", page_id: pageId, key: `block-${Date.now()}`,
        title: "New section", body: "Edit this block.", section_type: "text",
        display_order: (sections[sections.length - 1]?.display_order || 0) + 10,
        is_visible: true, status: "published",
      })
      onToast("Section added", "success")
      loadSections()
    } catch (error) {
      onToast(error.response?.data?.detail || "Could not add section", "error")
    }
  }

  return (
    <div className="rounded-xl border border-emerald-200 bg-white p-3">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs font-black text-emerald-800">All sections on this page ({sections.length})</p>
        <div className="flex gap-2">
          <button type="button" onClick={addSection} className="rounded-lg bg-emerald-700 px-3 py-1 text-xs font-bold text-white">Add section</button>
          <p className="self-center text-[10px] text-slate-500">Edit, preview, drag or use arrows.</p>
        </div>
      </div>
      {!sections.length && <p className="rounded-xl border border-dashed border-emerald-200 p-4 text-xs text-slate-500">No sections yet. Choose a template, add a reusable block, or add a section.</p>}
      <div className="space-y-2">
        {sections.map((section, index) => (
          <div key={section.id} className="rounded-xl border border-emerald-100 bg-emerald-50 p-3 text-xs">
            <div
              draggable
              onDragStart={() => { dragFrom.current = index }}
              onDragOver={(event) => event.preventDefault()}
              onDrop={() => onDrop(index)}
              className="flex cursor-grab items-center gap-3"
            >
              <span className="font-black text-emerald-800">{index + 1}</span>
              <div className="min-w-0 flex-1">
                <p className="truncate font-bold">{section.title || section.key}</p>
                <p className="text-[10px] uppercase tracking-widest text-slate-500">{section.key} · {section.section_type || "text"} · {section.status}{section.is_visible === false ? " · hidden" : ""}</p>
              </div>
              <button type="button" onClick={() => setPreviewId(previewId === section.id ? null : section.id)} className="rounded bg-white px-2 py-1 font-bold">Preview</button>
              <button type="button" onClick={() => { setOpenId(openId === section.id ? null : section.id); setDraft({ ...section }) }} className="rounded bg-white px-2 py-1 font-bold">Edit</button>
              <button type="button" onClick={() => move(index, -1)} className="rounded bg-white px-2 py-1 font-bold" aria-label="Move up">↑</button>
              <button type="button" onClick={() => move(index, 1)} className="rounded bg-white px-2 py-1 font-bold" aria-label="Move down">↓</button>
            </div>
            {previewId === section.id && (
              <article className="mt-3 rounded-lg bg-white p-3">
                <h4 className="text-base font-black">{section.title}</h4>
                <p className="text-slate-500">{section.subtitle}</p>
                {section.image_url && <img src={section.image_url} alt="" className="mt-2 max-h-40 w-full rounded-lg object-cover" />}
                <div className="prose prose-sm mt-2" dangerouslySetInnerHTML={{ __html: section.body || "" }} />
              </article>
            )}
            {openId === section.id && draft && (
              <div className="mt-3 grid gap-2 rounded-lg bg-slate-900 text-white p-3 sm:grid-cols-2">
                <label className="font-semibold text-slate-300">Title<input className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.title || ""} onChange={(e) => setDraft({ ...draft, title: e.target.value })} /></label>
                <label className="font-semibold text-slate-300">Key<input className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.key || ""} onChange={(e) => setDraft({ ...draft, key: e.target.value })} /></label>
                <label className="font-semibold text-slate-300">Subtitle<input className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.subtitle || ""} onChange={(e) => setDraft({ ...draft, subtitle: e.target.value })} /></label>
                <label className="font-semibold text-slate-300">Image / media URL<input className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.image_url || ""} onChange={(e) => setDraft({ ...draft, image_url: e.target.value })} /></label>
                <label className="font-semibold text-slate-300">Button Text (CTA)<input className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.cta_text || ""} onChange={(e) => setDraft({ ...draft, cta_text: e.target.value })} placeholder="e.g. Explore Now" /></label>
                <label className="font-semibold text-slate-300">Button Link Route<input className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.cta_url || ""} onChange={(e) => setDraft({ ...draft, cta_url: e.target.value })} placeholder="/destinations" /></label>
                <label className="font-semibold text-slate-300">Background Theme / Style
                  <select className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.config?.background_style || "clean-white"} onChange={(e) => setDraft({ ...draft, config: { ...(draft.config || {}), background_style: e.target.value } })}>
                    <option value="clean-white">Clean White (Standard Card)</option>
                    <option value="gradient-emerald">Gradient Emerald (Himalayan Forest)</option>
                    <option value="dark-slate">Dark Slate (Modern Dark Theme)</option>
                    <option value="saffron-warm">Saffron Gold (Warm Cultural Accent)</option>
                    <option value="hero-dark">Hero Dark (Cinematic Hero Banner)</option>
                    <option value="border-accent">Border Accent (Gold Border Highlighting)</option>
                  </select>
                </label>
                <label className="font-semibold text-slate-300">Padding & Spacing
                  <select className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.config?.padding_style || "medium"} onChange={(e) => setDraft({ ...draft, config: { ...(draft.config || {}), padding_style: e.target.value } })}>
                    <option value="compact">Compact (p-4)</option>
                    <option value="medium">Medium (p-6)</option>
                    <option value="spacious">Spacious (p-10)</option>
                  </select>
                </label>
                <label className="font-semibold text-slate-300">Section type
                  <select className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.section_type || "text"} onChange={(e) => setDraft({ ...draft, section_type: e.target.value })}>
                    {sectionTypes.map((type) => <option key={type}>{type}</option>)}
                  </select>
                </label>
                <label className="font-semibold text-slate-300">Layout Variant
                  <select className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.layout_variant || "default"} onChange={(e) => setDraft({ ...draft, layout_variant: e.target.value })}>
                    {["default", "compact", "wide", "cards", "hero", "split"].map((item) => <option key={item}>{item}</option>)}
                  </select>
                </label>
                <label className="sm:col-span-2 font-semibold text-slate-300">Body Content
                  <RichTextEditor value={draft.body || ""} onChange={(html) => setDraft({ ...draft, body: html })} />
                </label>
                <div className="sm:col-span-2 mt-2">
                  <ContentBlocksBuilder sectionId={draft.id} onToast={onToast} />
                </div>
                <label className="flex items-center gap-2 font-semibold text-slate-300"><input type="checkbox" checked={Boolean(draft.is_visible)} onChange={(e) => setDraft({ ...draft, is_visible: e.target.checked })} /> Visible on traveller page</label>
                <div className="flex gap-2 self-end">
                  <button type="button" onClick={saveSection} className="rounded-lg bg-amber-400 text-slate-950 font-black px-4 py-2 text-xs shadow">Save & Publish Section</button>
                  <button type="button" onClick={() => { setOpenId(null); setDraft(null) }} className="rounded-lg bg-slate-800 text-slate-300 px-3 py-2 text-xs font-bold">Cancel</button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
