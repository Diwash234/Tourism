import { useCallback, useEffect, useState } from "react"
import { FiArchive, FiCheck, FiChevronLeft, FiChevronRight, FiFlag, FiRefreshCw, FiRotateCcw, FiSearch } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

const states = ["pending", "approved", "flagged", "archived", "all"]
const actionStyle = { approve: "bg-emerald-700", flag: "bg-amber-700", archive: "bg-rose-800", restore: "bg-sky-700" }
const ActionIcon = ({ action }) => action === "approve" ? <FiCheck/> : action === "flag" ? <FiFlag/> : action === "archive" ? <FiArchive/> : <FiRotateCcw/>

export default function ReviewModerationPanel() {
  const { showToast } = useToast()
  const [rows, setRows] = useState([])
  const [count, setCount] = useState(0)
  const [pages, setPages] = useState(1)
  const [page, setPage] = useState(1)
  const [type, setType] = useState("all")
  const [status, setStatus] = useState("pending")
  const [q, setQ] = useState("")
  const [selected, setSelected] = useState([])
  const [note, setNote] = useState("")
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    setBusy(true)
    try {
      const { data } = await adminApi.getReviewModeration({ type, status, q, page, page_size: 25 })
      setRows(data.results || []); setCount(data.count || 0); setPages(data.pages || 1); setSelected([])
    } catch (error) { showToast(error.response?.data?.detail || "Could not load review queue", "error") }
    finally { setBusy(false) }
  }, [type, status, q, page])
  useEffect(() => { const timer = setTimeout(load, 250); return () => clearTimeout(timer) }, [load])
  useEffect(() => setPage(1), [type, status, q])

  const moderate = async (action, targets) => {
    const chosen = targets || rows.filter(row => selected.includes(`${row.type}-${row.id}`))
    if (!chosen.length) return showToast("Select at least one review", "info")
    if (["flag", "archive"].includes(action) && !note.trim()) return showToast("Add a moderation note for flagging or archiving", "info")
    if (!window.confirm(`${action[0].toUpperCase() + action.slice(1)} ${chosen.length} review(s)?`)) return
    setBusy(true)
    try {
      const groups = Object.groupBy ? Object.groupBy(chosen, row => row.type) : chosen.reduce((all, row) => ({ ...all, [row.type]: [...(all[row.type] || []), row] }), {})
      await Promise.all(Object.entries(groups).map(([kind, items]) => adminApi.moderateReviews({ type: kind, ids: items.map(item => item.id), action, note })))
      showToast(`${chosen.length} review(s) updated`, "success"); setNote(""); load()
    } catch (error) { showToast(error.response?.data?.detail || "Moderation action denied", "error") }
    finally { setBusy(false) }
  }
  const toggle = row => setSelected(current => {
    const key = `${row.type}-${row.id}`
    return current.includes(key) ? current.filter(item => item !== key) : [...current, key]
  })

  return <div className="space-y-4 text-slate-100">
    <header><h2 className="text-2xl font-black">Review moderation</h2><p className="text-xs text-slate-400">Destination and hotel reviews share one audited queue. Archive preserves records; approved reviews are public.</p></header>
    <div className="grid md:grid-cols-[1fr_160px_160px_auto] gap-2 bg-slate-950 border border-slate-700 rounded-2xl p-3">
      <label className="relative"><FiSearch className="absolute left-3 top-3 text-slate-500"/><input value={q} onChange={event => setQ(event.target.value)} placeholder="Review, user, destination or hotel" className="w-full bg-slate-900 border border-slate-700 rounded-xl py-2.5 pl-9 pr-3 text-sm"/></label>
      <select value={type} onChange={event => setType(event.target.value)} className="bg-slate-900 border border-slate-700 rounded-xl px-3 text-sm"><option value="all">All types</option><option value="destination">Destinations</option><option value="hotel">Hotels</option></select>
      <select value={status} onChange={event => setStatus(event.target.value)} className="bg-slate-900 border border-slate-700 rounded-xl px-3 text-sm">{states.map(item => <option key={item} value={item}>{item[0].toUpperCase()+item.slice(1)}</option>)}</select>
      <button onClick={load} className="px-3 rounded-xl bg-slate-800 flex items-center justify-center gap-1"><FiRefreshCw className={busy ? "animate-spin" : ""}/> Refresh</button>
    </div>

    <div className="bg-slate-950 border border-slate-700 rounded-2xl overflow-hidden">
      <div className="p-3 border-b border-slate-800 flex flex-wrap gap-2 items-center"><span className="text-xs text-slate-400 mr-auto">{count} reviews · {selected.length} selected</span><input value={note} onChange={event=>setNote(event.target.value)} placeholder="Moderation note" className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs"/>{["approve","flag","archive","restore"].map(action=><button key={action} disabled={!selected.length||busy} onClick={()=>moderate(action)} className={`${actionStyle[action]} disabled:opacity-30 px-3 py-2 rounded-lg capitalize text-xs font-bold flex gap-1`}><ActionIcon action={action}/>{action}</button>)}</div>
      <div className="overflow-x-auto"><table className="w-full text-sm"><thead className="bg-slate-900 text-slate-400 text-[11px] uppercase"><tr><th className="p-3"></th><th className="p-3 text-left">Review</th><th className="p-3 text-left">Subject</th><th className="p-3 text-left">User</th><th className="p-3 text-left">State</th><th className="p-3 text-right">Quick actions</th></tr></thead><tbody className="divide-y divide-slate-800">{rows.map(row=><tr key={`${row.type}-${row.id}`} className="hover:bg-slate-900/70"><td className="p-3"><input type="checkbox" checked={selected.includes(`${row.type}-${row.id}`)} onChange={()=>toggle(row)}/></td><td className="p-3 max-w-md"><p className="text-white whitespace-pre-wrap">{row.comment || <i className="text-slate-500">No written comment</i>}</p>{row.rating && <span className="text-amber-300 text-xs">{"★".repeat(row.rating)}{"☆".repeat(5-row.rating)}</span>}{row.moderation_note && <p className="text-[10px] text-amber-300 mt-1">Note: {row.moderation_note}</p>}</td><td className="p-3"><b>{row.subject}</b><span className="block text-[10px] text-slate-500 capitalize">{row.type}</span></td><td className="p-3 text-xs text-slate-400">{row.user}<span className="block">{new Date(row.created_at).toLocaleDateString()}</span></td><td className="p-3"><span className={`px-2 py-1 rounded-full text-xs ${row.status === "approved" ? "bg-emerald-500/15 text-emerald-300" : row.status === "flagged" ? "bg-amber-500/15 text-amber-300" : row.status === "archived" ? "bg-rose-500/15 text-rose-300" : "bg-sky-500/15 text-sky-300"}`}>{row.status}</span></td><td className="p-3"><div className="flex justify-end gap-1">{row.status !== "approved"&&<button onClick={()=>moderate("approve",[row])} className="p-2 bg-emerald-800 rounded-lg" title="Approve"><FiCheck/></button>}{row.status !== "flagged"&&<button onClick={()=>moderate("flag",[row])} className="p-2 bg-amber-800 rounded-lg" title="Flag"><FiFlag/></button>}{row.status !== "archived"?<button onClick={()=>moderate("archive",[row])} className="p-2 bg-rose-900 rounded-lg" title="Archive"><FiArchive/></button>:<button onClick={()=>moderate("restore",[row])} className="p-2 bg-sky-800 rounded-lg" title="Restore to pending"><FiRotateCcw/></button>}</div></td></tr>)}{!busy&&!rows.length&&<tr><td colSpan="6" className="p-12 text-center text-slate-500">No reviews match this queue.</td></tr>}</tbody></table></div>
      <div className="p-3 border-t border-slate-800 flex justify-end items-center gap-3 text-xs"><button disabled={page<=1} onClick={()=>setPage(value=>value-1)} className="p-2 disabled:opacity-30"><FiChevronLeft/></button><span>Page {page} of {pages}</span><button disabled={page>=pages} onClick={()=>setPage(value=>value+1)} className="p-2 disabled:opacity-30"><FiChevronRight/></button></div>
    </div>
  </div>
}
