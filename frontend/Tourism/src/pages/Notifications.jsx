import { useEffect, useState } from "react"
import { FiCheck, FiMail, FiRefreshCw, FiTrash2 } from "react-icons/fi"
import userApi from "../api/userApi"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"

export default function Notifications() {
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)
  const load = () => { setLoading(true); userApi.getNotifications().then(({data})=>setNotifications(data.results||data||[])).catch(()=>setNotifications([])).finally(()=>setLoading(false)) }
  useEffect(load, [])
  const toggle = async item => { const { data } = item.is_read ? await userApi.markNotificationUnread(item.id) : await userApi.markNotificationRead(item.id); setNotifications(rows=>rows.map(row=>row.id===item.id?data:row)) }
  const remove = async id => { await userApi.deleteNotification(id); setNotifications(rows=>rows.filter(row=>row.id!==id)) }
  const all = async read => { if(read) await userApi.markAllNotificationsRead(); else await userApi.markAllNotificationsUnread(); setNotifications(rows=>rows.map(row=>({...row,is_read:read}))) }
  if (loading) return <Loader />
  const unread=notifications.filter(item=>!item.is_read).length
  return <div className="theme-amber-alt space-y-5"><header className="flex flex-col sm:flex-row sm:items-end justify-between gap-3"><div><h1 className="section-title">Notifications</h1><p className="text-sm text-gray-500">{unread} unread · delivery status is shown honestly for each channel.</p></div><div className="flex gap-2"><button onClick={()=>all(true)} className="btn-outline text-xs"><FiCheck className="inline"/> Mark all read</button><button onClick={()=>all(false)} className="btn-outline text-xs"><FiMail className="inline"/> Mark all unread</button><button onClick={load} className="btn-outline"><FiRefreshCw/></button></div></header>{notifications.length?<div className="space-y-2">{notifications.map(item=><article key={item.id} className={`rounded-2xl border p-4 flex gap-3 ${item.is_read?"bg-white border-gray-200":"bg-amber-50 border-amber-300"}`}><button onClick={()=>toggle(item)} className="flex-1 text-left"><div className="flex flex-wrap gap-2 items-center"><b className="text-gray-900">{item.title}</b><span className="text-[10px] uppercase rounded-full bg-gray-100 px-2 py-0.5">{item.category}</span><span className={`text-[10px] rounded-full px-2 py-0.5 ${item.delivery_status==="sent"?"bg-emerald-100 text-emerald-700":item.delivery_status==="failed"?"bg-rose-100 text-rose-700":"bg-sky-100 text-sky-700"}`}>{item.channel} · {item.delivery_status}</span></div><p className="text-sm text-gray-600 mt-1">{item.message}</p><p className="text-xs text-gray-400 mt-2">{new Date(item.created_at).toLocaleString()}</p></button><button onClick={()=>remove(item.id)} className="self-start p-2 text-rose-600 hover:bg-rose-50 rounded-lg" aria-label="Delete notification"><FiTrash2/></button></article>)}</div>:<EmptyState title="You are all caught up" subtitle="New notifications will appear here."/>}</div>
}
