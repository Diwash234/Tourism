import { useEffect, useState } from "react"
import { FiEdit3, FiPlus, FiRefreshCw, FiTrash2 } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

const empty = { type: "", name: "", phone_number: "", alternate_phone: "", description: "", source_name: "", source_url: "" }

export default function NationalHotlinesPanel() {
  const { showToast } = useToast()
  const [rows, setRows] = useState([])
  const [protectedTypes, setProtectedTypes] = useState([])
  const [form, setForm] = useState(empty)
  const [editing, setEditing] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    try {
      const { data } = await adminApi.getNationalHotlines()
      setRows(data.results || [])
      setProtectedTypes(data.protected_types || [])
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not load national hotlines", "error")
    } finally { setLoading(false) }
  }
  const refresh = () => { setLoading(true); return load() }
  useEffect(() => {
    let active = true
    adminApi.getNationalHotlines()
      .then(({ data }) => {
        if (!active) return
        setRows(data.results || [])
        setProtectedTypes(data.protected_types || [])
      })
      .catch((error) => {
        if (active) showToast(error.response?.data?.detail || "Could not load national hotlines", "error")
      })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  const save = async (event) => {
    event.preventDefault()
    try {
      if (editing) await adminApi.updateNationalHotline({ ...form, type: editing })
      else await adminApi.createNationalHotline(form)
      showToast(editing ? "National hotline updated" : "National hotline added", "success")
      setForm(empty); setEditing(null); refresh()
    } catch (error) { showToast(error.response?.data?.detail || "Could not save hotline", "error") }
  }
  const remove = async (type) => {
    if (!window.confirm("Delete this non-protected hotline?")) return
    try { await adminApi.deleteNationalHotline(type); showToast("National hotline deleted", "success"); refresh() }
    catch (error) { showToast(error.response?.data?.detail || "Could not delete hotline", "error") }
  }
  const startEdit = (row) => { setEditing(row.type); setForm({ ...empty, ...row }) }

  return <section className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-slate-900" data-testid="national-hotlines-panel">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div><p className="text-[11px] font-black uppercase tracking-wider text-amber-800">Owner-managed safety data</p><h3 className="text-xl font-black">National emergency hotlines</h3><p className="mt-1 text-xs text-slate-600">Edit sourced definitions or add a non-critical operator. Tourist Police 1144, Police 100, Ambulance 102, Fire 101 and Traffic 103 are protected from deletion.</p></div>
      <button type="button" onClick={refresh} className="inline-flex items-center gap-2 rounded-xl border border-amber-300 bg-white px-3 py-2 text-xs font-bold"><FiRefreshCw className={loading ? "animate-spin" : ""} /> Refresh</button>
    </div>
    <div className="mt-4 grid gap-3 md:grid-cols-2">
      {rows.map((row) => <article key={row.type} className="rounded-xl border border-amber-200 bg-white p-4">
        <div className="flex items-start justify-between gap-3"><div><h4 className="font-black">{row.name}</h4><p className="text-sm font-bold text-rose-700">{row.phone_number}</p><p className="text-xs text-slate-500">{row.description}</p></div><span className="rounded-full bg-amber-100 px-2 py-1 text-xs font-black uppercase">{row.type}</span></div>
        <p className="mt-2 text-[11px] text-slate-500">Source: {row.source_name} {row.source_url && <a className="underline" href={row.source_url} target="_blank" rel="noreferrer">(open)</a>}</p>
        <div className="mt-3 flex gap-2"><button type="button" onClick={() => startEdit(row)} className="inline-flex items-center gap-1 rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-bold text-white"><FiEdit3 /> Edit</button>{!protectedTypes.includes(row.type) && <button type="button" onClick={() => remove(row.type)} className="inline-flex items-center gap-1 rounded-lg bg-rose-700 px-3 py-1.5 text-xs font-bold text-white"><FiTrash2 /> Delete</button>}</div>
      </article>)}
    </div>
    <form onSubmit={save} className="mt-4 rounded-xl border border-amber-200 bg-white p-4">
      <div className="mb-3 flex items-center justify-between"><h4 className="font-black">{editing ? `Edit ${editing}` : "Add hotline"}</h4>{editing && <button type="button" onClick={() => { setEditing(null); setForm(empty) }} className="text-xs font-bold underline">Cancel</button>}</div>
      <div className="grid gap-2 md:grid-cols-2"><input required disabled={Boolean(editing)} className="input-field" placeholder="Type key (e.g. district_rescue)" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })} /><input required className="input-field" placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /><input required className="input-field" placeholder="Phone number" value={form.phone_number} onChange={(e) => setForm({ ...form, phone_number: e.target.value })} /><input className="input-field" placeholder="Alternate phone" value={form.alternate_phone} onChange={(e) => setForm({ ...form, alternate_phone: e.target.value })} /><input className="input-field md:col-span-2" placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /><input required className="input-field" placeholder="Source name" value={form.source_name} onChange={(e) => setForm({ ...form, source_name: e.target.value })} /><input type="url" className="input-field" placeholder="HTTPS source URL" value={form.source_url} onChange={(e) => setForm({ ...form, source_url: e.target.value })} /></div>
      <button type="submit" className="mt-3 inline-flex items-center gap-2 rounded-xl bg-amber-500 px-4 py-2 text-xs font-black text-slate-950"><FiPlus /> {editing ? "Save changes" : "Add hotline"}</button>
    </form>
  </section>
}
