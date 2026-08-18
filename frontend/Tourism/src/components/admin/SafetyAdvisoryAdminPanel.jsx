import { useState } from "react"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

export default function SafetyAdvisoryAdminPanel() {
  const { showToast } = useToast()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ alert_type:"flood", severity:"high", title:"", description:"", latitude:"", longitude:"", city:"", municipality:"", district:"", province:"", radius_km:4, source:"", source_url:"", is_verified:true, is_active:true })
  const update=(key,value)=>setForm(old=>({...old,[key]:value}))
  const submit=async(e)=>{e.preventDefault();try{await adminApi.createAlert(form);showToast("Location advisory published; nearby users and linked family were notified.","success");setOpen(false)}catch(err){showToast(err.response?.data?.detail||"Could not publish advisory","error")}}
  return <div className="rounded-2xl border border-rose-500/20 bg-slate-900/70 p-5">
    <div className="flex justify-between gap-3"><div><h3 className="font-black text-white">Location News & Disaster Advisory</h3><p className="text-xs text-slate-400">Verified alerts notify users within 2–4 km and their accepted family links.</p></div><button onClick={()=>setOpen(!open)} className="rounded-xl bg-rose-600 text-white px-4 py-2 text-xs font-black">{open?"Close":"Publish advisory"}</button></div>
    {open&&<form onSubmit={submit} className="grid md:grid-cols-4 gap-3 mt-4">
      <select className="input-field" value={form.alert_type} onChange={e=>update("alert_type",e.target.value)}><option value="flood">Flood</option><option value="landslide">Landslide</option><option value="weather">Weather</option><option value="earthquake">Earthquake</option><option value="health">Health</option><option value="transport">Transport</option><option value="crime">Crime</option></select>
      <select className="input-field" value={form.severity} onChange={e=>update("severity",e.target.value)}><option value="low">Low</option><option value="moderate">Moderate</option><option value="high">High</option><option value="critical">Critical</option></select>
      <input required className="input-field" placeholder="Latitude" type="number" step="any" value={form.latitude} onChange={e=>update("latitude",e.target.value)}/><input required className="input-field" placeholder="Longitude" type="number" step="any" value={form.longitude} onChange={e=>update("longitude",e.target.value)}/>
      <input required className="input-field md:col-span-2" placeholder="Alert/news title" value={form.title} onChange={e=>update("title",e.target.value)}/><input className="input-field" placeholder="City / place" value={form.city} onChange={e=>update("city",e.target.value)}/><input className="input-field" placeholder="Municipality" value={form.municipality} onChange={e=>update("municipality",e.target.value)}/>
      <input className="input-field" placeholder="District" value={form.district} onChange={e=>update("district",e.target.value)}/><input className="input-field" placeholder="Province" value={form.province} onChange={e=>update("province",e.target.value)}/><input className="input-field" placeholder="Official source" value={form.source} onChange={e=>update("source",e.target.value)}/><input className="input-field" placeholder="Source URL" type="url" value={form.source_url} onChange={e=>update("source_url",e.target.value)}/>
      <textarea required className="input-field md:col-span-3" placeholder="Verified advisory details and safety instructions" value={form.description} onChange={e=>update("description",e.target.value)}/><label className="text-xs text-slate-300">Radius: {form.radius_km} km<input className="w-full" type="range" min="2" max="4" step="0.5" value={form.radius_km} onChange={e=>update("radius_km",Number(e.target.value))}/></label>
      <button className="md:col-span-4 rounded-xl bg-rose-600 text-white py-3 font-black text-sm">Publish verified alert & notify nearby users</button>
    </form>}
  </div>
}
