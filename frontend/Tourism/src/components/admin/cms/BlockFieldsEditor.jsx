// Structured, no-JSON editors for CMS content blocks. Field names match the
// public renderer (components/cms/CMSBlock.jsx -> ContentBlockItem) and the
// server-side checks in views_admin._validate_block_data, so what an editor
// types is exactly what travellers get. Each editor also reports problems
// inline (via blockIssues) before the admin presses Save.

const input = "input-field mt-1 bg-slate-900 text-white border-slate-700"
const small = "rounded bg-slate-800 px-2 py-0.5 text-[11px] font-bold hover:bg-slate-700 disabled:opacity-30"

const isSiteOrHttps = (v) => !v || v.startsWith("https://") || v.startsWith("/")

export function blockIssues(block) {
  const d = block?.data || {}
  const out = []
  switch (block?.block_type) {
    case "gallery":
      ;(d.images || []).forEach((img, i) => {
        const url = typeof img === "string" ? img : img?.url
        if (!url) out.push(`Image ${i + 1} has no URL.`)
        else if (!isSiteOrHttps(url)) out.push(`Image ${i + 1} must be an HTTPS URL or a site path starting with /.`)
        else if (!(typeof img === "string" ? "" : img.alt)) out.push(`Image ${i + 1} has no alt text (needed for screen readers).`)
      })
      break
    case "card_grid":
      ;(d.items || []).forEach((c, i) => {
        if (!String(c?.title || "").trim()) out.push(`Card ${i + 1} needs a title.`)
        if (c?.url && !c.url.startsWith("/")) out.push(`Card ${i + 1}: links must be internal routes starting with /.`)
        if (c?.image && !isSiteOrHttps(c.image)) out.push(`Card ${i + 1}: image must be HTTPS or a site path.`)
      })
      break
    case "map": {
      const lat = Number(d.latitude)
      const lng = Number(d.longitude)
      if (d.latitude === undefined || d.latitude === "" || Number.isNaN(lat) || lat < -90 || lat > 90) out.push("Latitude must be a number between -90 and 90.")
      if (d.longitude === undefined || d.longitude === "" || Number.isNaN(lng) || lng < -180 || lng > 180) out.push("Longitude must be a number between -180 and 180.")
      if (!Number.isNaN(lat) && !Number.isNaN(lng) && (lat < 26.3 || lat > 30.5 || lng < 80 || lng > 88.3)) out.push("These coordinates are outside Nepal. Check them before saving.")
      break
    }
    case "statistics":
      ;(d.items || []).forEach((s, i) => { if (!String(s?.number || "").trim() || !String(s?.label || "").trim()) out.push(`Statistic ${i + 1} needs both a number and a label.`) })
      if ((d.items || []).length) out.push("Statistics are published as facts. Only use figures you can source.")
      break
    case "table":
      ;(d.rows || []).forEach((r, i) => { if ((d.columns || []).length && r.length !== d.columns.length) out.push(`Row ${i + 1} has ${r.length} cells but there are ${d.columns.length} columns.`) })
      break
    case "html":
      if (/<script|on\w+=|javascript:/i.test(d.html || "")) out.push("Scripts and inline event handlers are removed when this block is saved.")
      break
    default:
  }
  return out
}

function RowControls({ index, count, move, remove }) {
  return (
    <span className="flex shrink-0 gap-1">
      <button type="button" className={small} onClick={() => move(index, -1)} disabled={index === 0} aria-label="Move up">↑</button>
      <button type="button" className={small} onClick={() => move(index, 1)} disabled={index === count - 1} aria-label="Move down">↓</button>
      <button type="button" className={`${small} text-rose-300`} onClick={() => remove(index)} aria-label="Remove">✕</button>
    </span>
  )
}

/** Generic editable list of objects with add / move / remove. */
function RowList({ label, rows, fields, onChange, addLabel, empty }) {
  const list = Array.isArray(rows) ? rows : []
  const update = (i, patch) => onChange(list.map((r, idx) => (idx === i ? { ...r, ...patch } : r)))
  const move = (i, dir) => {
    const j = i + dir
    if (j < 0 || j >= list.length) return
    const copy = list.slice()
    ;[copy[i], copy[j]] = [copy[j], copy[i]]
    onChange(copy)
  }
  const remove = (i) => onChange(list.filter((_, idx) => idx !== i))
  return (
    <div className="space-y-2">
      <p className="font-bold text-amber-300">{label}</p>
      {!list.length && <p className="text-slate-500">{empty}</p>}
      {list.map((row, i) => (
        <div key={i} className="rounded-lg border border-slate-800 bg-slate-900/60 p-2">
          <div className="mb-1 flex items-center justify-between"><span className="text-[11px] font-bold text-slate-400">#{i + 1}</span><RowControls index={i} count={list.length} move={move} remove={remove} /></div>
          <div className="grid gap-2 sm:grid-cols-2">
            {fields.map((f) => (
              <label key={f.key} className={`block font-semibold text-slate-300 ${f.wide ? "sm:col-span-2" : ""}`}>{f.label}
                {f.type === "textarea"
                  ? <textarea rows="2" className={input} value={row[f.key] ?? ""} onChange={(e) => update(i, { [f.key]: e.target.value })} placeholder={f.placeholder} />
                  : <input className={input} value={row[f.key] ?? ""} onChange={(e) => update(i, { [f.key]: e.target.value })} placeholder={f.placeholder} />}
              </label>
            ))}
          </div>
        </div>
      ))}
      <button type="button" className="rounded bg-slate-800 px-3 py-1 font-bold text-amber-300 hover:bg-slate-700" onClick={() => onChange([...list, {}])}>+ {addLabel}</button>
    </div>
  )
}

function TableEditor({ data, setData }) {
  const columns = Array.isArray(data.columns) ? data.columns : []
  const rows = Array.isArray(data.rows) ? data.rows : []
  const setCols = (next) => setData({ columns: next, rows: rows.map((r) => next.map((_, i) => r[i] ?? "")) })
  const setCell = (ri, ci, value) => setData({ rows: rows.map((r, i) => (i === ri ? columns.map((_, c) => (c === ci ? value : r[c] ?? "")) : r)) })
  return (
    <div className="space-y-2">
      <p className="font-bold text-amber-300">Table</p>
      <div className="flex flex-wrap items-end gap-2">
        {columns.map((col, ci) => (
          <label key={ci} className="font-semibold text-slate-300">Column {ci + 1}
            <span className="flex gap-1"><input className={input} value={col} onChange={(e) => setCols(columns.map((c, i) => (i === ci ? e.target.value : c)))} />
              <button type="button" className={`${small} mt-1 text-rose-300`} onClick={() => setCols(columns.filter((_, i) => i !== ci))} aria-label={`Remove column ${ci + 1}`}>✕</button></span>
          </label>
        ))}
        <button type="button" className="rounded bg-slate-800 px-3 py-1.5 font-bold text-amber-300" onClick={() => setCols([...columns, `Column ${columns.length + 1}`])}>+ Column</button>
      </div>
      {columns.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead><tr>{columns.map((c, i) => <th key={i} className="px-1 py-1 text-[11px] text-slate-400">{c || `Column ${i + 1}`}</th>)}<th /></tr></thead>
            <tbody>
              {rows.map((r, ri) => (
                <tr key={ri}>
                  {columns.map((_, ci) => <td key={ci} className="px-1 py-0.5"><input className="input-field bg-slate-900 text-white border-slate-700 py-1" value={r[ci] ?? ""} onChange={(e) => setCell(ri, ci, e.target.value)} aria-label={`Row ${ri + 1}, ${columns[ci] || `column ${ci + 1}`}`} /></td>)}
                  <td><button type="button" className={`${small} text-rose-300`} onClick={() => setData({ rows: rows.filter((_, i) => i !== ri) })} aria-label={`Remove row ${ri + 1}`}>✕</button></td>
                </tr>
              ))}
            </tbody>
          </table>
          <button type="button" className="mt-1 rounded bg-slate-800 px-3 py-1 font-bold text-amber-300" onClick={() => setData({ rows: [...rows, columns.map(() => "")] })}>+ Row</button>
        </div>
      )}
    </div>
  )
}

function GridFilters({ type, data, setData }) {
  const limit = Number(data.limit) || 6
  return (
    <div className="grid gap-2 sm:grid-cols-3">
      {type === "destination_grid" ? (
        <>
          <label className="block font-semibold text-slate-300">District (exact name)
            <input className={input} value={data.district || ""} onChange={(e) => setData({ district: e.target.value })} placeholder="e.g. Kaski" /></label>
          <label className="block font-semibold text-slate-300">Name contains
            <input className={input} value={data.search || ""} onChange={(e) => setData({ search: e.target.value })} placeholder="e.g. lake" /></label>
        </>
      ) : (
        <label className="block font-semibold text-slate-300 sm:col-span-2">Name or address contains
          <input className={input} value={data.search || ""} onChange={(e) => setData({ search: e.target.value })} placeholder="e.g. Pokhara" /></label>
      )}
      <label className="block font-semibold text-slate-300">How many (1–12)
        <input type="number" min="1" max="12" className={input} value={limit} onChange={(e) => setData({ limit: Math.min(12, Math.max(1, parseInt(e.target.value || "6", 10))) })} /></label>
      <p className="sm:col-span-3 text-[11px] text-slate-400">Shows live published records only. Unverified hotels and restaurants are labelled as unverified. If nothing matches, travellers see nothing, and the preview below will tell you.</p>
    </div>
  )
}

/**
 * Editors for block types that previously had no form (or only raw JSON).
 * Returns null for types edited elsewhere in the builder.
 */
export default function BlockFieldsEditor({ block, onChange }) {
  const data = block.data || {}
  const setData = (patch) => onChange({ ...block, data: { ...data, ...patch } })
  switch (block.block_type) {
    case "subheading":
      return (
        <div className="grid gap-2 sm:grid-cols-2">
          <label className="block font-semibold text-slate-300">Text<input className={input} value={data.text || ""} onChange={(e) => setData({ text: e.target.value })} /></label>
          <label className="block font-semibold text-slate-300">Alignment
            <select className={input} value={data.align || "left"} onChange={(e) => setData({ align: e.target.value })}>{["left", "center", "right"].map((a) => <option key={a}>{a}</option>)}</select></label>
          <p className="sm:col-span-2 text-[11px] text-slate-400">The block title, if set, is shown instead of this text.</p>
        </div>
      )
    case "gallery":
      return (
        <RowList label="Gallery images" rows={(data.images || []).map((img) => (typeof img === "string" ? { url: img } : img))}
          onChange={(images) => setData({ images })} addLabel="Image" empty="No images yet."
          fields={[{ key: "url", label: "Image URL (HTTPS or /media/…)", wide: true }, { key: "alt", label: "Alt text" }, { key: "caption", label: "Caption" }]} />
      )
    case "map":
      return (
        <div className="grid gap-2 sm:grid-cols-4">
          <label className="block font-semibold text-slate-300">Latitude<input className={input} inputMode="decimal" value={data.latitude ?? ""} onChange={(e) => setData({ latitude: e.target.value === "" ? "" : Number(e.target.value) })} placeholder="27.7172" /></label>
          <label className="block font-semibold text-slate-300">Longitude<input className={input} inputMode="decimal" value={data.longitude ?? ""} onChange={(e) => setData({ longitude: e.target.value === "" ? "" : Number(e.target.value) })} placeholder="85.3240" /></label>
          <label className="block font-semibold text-slate-300">Zoom (1–19)<input type="number" min="1" max="19" className={input} value={data.zoom ?? 12} onChange={(e) => setData({ zoom: Math.min(19, Math.max(1, parseInt(e.target.value || "12", 10))) })} /></label>
          <label className="block font-semibold text-slate-300">Label<input className={input} value={data.title || ""} onChange={(e) => setData({ title: e.target.value })} /></label>
          <label className="block font-semibold text-slate-300 sm:col-span-4">Description<input className={input} value={data.description || ""} onChange={(e) => setData({ description: e.target.value })} /></label>
        </div>
      )
    case "destination_grid":
    case "hotel_grid":
    case "restaurant_grid":
      return <GridFilters type={block.block_type} data={data} setData={setData} />
    case "statistics":
      return <RowList label="Statistics" rows={data.items} onChange={(items) => setData({ items })} addLabel="Statistic" empty="No statistics yet."
        fields={[{ key: "number", label: "Number", placeholder: "77" }, { key: "label", label: "Label", placeholder: "Districts" }]} />
    case "list":
      return (
        <div className="space-y-2">
          <label className="flex items-center gap-2 font-semibold text-slate-300"><input type="checkbox" checked={Boolean(data.ordered)} onChange={(e) => setData({ ordered: e.target.checked })} /> Numbered list</label>
          <RowList label="Items" rows={(data.items || []).map((it) => (typeof it === "string" ? { text: it } : it))} onChange={(items) => setData({ items })} addLabel="Item" empty="No items yet."
            fields={[{ key: "text", label: "Text", wide: true }]} />
        </div>
      )
    case "quote":
      return (
        <div className="grid gap-2 sm:grid-cols-2">
          <label className="block font-semibold text-slate-300 sm:col-span-2">Quote<textarea rows="3" className={input} value={data.quote || ""} onChange={(e) => setData({ quote: e.target.value })} /></label>
          <label className="block font-semibold text-slate-300">Attributed to<input className={input} value={data.author || ""} onChange={(e) => setData({ author: e.target.value })} /></label>
          <p className="self-end text-[11px] text-slate-400">Only publish quotes you have permission to use, with the real source.</p>
        </div>
      )
    case "html":
      return (
        <label className="block font-semibold text-slate-300">HTML (sanitised on save: no scripts, iframes or event handlers)
          <textarea rows="8" spellCheck="false" className={`${input} font-mono`} value={data.html || ""} onChange={(e) => setData({ html: e.target.value })} /></label>
      )
    case "divider":
      return <p className="text-slate-400">A divider has no settings.</p>
    case "table":
      return <TableEditor data={data} setData={setData} />
    case "card_grid":
      return (
        <div className="space-y-2">
          <RowList label="Cards" rows={data.items} onChange={(items) => setData({ items })} addLabel="Card" empty="No cards yet."
            fields={[{ key: "title", label: "Title" }, { key: "emoji", label: "Emoji (shown when there is no image)" }, { key: "url", label: "Link (internal, starts with /)", placeholder: "/before-you-travel" }, { key: "image", label: "Image (HTTPS or /media/…)" }, { key: "description", label: "Description", type: "textarea", wide: true }]} />
          <label className="block font-semibold text-slate-300">Columns on desktop
            <select className={input} value={data.columns || 4} onChange={(e) => setData({ columns: Number(e.target.value) })}>{[1, 2, 3, 4].map((n) => <option key={n} value={n}>{n}</option>)}</select></label>
        </div>
      )
    default:
      return null
  }
}

export const STRUCTURED_TYPES = new Set(["subheading", "gallery", "map", "destination_grid", "hotel_grid", "restaurant_grid", "statistics", "list", "quote", "html", "divider", "table", "card_grid"])
