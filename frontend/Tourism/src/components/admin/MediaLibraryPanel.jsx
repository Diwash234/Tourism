import { useEffect, useState } from "react"
import { useSearchParams } from "react-router-dom"
import { FiArrowDown, FiArrowUp, FiPlus, FiUpload, FiX } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import PlaceholderImage from "../common/PlaceholderImage"
import useToast from "../../hooks/useToast"
import ImageCropper from "./ImageCropper"

const emptyUpload = { destination_id: "", caption: "", alt_text: "", external_url: "", source_url: "", license: "" }

export default function MediaLibraryPanel() {
  const { showToast } = useToast()
  const [data, setData] = useState({ results: [], page: 1, total_pages: 1, count: 0 })
  const [params] = useSearchParams()
  const [q, setQ] = useState("")
  const [status, setStatus] = useState(params.get("status") || "")
  const [active, setActive] = useState(null)
  const [cropping, setCropping] = useState(null)
  const [selected, setSelected] = useState([])
  const [showUpload, setShowUpload] = useState(false)
  const [upload, setUpload] = useState(emptyUpload)
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(false)

  const load = async (page = 1) => {
    setBusy(true)
    try { setData((await adminApi.getMediaLibrary({ q, status, page, page_size: 30 })).data) }
    catch (error) { showToast(error.response?.data?.detail || "Could not load media", "error") }
    finally { setBusy(false) }
  }

  useEffect(() => { setStatus(params.get("status") || "") }, [params])
  useEffect(() => { load() }, [status])

  const update = async (image, patch) => {
    try {
      await adminApi.updateMediaLibrary({ id: image.id, ...patch })
      showToast("Media updated", "success")
      load(data.page)
    } catch (error) {
      showToast(error.response?.data?.detail || "Update failed", "error")
    }
  }

  const bulk = async (action) => {
    await adminApi.updateMediaLibrary({ ids: selected, action })
    setSelected([])
    load(data.page)
  }

  const submit = async (event) => {
    event.preventDefault()
    const body = new FormData()
    Object.entries(upload).forEach(([key, value]) => value && body.append(key, value))
    if (file) body.append("file", file)
    setBusy(true)
    try {
      await adminApi.uploadMediaLibrary(body)
      showToast("Image added to moderation queue", "success")
      setUpload(emptyUpload)
      setFile(null)
      setShowUpload(false)
      load(1)
    } catch (error) {
      showToast(error.response?.data?.detail || "Upload failed", "error")
    } finally { setBusy(false) }
  }

  const remove = async (image) => {
    if (!window.confirm("Permanently remove this media record? Destination and audit records remain protected.")) return
    try {
      await adminApi.deleteMediaLibrary(image.id)
      showToast("Media removed", "success")
      load(data.page)
    } catch (error) {
      showToast(error.response?.data?.detail || "Delete failed", "error")
    }
  }

  return (
    <div className="space-y-4 text-slate-900">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div>
          <h2 className="text-2xl font-black text-emerald-950">Central Media Library</h2>
          <p className="text-sm text-slate-500">{data.count.toLocaleString()} database images. Upload local files, add licensed external media, crop, reorder galleries and select covers.</p>
        </div>
        <button onClick={() => setShowUpload(true)} className="ml-auto flex items-center gap-2 rounded-xl bg-emerald-700 px-4 py-3 font-bold text-white"><FiPlus />Add image</button>
      </header>
      <div className="flex flex-col gap-2 rounded-2xl border border-emerald-200 bg-white p-3 sm:flex-row">
        <input className="input-field" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search destination, caption or URL…" />
        <select className="input-field sm:w-44" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All status</option>
          <option>pending</option>
          <option>approved</option>
          <option>rejected</option>
        </select>
        <button onClick={() => load(1)} className="rounded-xl bg-emerald-700 px-5 py-2 font-black text-white">Search</button>
      </div>
      <div className="flex justify-between">
        <p className="text-xs text-slate-500">Page {data.page} of {data.total_pages} · {selected.length} selected</p>
        {selected.length > 0 && (
          <div>
            <button onClick={() => bulk("approve")} className="mr-3 font-bold text-emerald-700">Bulk approve</button>
            <button onClick={() => bulk("reject")} className="font-bold text-rose-600">Bulk reject</button>
          </div>
        )}
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {data.results.map((image) => (
          <article key={image.id} className="relative overflow-hidden rounded-2xl border border-emerald-200 bg-white shadow-sm">
            <input
              type="checkbox"
              aria-label={`Select ${image.caption || image.destination}`}
              checked={selected.includes(image.id)}
              onChange={(e) => setSelected(e.target.checked ? [...selected, image.id] : selected.filter((id) => id !== image.id))}
              className="absolute right-2 top-2 z-10 h-5 w-5"
            />
            <button onClick={() => setActive(image)} className="w-full">
              <PlaceholderImage src={image.url} title={image.destination} alt={image.caption} cropBox={image.crop_box} className="h-40 w-full" />
            </button>
            <div className="p-3 text-xs text-slate-600">
              <div className="flex justify-between gap-2">
                <b className="block truncate text-emerald-950">{image.destination}</b>
                {image.is_cover && <span className="rounded bg-amber-100 px-2 text-amber-800">Cover</span>}
              </div>
              <p className="truncate">{image.caption || "No caption"}</p>
              {image.used_on?.length > 0 && <p className="mt-1 text-[10px] text-slate-500">Used on: {image.used_on.map((item) => item.label).join(" · ")}</p>}
              <p>{image.source} · {image.status} · position {image.ordering + 1}</p>
              <div className="mt-3 grid grid-cols-2 gap-1.5">
                <button onClick={() => update(image, { verification_status: "approved", is_verified: true })} className="rounded-lg bg-emerald-700 px-2 py-1.5 font-bold text-white">Approve</button>
                <button onClick={() => update(image, { verification_status: "rejected", is_verified: false })} className="rounded-lg bg-rose-600 px-2 py-1.5 font-bold text-white">Reject</button>
                <button onClick={() => update(image, { action: "move_up" })} className="rounded-lg bg-emerald-50 px-2 py-1.5 font-bold text-emerald-900" title="Move up"><FiArrowUp className="inline" /> Up</button>
                <button onClick={() => update(image, { action: "move_down" })} className="rounded-lg bg-emerald-50 px-2 py-1.5 font-bold text-emerald-900" title="Move down"><FiArrowDown className="inline" /> Down</button>
                <button onClick={async () => { await adminApi.setAdminDestinationCover(image.destination_id, { image_id: image.id }); load(data.page) }} className="rounded-lg bg-amber-400 px-2 py-1.5 font-bold text-slate-950">Cover</button>
                <button onClick={() => setCropping(image)} className="rounded-lg bg-sky-700 px-2 py-1.5 font-bold text-white">Crop</button>
                <button onClick={() => remove(image)} className="col-span-2 rounded-lg bg-rose-100 px-2 py-1.5 font-bold text-rose-800">Remove</button>
              </div>
            </div>
          </article>
        ))}
      </div>
      <div className="flex justify-between rounded-xl border border-emerald-100 bg-white p-3">
        <button disabled={data.page <= 1 || busy} onClick={() => load(data.page - 1)}>Previous</button>
        <span>Page {data.page} / {data.total_pages}</span>
        <button disabled={data.page >= data.total_pages || busy} onClick={() => load(data.page + 1)}>Next</button>
      </div>
      {active && (
        <button onClick={() => setActive(null)} className="fixed inset-0 z-[100] bg-black/90 p-8" aria-label="Close image preview">
          <img src={active.url} alt={active.caption} className="mx-auto max-h-full max-w-full object-contain" />
        </button>
      )}
      {cropping && (
        <ImageCropper
          image={cropping}
          onClose={() => setCropping(null)}
          onSave={async (crop_box) => {
            await update(cropping, { crop_box })
            setCropping(null)
          }}
        />
      )}
      {showUpload && (
        <div className="fixed inset-0 z-[100] grid place-items-center bg-black/60 p-4">
          <form onSubmit={submit} className="w-full max-w-xl space-y-3 rounded-2xl bg-white p-6 text-slate-900">
            <div className="flex justify-between">
              <div>
                <h3 className="text-xl font-black text-emerald-950">Add destination image</h3>
                <p className="text-xs text-slate-500">New media starts pending and must be approved.</p>
              </div>
              <button type="button" onClick={() => setShowUpload(false)} aria-label="Close"><FiX /></button>
            </div>
            <label className="block text-xs font-bold">Destination database ID
              <input required type="number" className="input-field mt-1" value={upload.destination_id} onChange={(e) => setUpload({ ...upload, destination_id: e.target.value })} />
            </label>
            <label className="block cursor-pointer rounded-xl border-2 border-dashed border-emerald-300 bg-emerald-50 p-5 text-center">
              <FiUpload className="mx-auto mb-2" />Browse computer for JPEG, PNG or WebP
              <input type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={(e) => setFile(e.target.files?.[0] || null)} />
              {file && <span className="mt-2 block font-bold text-emerald-800">{file.name}</span>}
            </label>
            <div className="text-center text-xs font-bold text-slate-400">OR</div>
            <label className="block text-xs font-bold">External HTTPS image URL
              <input type="url" className="input-field mt-1" value={upload.external_url} onChange={(e) => setUpload({ ...upload, external_url: e.target.value })} placeholder="https://…" />
            </label>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="text-xs font-bold">Caption<input className="input-field mt-1" value={upload.caption} onChange={(e) => setUpload({ ...upload, caption: e.target.value })} /></label>
              <label className="text-xs font-bold">Alt text<input className="input-field mt-1" value={upload.alt_text} onChange={(e) => setUpload({ ...upload, alt_text: e.target.value })} /></label>
              <label className="text-xs font-bold">Original source page<input type="url" className="input-field mt-1" value={upload.source_url} onChange={(e) => setUpload({ ...upload, source_url: e.target.value })} /></label>
              <label className="text-xs font-bold">License / permission<input className="input-field mt-1" value={upload.license} onChange={(e) => setUpload({ ...upload, license: e.target.value })} /></label>
            </div>
            <button disabled={busy || (!file && !upload.external_url)} className="w-full rounded-xl bg-emerald-700 py-3 font-black text-white disabled:opacity-40">Add to moderation queue</button>
          </form>
        </div>
      )}
    </div>
  )
}
