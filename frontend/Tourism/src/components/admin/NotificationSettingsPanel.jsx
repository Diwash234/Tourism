import { useEffect, useMemo, useState } from "react"
import { FiBell, FiRefreshCw, FiSearch, FiSend, FiSettings } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

const ROLES = ["", "tourist", "guide", "staff", "content_moderator", "district_manager", "hotel_manager", "tourist_police"]
const empty = { title: "", message: "", role: "" }

export default function NotificationSettingsPanel() {
  const { showToast } = useToast()
  const [tab, setTab] = useState("broadcast")
  const [form, setForm] = useState(empty)
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)
  const [query, setQuery] = useState("")
  const [channel, setChannel] = useState("all")
  const [readFilter, setReadFilter] = useState("all")
  const [result, setResult] = useState(null)
  const [branding, setBranding] = useState({ site_title: "", tagline: "", primary_color: "#1f6b4d", secondary_color: "#c2603a", footer_text: "", contact_email: "", contact_phone: "" })
  const [settingId, setSettingId] = useState(null)

  const loadNotifications = async () => {
    setLoading(true)
    try { const { data } = await adminApi.getAdminNotifications(); setNotifications(data || []) }
    catch (error) { showToast(error.response?.data?.detail || "Could not load notifications", "error") }
    finally { setLoading(false) }
  }
  const loadSettings = async () => {
    try {
      const { data } = await adminApi.getCMS("settings")
      const item = (data.results || []).find(row => row.key === "branding")
      if (item) { setSettingId(item.id); setBranding(old => ({ ...old, ...(item.value || {}) })) }
    } catch { /* capability/API errors are shown when saving */ }
  }
  useEffect(() => { loadNotifications(); loadSettings() }, [])

  const send = async (event) => {
    event.preventDefault()
    if (!form.title.trim() || !form.message.trim()) return showToast("Title and message are required", "error")
    setSending(true); setResult(null)
    try {
      const { data } = await adminApi.broadcastNotification({ ...form, role: form.role || null })
      setResult(data); setForm(empty); showToast(`Broadcast created for ${data.recipient_count} users`, "success"); loadNotifications()
    } catch (error) { showToast(error.response?.data?.detail || "Broadcast failed", "error") }
    finally { setSending(false) }
  }
  const saveBranding = async () => {
    try {
      const payload = { resource: "settings", id: settingId, key: "branding", value: branding, description: "Public platform branding", is_public: true }
      if (settingId) await adminApi.updateCMS(payload)
      else { const { data } = await adminApi.createCMS(payload); setSettingId(data.id) }
      showToast("Branding settings saved", "success")
    } catch (error) { showToast(error.response?.data?.detail || "Settings save failed", "error") }
  }
  const filtered = useMemo(() => notifications.filter(item => {
    const text = `${item.title} ${item.message} ${item.user}`.toLowerCase()
    return (!query || text.includes(query.toLowerCase())) && (channel === "all" || item.channel === channel) && (readFilter === "all" || String(item.is_read) === readFilter)
  }), [notifications, query, channel, readFilter])
  const stats = useMemo(() => ({ total: notifications.length, unread: notifications.filter(x => !x.is_read).length, sent: notifications.filter(x => x.is_sent).length }), [notifications])

  return <div className="space-y-5">
    <div className="flex flex-wrap gap-2 border-b border-slate-700 pb-3">
      {[['broadcast','Broadcast',FiSend],['history','History',FiBell],['settings','Branding & Contact',FiSettings]].map(([id,label,Icon]) => <button key={id} onClick={() => setTab(id)} className={`px-4 py-2 rounded-xl text-xs font-black flex gap-2 items-center ${tab===id?'bg-amber-400 text-slate-950':'bg-slate-900 text-slate-300'}`}><Icon/>{label}</button>)}
    </div>
    {tab === "broadcast" && <form onSubmit={send} className="max-w-3xl rounded-2xl bg-slate-950 border border-slate-700 p-6 space-y-4">
      <h2 className="text-white text-xl font-black">Send Platform Notification</h2>
      <p className="text-xs text-slate-400">Creates in-app notifications for active users. Role targeting is optional and every broadcast is audited.</p>
      <label className="block text-xs text-slate-300">Title<input className="input-field mt-1" maxLength="200" value={form.title} onChange={e=>setForm({...form,title:e.target.value})}/></label>
      <label className="block text-xs text-slate-300">Message<textarea className="input-field mt-1" rows="5" value={form.message} onChange={e=>setForm({...form,message:e.target.value})}/></label>
      <label className="block text-xs text-slate-300">Target role<select className="input-field mt-1" value={form.role} onChange={e=>setForm({...form,role:e.target.value})}>{ROLES.map(role=><option key={role} value={role}>{role || "All active users"}</option>)}</select></label>
      <div className="flex justify-between text-xs text-slate-500"><span>{form.message.length} characters</span>{result&&<span className="text-emerald-400">{result.recipient_count} recipients created</span>}</div>
      <button disabled={sending} className="bg-emerald-600 disabled:opacity-50 text-white px-6 py-3 rounded-xl font-black">{sending?"Sending…":"Create Broadcast"}</button>
    </form>}
    {tab === "history" && <div className="space-y-4"><div className="grid grid-cols-3 gap-3">{Object.entries(stats).map(([key,value])=><div key={key} className="bg-slate-950 border border-slate-700 rounded-xl p-4"><p className="text-xs uppercase text-slate-500">{key}</p><b className="text-white text-2xl">{value}</b></div>)}</div><div className="flex flex-wrap gap-2"><div className="relative flex-1"><FiSearch className="absolute left-3 top-3 text-slate-500"/><input className="input-field pl-9" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search title, message or recipient…"/></div><select className="input-field w-36" value={channel} onChange={e=>setChannel(e.target.value)}><option value="all">All channels</option><option value="in_app">In app</option><option value="email">Email</option><option value="sms">SMS</option><option value="push">Push</option></select><select className="input-field w-32" value={readFilter} onChange={e=>setReadFilter(e.target.value)}><option value="all">All status</option><option value="true">Read</option><option value="false">Unread</option></select><button onClick={loadNotifications} className="p-3 rounded-xl bg-slate-800 text-white"><FiRefreshCw className={loading?'animate-spin':''}/></button></div><div className="space-y-2 max-h-[60vh] overflow-y-auto">{filtered.map(item=><article key={item.id} className="bg-slate-950 border border-slate-700 p-4 rounded-xl text-xs"><div className="flex justify-between"><b className="text-white">{item.title}</b><span className={item.is_read?'text-slate-500':'text-amber-400'}>{item.is_read?'Read':'Unread'}</span></div><p className="text-slate-300 mt-1">{item.message}</p><p className="text-slate-500 mt-2">{item.user} · {item.channel} · {new Date(item.created_at).toLocaleString()}</p></article>)}</div></div>}
    {tab === "settings" && <div className="max-w-3xl rounded-2xl bg-slate-950 border border-slate-700 p-6"><h2 className="text-white font-black text-xl mb-4">Branding & Contact Settings</h2><div className="grid sm:grid-cols-2 gap-3">{[['site_title','Website title'],['tagline','Tagline'],['footer_text','Footer text'],['contact_email','Contact email'],['contact_phone','Contact phone']].map(([key,label])=><label key={key} className="text-xs text-slate-300">{label}<input className="input-field mt-1" value={branding[key]||''} onChange={e=>setBranding({...branding,[key]:e.target.value})}/></label>)}{[['primary_color','Primary color'],['secondary_color','Secondary color']].map(([key,label])=><label key={key} className="text-xs text-slate-300">{label}<div className="flex gap-2"><input type="color" value={branding[key]} onChange={e=>setBranding({...branding,[key]:e.target.value})}/><input className="input-field" value={branding[key]} onChange={e=>setBranding({...branding,[key]:e.target.value})}/></div></label>)}</div><button onClick={saveBranding} className="mt-4 bg-emerald-600 text-white px-6 py-2 rounded-xl font-black">Save Published Settings</button></div>}
  </div>
}
