import { useCallback, useEffect, useState } from "react"
import { FiCheckCircle, FiChevronLeft, FiChevronRight, FiKey, FiPlus, FiRefreshCw, FiSearch, FiShield, FiUserCheck, FiUserX, FiX } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

const ROLES = ["tourist", "guide", "staff", "content_moderator", "district_manager", "hotel_manager", "tourist_police", "police", "hospital_staff", "rescue_team", "emergency_operator", "tourism_admin", "admin", "super_admin"]
const label = (value) => value?.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())
const date = (value) => value ? new Date(value).toLocaleString() : "Never"

export default function UserManagement() {
  const { showToast } = useToast()
  const [rows, setRows] = useState([])
  const [count, setCount] = useState(0)
  const [pages, setPages] = useState(1)
  const [page, setPage] = useState(1)
  const [q, setQ] = useState("")
  const [role, setRole] = useState("")
  const [status, setStatus] = useState("")
  const [verified, setVerified] = useState("")
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({ email: "", password: "", first_name: "", last_name: "", role: "staff", managed_district: "" })

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await adminApi.getUsers({ q, role, status, verified, page, page_size: 25 })
      setRows(data.results || [])
      setCount(data.count || 0)
      setPages(data.pages || 1)
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not load users", "error")
    } finally { setLoading(false) }
  }, [q, role, status, verified, page])

  useEffect(() => { const timer = setTimeout(load, 250); return () => clearTimeout(timer) }, [load])
  useEffect(() => setPage(1), [q, role, status, verified])

  const openDetail = async (id) => {
    setDetailLoading(true)
    setSelected({ id })
    try { setSelected((await adminApi.getUserDetail(id)).data) }
    catch (error) { showToast(error.response?.data?.detail || "Could not load profile", "error"); setSelected(null) }
    finally { setDetailLoading(false) }
  }

  const mutate = async (id, operation, confirmation) => {
    if (confirmation && !window.confirm(confirmation)) return
    try {
      const response = await operation()
      showToast(response.data?.message || "User updated", "success")
      await load()
      if (selected?.id === id) await openDetail(id)
    } catch (error) { showToast(error.response?.data?.detail || "Action was denied", "error") }
  }

  const create = async (event) => {
    event.preventDefault()
    try {
      const { data } = await adminApi.createUser(form)
      showToast(data.message, "success")
      setCreating(false)
      setForm({ email: "", password: "", first_name: "", last_name: "", role: "staff", managed_district: "" })
      load()
    } catch (error) { showToast(error.response?.data?.detail || "Could not create user", "error") }
  }

  return <div className="space-y-5 text-slate-100">
    <div className="flex flex-col xl:flex-row xl:items-end justify-between gap-4">
      <div><h2 className="text-2xl font-black flex items-center gap-2"><FiShield className="text-amber-400"/> User access management</h2><p className="text-xs text-slate-400 mt-1">Search, verify, deactivate, revoke sessions, and review security history. Deletion is retention-safe deactivation.</p></div>
      <button onClick={() => setCreating(true)} className="px-4 py-2.5 rounded-xl bg-amber-400 text-slate-950 font-black text-sm flex items-center justify-center gap-2"><FiPlus/> Create account</button>
    </div>

    <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-2 bg-slate-900/80 border border-slate-700 p-3 rounded-2xl">
      <label className="relative lg:col-span-2"><FiSearch className="absolute left-3 top-3 text-slate-500"/><input value={q} onChange={e=>setQ(e.target.value)} placeholder="Name, email, city or district" className="w-full bg-slate-950 border border-slate-700 rounded-xl py-2.5 pl-9 pr-3 text-sm"/></label>
      <select value={role} onChange={e=>setRole(e.target.value)} className="bg-slate-950 border border-slate-700 rounded-xl px-3 text-sm"><option value="">All roles</option>{ROLES.map(r=><option key={r} value={r}>{label(r)}</option>)}</select>
      <select value={status} onChange={e=>setStatus(e.target.value)} className="bg-slate-950 border border-slate-700 rounded-xl px-3 text-sm"><option value="">Any access</option><option value="active">Active</option><option value="inactive">Inactive</option></select>
      <select value={verified} onChange={e=>setVerified(e.target.value)} className="bg-slate-950 border border-slate-700 rounded-xl px-3 text-sm"><option value="">Any verification</option><option value="true">Verified</option><option value="false">Unverified</option></select>
    </div>

    <div className="rounded-2xl border border-slate-700 bg-slate-900/70 overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-700 flex justify-between text-xs text-slate-400"><span>{count.toLocaleString()} matching accounts</span><button onClick={load} className="flex gap-1 items-center hover:text-white"><FiRefreshCw className={loading?"animate-spin":""}/> Refresh</button></div>
      <div className="overflow-x-auto"><table className="w-full text-sm"><thead className="bg-slate-800 text-left text-[11px] uppercase tracking-wider text-slate-400"><tr><th className="p-4">Account</th><th className="p-4">Role</th><th className="p-4">Verification</th><th className="p-4">Last access</th><th className="p-4">Status</th><th className="p-4 text-right">Actions</th></tr></thead>
      <tbody className="divide-y divide-slate-800">{rows.map(u=><tr key={u.id} className="hover:bg-slate-800/50"><td className="p-4"><button onClick={()=>openDetail(u.id)} className="text-left"><b className="block text-white hover:text-amber-300">{u.full_name}</b><span className="text-xs text-slate-400">{u.email}</span><span className="block text-[10px] text-slate-500">{u.city || u.managed_district || "Location unavailable"}</span></button></td><td className="p-4"><select value={u.role} onChange={e=>mutate(u.id, ()=>adminApi.updateUserStatus(u.id,{role:e.target.value}), `Change this account's role to ${label(e.target.value)}?`)} className="bg-slate-950 border border-slate-700 rounded-lg px-2 py-1 text-xs">{ROLES.map(r=><option key={r} value={r}>{label(r)}</option>)}</select></td><td className="p-4"><span className={u.is_verified?"text-emerald-300":"text-amber-300"}>{u.is_verified?"Verified":"Pending"}</span></td><td className="p-4 text-xs text-slate-400">{date(u.last_login)}</td><td className="p-4"><span className={`px-2 py-1 rounded-full text-xs ${u.is_active?"bg-emerald-500/15 text-emerald-300":"bg-rose-500/15 text-rose-300"}`}>{u.is_active?"Active":"Inactive"}</span></td><td className="p-4 text-right"><button onClick={()=>mutate(u.id,()=>adminApi.updateUserStatus(u.id,{is_active:!u.is_active}),`${u.is_active?"Deactivate":"Activate"} this account?`)} className="p-2 rounded-lg bg-slate-800" title="Toggle account access">{u.is_active?<FiUserX/>:<FiUserCheck/>}</button></td></tr>)}
      {!loading&&!rows.length&&<tr><td colSpan="6" className="p-10 text-center text-slate-500">No accounts match these filters.</td></tr>}</tbody></table></div>
      <div className="p-3 border-t border-slate-700 flex justify-end items-center gap-3 text-xs"><button disabled={page<=1} onClick={()=>setPage(p=>p-1)} className="p-2 disabled:opacity-30"><FiChevronLeft/></button><span>Page {page} of {pages}</span><button disabled={page>=pages} onClick={()=>setPage(p=>p+1)} className="p-2 disabled:opacity-30"><FiChevronRight/></button></div>
    </div>

    {selected&&<div className="fixed inset-0 z-[70] bg-black/70 flex justify-end" onMouseDown={e=>e.target===e.currentTarget&&setSelected(null)}><aside className="w-full max-w-xl bg-slate-950 border-l border-slate-700 p-5 overflow-y-auto"><div className="flex justify-between"><div><h3 className="text-xl font-black">{selected.full_name||"User profile"}</h3><p className="text-sm text-slate-400">{selected.email}</p></div><button onClick={()=>setSelected(null)}><FiX size={22}/></button></div>{detailLoading?<p className="py-16 text-center text-slate-500">Loading profile…</p>:<div className="space-y-5 mt-6">
      <div className="grid grid-cols-2 gap-2 text-xs">{Object.entries(selected.activity||{}).map(([key,value])=><div key={key} className="rounded-xl bg-slate-900 border border-slate-800 p-3"><b className="text-xl block text-amber-300">{value}</b>{label(key)}</div>)}</div>
      <div className="rounded-xl bg-slate-900 border border-slate-800 p-4 text-xs space-y-2"><p><b>Role:</b> {label(selected.role)}</p><p><b>Joined:</b> {date(selected.date_joined)}</p><p><b>Last login:</b> {date(selected.last_login)}</p><p><b>Provider:</b> {label(selected.auth_provider)}</p><p><b>District:</b> {selected.managed_district||"Not assigned"}</p></div>
      <div className="grid sm:grid-cols-2 gap-2"><button onClick={()=>mutate(selected.id,()=>adminApi.runUserAccessAction(selected.id,selected.is_verified?"unverify":"verify"),"Update verified status?")} className="rounded-xl bg-emerald-700 px-3 py-2 text-sm font-bold flex justify-center gap-2"><FiCheckCircle/> {selected.is_verified?"Remove verification":"Mark verified"}</button><button onClick={()=>mutate(selected.id,()=>adminApi.runUserAccessAction(selected.id,"revoke_sessions"),"Revoke all recorded refresh sessions for this user?")} className="rounded-xl bg-rose-800 px-3 py-2 text-sm font-bold flex justify-center gap-2"><FiKey/> Revoke sessions</button></div>
      <section><h4 className="font-bold mb-2">Recent visits</h4>{selected.recent_visits?.map((v,i)=><div key={i} className="border-l border-emerald-600 pl-3 py-2 text-xs"><b>{v.destination}</b><span className="block text-slate-500">{date(v.viewed_at)}</span></div>)}{!selected.recent_visits?.length&&<p className="text-xs text-slate-500">No visits recorded.</p>}</section>
      <section><h4 className="font-bold mb-2">Role and access history</h4>{selected.role_history?.map((h,i)=><div key={i} className="rounded-lg bg-slate-900 p-3 mb-2 text-xs"><b>{label(h.action)}</b><span className="block text-slate-500">{date(h.timestamp)} by {h.actor||"system"}</span></div>)}{!selected.role_history?.length&&<p className="text-xs text-slate-500">No administrative changes recorded.</p>}</section>
    </div>}</aside></div>}

    {creating&&<div className="fixed inset-0 z-[80] bg-black/75 grid place-items-center p-4"><form onSubmit={create} className="w-full max-w-lg bg-slate-950 border border-slate-700 rounded-2xl p-5 space-y-3"><div className="flex justify-between"><h3 className="font-black text-xl">Create account</h3><button type="button" onClick={()=>setCreating(false)}><FiX/></button></div><div className="grid grid-cols-2 gap-2"><input required placeholder="First name" value={form.first_name} onChange={e=>setForm({...form,first_name:e.target.value})} className="bg-slate-900 border border-slate-700 rounded-xl p-3"/><input placeholder="Last name" value={form.last_name} onChange={e=>setForm({...form,last_name:e.target.value})} className="bg-slate-900 border border-slate-700 rounded-xl p-3"/></div><input required type="email" placeholder="Email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})} className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3"/><input required minLength="8" type="password" placeholder="Temporary password (8+ characters)" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3"/><select value={form.role} onChange={e=>setForm({...form,role:e.target.value})} className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3">{ROLES.map(r=><option key={r} value={r}>{label(r)}</option>)}</select><input placeholder="Managed district (if applicable)" value={form.managed_district} onChange={e=>setForm({...form,managed_district:e.target.value})} className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3"/><p className="text-xs text-slate-500">New accounts start unverified. Administrator roles require a super administrator.</p><button className="w-full bg-amber-400 text-slate-950 rounded-xl p-3 font-black">Create unverified account</button></form></div>}
  </div>
}
