import { useEffect, useState, useRef } from "react"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"
import { FiSend, FiUser, FiShield, FiPaperclip, FiRefreshCw, FiCheckCircle } from "react-icons/fi"

const statuses = ["new", "read", "in_progress", "waiting_user", "replied", "resolved", "closed", "archived"]

export default function FeedbackWorkspace() {
  const { showToast } = useToast()
  const [rows, setRows] = useState([])
  const [selected, setSelected] = useState(null)
  const [filter, setFilter] = useState("")
  const [reply, setReply] = useState("")
  const [internal, setInternal] = useState(false)
  const [sending, setSending] = useState(false)
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const load = () => {
    setLoading(true)
    adminApi.getFeedback(filter ? { status: filter } : {})
      .then(({ data }) => {
        const list = Array.isArray(data) ? data : []
        setRows(list)
        if (selected) {
          const updated = list.find((x) => x.id === selected.id)
          if (updated) setSelected(updated)
        } else if (list.length > 0) {
          setSelected(list[0])
        }
      })
      .catch(() => setRows([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [filter])

  useEffect(() => {
    if (selected && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [selected?.messages])

  const update = async (patch) => {
    if (!selected) return
    await adminApi.updateFeedbackThread(selected.id, patch)
    showToast("Thread updated", "success")
    load()
  }

  const send = async (e) => {
    if (e) e.preventDefault()
    if (!reply.trim() || !selected) return
    setSending(true)
    try {
      await adminApi.replyFeedback(selected.id, reply, internal)
      setReply("")
      setInternal(false)
      showToast(internal ? "Internal note added" : "Reply sent to traveler", "success")
      load()
    } catch {
      showToast("Could not send reply", "error")
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="grid lg:grid-cols-[340px_1fr] gap-5 min-h-[580px]">
      {/* Thread List Sidebar */}
      <aside className="bg-slate-950 border border-slate-800 rounded-2xl p-4 flex flex-col space-y-3">
        <div className="flex justify-between items-center">
          <h3 className="text-xs font-black uppercase text-slate-300 tracking-wider">Support Threads</h3>
          <button type="button" onClick={load} className="p-1 rounded bg-slate-900 text-slate-400 hover:text-white" title="Refresh">
            <FiRefreshCw size={13} className={loading ? "animate-spin" : ""} />
          </button>
        </div>

        <select
          className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs focus:outline-none focus:border-amber-400"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        >
          <option value="">All Status Filter</option>
          {statuses.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

        <div className="flex-1 space-y-2 max-h-[64vh] overflow-y-auto pr-1 text-xs">
          {rows.length === 0 ? (
            <p className="p-6 text-center text-slate-500">No support threads found.</p>
          ) : (
            rows.map((r) => {
              const active = selected?.id === r.id
              return (
                <button
                  key={r.id}
                  type="button"
                  onClick={() => setSelected(r)}
                  className={`w-full text-left p-3 rounded-xl border transition-all space-y-1 block ${
                    active
                      ? "bg-amber-400 text-slate-950 border-amber-400 font-bold shadow"
                      : "bg-slate-900 text-slate-300 border-slate-800 hover:border-slate-700"
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <b className="truncate max-w-[170px]">{r.subject}</b>
                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-mono uppercase ${
                      active ? "bg-slate-950 text-amber-300 font-bold" : "bg-slate-800 text-slate-300"
                    }`}>
                      {r.status}
                    </span>
                  </div>
                  <p className={`text-[11px] truncate ${active ? "text-slate-900" : "text-slate-400"}`}>
                    {r.name || r.email || "Visitor"} · {r.priority}
                  </p>
                </button>
              )
            })
          )}
        </div>
      </aside>

      {/* Main Conversation & Action Workspace */}
      <section className="bg-slate-950 border border-slate-800 rounded-2xl p-5 flex flex-col space-y-4">
        {selected ? (
          <>
            {/* Header */}
            <div className="border-b border-slate-800 pb-3 flex justify-between items-start">
              <div>
                <span className="text-[10px] uppercase font-bold text-amber-400 tracking-wider block mb-1">
                  Support Ticket #{selected.id} · Category: {selected.category}
                </span>
                <h2 className="text-xl font-black text-white">{selected.subject}</h2>
                <p className="text-xs text-slate-400 mt-1">
                  User: <b className="text-slate-200">{selected.name || "Anonymous"}</b> ({selected.email || "No email recorded"})
                </p>
              </div>
              <span className="px-3 py-1 rounded-full bg-emerald-950 text-emerald-300 text-xs font-mono font-bold uppercase border border-emerald-800">
                {selected.status}
              </span>
            </div>

            {/* Controls Bar */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs">
              <div>
                <label className="text-[10px] font-bold text-slate-400 block mb-1">Update Status</label>
                <select
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none"
                  value={selected.status}
                  onChange={(e) => update({ status: e.target.value })}
                >
                  {statuses.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-400 block mb-1">Set Priority</label>
                <select
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none"
                  value={selected.priority}
                  onChange={(e) => update({ priority: e.target.value })}
                >
                  <option value="low">Low</option>
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-400 block mb-1">Assign Staff User ID</label>
                <input
                  type="text"
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none"
                  placeholder="e.g. 5"
                  value={selected.assigned_to || ""}
                  onChange={(e) => setSelected({ ...selected, assigned_to: e.target.value })}
                  onBlur={() => update({ assigned_to: selected.assigned_to || null })}
                />
              </div>
            </div>

            {/* Evidence media attachments */}
            {selected.evidence?.length > 0 && (
              <div className="space-y-1">
                <span className="text-xs font-bold text-slate-300 block flex items-center gap-1">
                  <FiPaperclip size={14} /> Attached Evidence ({selected.evidence.length})
                </span>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {selected.evidence.map((item) => (
                    item.media_type === "image" ? (
                      <a key={item.id} href={item.url} target="_blank" rel="noreferrer" className="block rounded-lg overflow-hidden border border-slate-700">
                        <img src={item.url} alt={item.caption || "Evidence"} className="h-20 w-full object-cover" />
                      </a>
                    ) : (
                      <a key={item.id} href={item.url} target="_blank" rel="noreferrer" className="p-3 bg-slate-900 border border-slate-800 rounded-lg text-amber-300 text-xs block">
                        📹 Video Evidence #{item.id}
                      </a>
                    )
                  ))}
                </div>
              </div>
            )}

            {/* Conversation Messages */}
            <div className="flex-1 overflow-y-auto space-y-3 p-4 bg-slate-900/60 rounded-2xl border border-slate-800 max-h-[380px] text-xs">
              {/* Opener message */}
              <div className="p-3.5 rounded-2xl bg-amber-950/40 border border-amber-800/40 text-amber-100 space-y-1">
                <div className="font-bold text-[11px] text-amber-300 flex items-center gap-1">
                  <FiUser size={13} /> {selected.name || selected.email || "User"} (Initial Request)
                </div>
                <p className="leading-relaxed">{selected.message}</p>
                <span className="text-[9px] text-amber-400/60 block text-right">
                  {new Date(selected.created_at).toLocaleString()}
                </span>
              </div>

              {selected.messages?.map((m) => {
                if (m.is_internal) {
                  return (
                    <div key={m.id} className="p-3 rounded-xl bg-amber-950/90 border border-amber-600/50 text-amber-200 text-xs space-y-1">
                      <b className="text-amber-300 text-[10px] uppercase font-bold block">🔒 Internal Staff Note ({m.sender}):</b>
                      <p>{m.body}</p>
                    </div>
                  )
                }
                const isAdmin = m.sender && (m.sender.includes("admin") || m.sender.includes("staff") || m.sender !== selected.email)
                return (
                  <div
                    key={m.id}
                    className={`p-3.5 rounded-2xl max-w-[85%] text-xs space-y-1 ${
                      isAdmin
                        ? "bg-purple-950/90 border border-purple-700/60 text-purple-100 ml-auto text-right"
                        : "bg-slate-900 border border-slate-800 text-slate-200 mr-auto text-left"
                    }`}
                  >
                    <div className="font-bold text-[11px] flex items-center gap-1 justify-end">
                      <span className={isAdmin ? "text-purple-300" : "text-emerald-300"}>{m.sender}</span>
                      {isAdmin ? <FiShield size={13} className="text-purple-300" /> : <FiUser size={13} className="text-emerald-300" />}
                    </div>
                    <p className="leading-relaxed">{m.body}</p>
                    <span className="text-[9px] opacity-60 block">
                      {new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                )
              })}
              <div ref={messagesEndRef} />
            </div>

            {/* Reply composer */}
            <form onSubmit={send} className="space-y-2 text-xs pt-1">
              <textarea
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-amber-400"
                rows="3"
                value={reply}
                onChange={(e) => setReply(e.target.value)}
                placeholder="Type your response to the user, or add an internal staff note..."
              />
              <div className="flex justify-between items-center">
                <label className="text-xs text-slate-300 flex items-center gap-2 font-bold cursor-pointer">
                  <input
                    type="checkbox"
                    checked={internal}
                    onChange={(e) => setInternal(e.target.checked)}
                    className="accent-amber-400 rounded"
                  />
                  🔒 Mark as Internal Staff Note (hidden from traveler)
                </label>
                <button
                  type="submit"
                  disabled={sending || !reply.trim()}
                  className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-black flex items-center gap-2 shadow disabled:opacity-50"
                >
                  <FiSend size={14} /> {sending ? "Sending..." : internal ? "Add Internal Note" : "Send Reply to Traveler"}
                </button>
              </div>
            </form>
          </>
        ) : (
          <p className="text-slate-500 text-sm">Select a support thread from the list to view and chat.</p>
        )}
      </section>
    </div>
  )
}
