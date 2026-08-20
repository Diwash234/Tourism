import { useEffect, useState } from "react"
import { FiImage, FiSave, FiTrash2, FiUpload } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

const textFields = [["site_title","Website title"],["tagline","Tagline"],["footer_text","Footer text"],["contact_email","Contact email"],["contact_phone","Contact phone"]]
const socialFields = [["facebook_url","Facebook HTTPS URL"],["instagram_url","Instagram HTTPS URL"],["twitter_url","X / Twitter HTTPS URL"],["youtube_url","YouTube HTTPS URL"]]

export default function BrandingPanel() {
  const { showToast } = useToast()
  const [branding, setBranding] = useState({ theme_preset: "himalayan" })
  const [assets, setAssets] = useState({})
  const [presets, setPresets] = useState({})
  const [busy, setBusy] = useState(false)
  const load = async () => { try { const { data } = await adminApi.getBranding(); setBranding(data.branding || {}); setAssets(data.assets || {}); setPresets(data.presets || {}) } catch (error) { showToast(error.response?.data?.detail || "Branding unavailable", "error") } }
  useEffect(() => { load() }, [])
  const save = async () => {
    setBusy(true)
    try {
      const allowed = [...textFields, ...socialFields].reduce((value,[key]) => ({ ...value, [key]: branding[key] || "" }), { theme_preset: branding.theme_preset || "himalayan" })
      const { data } = await adminApi.updateBranding(allowed); setBranding(data.branding); showToast("Branding published", "success")
    } catch (error) { showToast(error.response?.data?.detail || "Branding save failed", "error") } finally { setBusy(false) }
  }
  const upload = async (kind, file) => {
    if (!file) return
    const body = new FormData(); body.append("kind", kind); body.append("file", file); body.append("alt_text", kind === "logo" ? branding.site_title || "Tourism logo" : "Website icon")
    try { await adminApi.uploadBrandingAsset(body); showToast(`${kind} uploaded`, "success"); load() } catch (error) { showToast(error.response?.data?.detail || "Upload failed", "error") }
  }
  const remove = async kind => { if (!window.confirm(`Remove the current ${kind}?`)) return; try { await adminApi.deleteBrandingAsset(kind); load() } catch (error) { showToast(error.response?.data?.detail || "Removal failed", "error") } }

  return <div className="space-y-5 text-slate-100"><header><h2 className="text-2xl font-black">Branding and theme studio</h2><p className="text-xs text-slate-400">Upload validated assets and choose a safe preset. Arbitrary CSS, JavaScript, and SVG uploads are not accepted.</p></header>
    <div className="grid lg:grid-cols-2 gap-4">
      <section className="bg-slate-950 border border-slate-700 rounded-2xl p-5 space-y-4"><h3 className="font-black text-lg">Identity and contact</h3><div className="grid sm:grid-cols-2 gap-3">{textFields.map(([key,label])=><label key={key} className={`text-xs text-slate-400 ${key === "footer_text" ? "sm:col-span-2" : ""}`}>{label}{key === "footer_text" ? <textarea rows="3" className="input-field mt-1" value={branding[key]||""} onChange={event=>setBranding({...branding,[key]:event.target.value})}/>:<input className="input-field mt-1" value={branding[key]||""} onChange={event=>setBranding({...branding,[key]:event.target.value})}/>}</label>)}</div><h4 className="font-bold">Official social links</h4>{socialFields.map(([key,label])=><label key={key} className="block text-xs text-slate-400">{label}<input type="url" placeholder="https://" className="input-field mt-1" value={branding[key]||""} onChange={event=>setBranding({...branding,[key]:event.target.value})}/></label>)}</section>
      <section className="bg-slate-950 border border-slate-700 rounded-2xl p-5"><h3 className="font-black text-lg mb-3">Safe theme presets</h3><div className="space-y-2">{Object.entries(presets).map(([key,preset])=><button key={key} onClick={()=>setBranding({...branding,theme_preset:key})} className={`w-full text-left rounded-xl border p-4 ${branding.theme_preset===key?"border-amber-400 bg-slate-800":"border-slate-700 bg-slate-900"}`}><div className="flex justify-between"><b className="capitalize">{key}</b><span className="flex gap-1"><i className="w-5 h-5 rounded-full" style={{background:preset.primary_color}}/><i className="w-5 h-5 rounded-full" style={{background:preset.secondary_color}}/></span></div><p className="text-[11px] text-slate-500 mt-1">{preset.density} density · {preset.border_radius} corners · {preset.sidebar_style} sidebar</p></button>)}</div><div className="mt-4 rounded-xl border border-slate-700 overflow-hidden" style={{background:presets[branding.theme_preset]?.background_color}}><div className="p-3 text-white font-bold" style={{background:presets[branding.theme_preset]?.primary_color}}>Live preset sample</div><div className="p-5"><button className="px-4 py-2 text-white rounded-lg" style={{background:presets[branding.theme_preset]?.secondary_color}}>Primary action</button></div></div></section>
    </div>
    <section className="bg-slate-950 border border-slate-700 rounded-2xl p-5"><h3 className="font-black text-lg mb-4">Logo and favicon</h3><div className="grid md:grid-cols-2 gap-4">{["logo","favicon"].map(kind=><div key={kind} className="bg-slate-900 border border-slate-700 rounded-xl p-4"><div className="flex gap-3 items-center">{assets[kind]?.url?<img src={assets[kind].url} alt={kind} className="w-20 h-20 object-contain bg-white rounded-lg"/>:<div className="w-20 h-20 grid place-items-center bg-slate-800 rounded-lg"><FiImage size={25}/></div>}<div><b className="capitalize">{kind}</b>{assets[kind]&&<p className="text-[10px] text-slate-500">{assets[kind].width}×{assets[kind].height} · {Math.ceil(assets[kind].file_size/1024)} KB</p>}<div className="flex gap-2 mt-2"><label className="cursor-pointer px-3 py-2 bg-sky-700 rounded-lg text-xs font-bold flex gap-1"><FiUpload/> Upload<input type="file" accept="image/png,image/jpeg,image/webp,image/x-icon" className="hidden" onChange={event=>upload(kind,event.target.files?.[0])}/></label>{assets[kind]&&<button onClick={()=>remove(kind)} className="p-2 bg-rose-800 rounded-lg"><FiTrash2/></button>}</div></div></div></div>)}</div><p className="text-[11px] text-slate-500 mt-3">PNG, JPEG, WebP or ICO only, maximum 2 MB. Favicons must be square and at most 512×512.</p></section>
    <button disabled={busy} onClick={save} className="px-6 py-3 bg-emerald-700 rounded-xl font-black flex items-center gap-2"><FiSave/> {busy?"Publishing…":"Publish branding and theme"}</button>
  </div>
}
