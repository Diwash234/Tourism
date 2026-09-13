import { useCallback, useEffect, useRef, useState } from "react"
import { FiSend, FiUserPlus, FiCheckCircle } from "react-icons/fi"
import chatbotApi from "../../api/chatbotApi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

/**
 * Live human support inbox (master spec §30 + V6 support workflow).
 *
 * Every traveller chat message is fanned out over the `support_inbox`
 * WebSocket the moment the chat API persists it, so staff see new messages
 * within ~seconds (no polling of the list). The REST endpoints remain the
 * source of truth: this panel reads the inbox, opens a thread, sends admin
 * replies (pushed live to the user's chat socket), assigns conversations to
 * staff, and resolves them. If the socket is unavailable the panel falls
 * back to a short polling refresh so it still works behind a WS-less proxy.
 */
function socketUrl() {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:"
  let token = ""
  try { token = localStorage.getItem("access") || "" } catch { /* ignore */ }
  return `${proto}//${window.location.host}/ws/support/${token ? `?token=${encodeURIComponent(token)}` : ""}`
}

export default function SupportInboxPanel() {
  const { showToast } = useToast()
  const [threads, setThreads] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeId, setActiveId] = useState(null)
  const [thread, setThread] = useState(null)
  const [reply, setReply] = useState("")
  const [sending, setSending] = useState(false)
  const [staff, setStaff] = useState([])
  const [assignTo, setAssignTo] = useState("")
  const [mine, setMine] = useState(false)
  const scrollRef = useRef(null)
  const socketRef = useRef(null)

  const loadInbox = useCallback(() => {
    chatbotApi
      .supportInbox(mine ? { mine: 1 } : undefined)
      .then(({ data }) => setThreads(data.results || []))
      .catch(() => showToast("Could not load support inbox", "error"))
      .finally(() => setLoading(false))
  }, [mine, showToast])

  const openThread = useCallback((id) => {
    setActiveId(id)
    setReply("")
    chatbotApi
      .supportThread(id)
      .then(({ data }) => {
        setThread(data)
        setAssignTo(data.assigned_to || "")
      })
      .catch(() => showToast("Could not open conversation", "error"))
  }, [showToast])

  // Initial load + assignable people (staff, moderators, admins AND guides —
  // per V6 admins can hand a conversation to a staff member or a local guide).
  useEffect(() => {
    loadInbox()
    adminApi
      .getUsers()
      .then(({ data }) => {
        const rows = data.results || data || []
        const assignable = rows
          .filter((u) => ["staff", "guide", "admin", "super_admin", "tourism_admin", "content_moderator"].includes(u.role))
          .filter((u) => u.email)
          .map((u) => ({ email: u.email, role: u.role }))
        setStaff(assignable)
      })
      .catch(() => { /* assignment list optional */ })
  }, [loadInbox])

  // Live socket: new user messages + assignment changes refresh the inbox.
  useEffect(() => {
    let closed = false
    let retry = 0
    let retryTimer = null
    const connect = () => {
      try { socketRef.current = new WebSocket(socketUrl()) } catch { return }
      const ws = socketRef.current
      ws.onopen = () => { retry = 0 }
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === "support.user_message" || data.type === "support.assigned") {
            loadInbox()
            if (data.type === "support.user_message" && activeId === data.conversation_id) {
              openThread(activeId)
            }
          }
        } catch { /* ignore malformed frames */ }
      }
      ws.onclose = () => {
        if (!closed && retry < 5) { retry += 1; retryTimer = setTimeout(connect, 1000 * retry) }
      }
      ws.onerror = () => { try { ws.close() } catch { /* noop */ } }
    }
    connect()
    return () => {
      closed = true
      if (retryTimer) clearTimeout(retryTimer)
      try { socketRef.current?.close() } catch { /* noop */ }
    }
  }, [loadInbox, openThread, activeId])

  // Safety net: light polling keeps the inbox fresh if the socket is down.
  useEffect(() => {
    const t = setInterval(loadInbox, 8000)
    return () => clearInterval(t)
  }, [loadInbox])

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [thread])

  const sendReply = async (e) => {
    e.preventDefault()
    const text = reply.trim()
    if (!text || !activeId) return
    setSending(true)
    try {
      await chatbotApi.supportReply(activeId, text)
      setReply("")
      await openThread(activeId)
      loadInbox()
    } catch {
      showToast("Could not send reply", "error")
    } finally {
      setSending(false)
    }
  }

  const assign = async () => {
    if (!activeId) return
    try {
      const { data } = await chatbotApi.supportAssign({
        conversation_id: activeId,
        assigned_to: assignTo || null,
      })
      setThread((prev) => (prev ? { ...prev, status: data.status, assigned_to: data.assigned_to } : prev))
      loadInbox()
      showToast(assignTo ? `Assigned to ${data.assigned_to}` : "Unassigned", "success")
    } catch (err) {
      showToast(err?.response?.data?.detail || "Could not assign", "error")
    }
  }

  const resolve = async () => {
    if (!activeId) return
    try {
      await chatbotApi.supportAssign({ conversation_id: activeId, status: "resolved" })
      openThread(activeId)
      loadInbox()
      showToast("Conversation resolved", "success")
    } catch {
      showToast("Could not resolve", "error")
    }
  }

  const statusPill = (status) => {
    const map = {
      open: "bg-amber-100 text-amber-800",
      assigned: "bg-sky-100 text-sky-800",
      resolved: "bg-emerald-100 text-emerald-800",
    }
    return <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${map[status] || "bg-slate-200 text-slate-700"}`}>{status}</span>
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h2 className="text-lg font-black text-white">Support Inbox &amp; Live Chat</h2>
          <p className="text-sm text-slate-300">
            Real-time traveller conversations. New messages arrive instantly over WebSocket;
            reply here and it reaches the traveller's chat within seconds.
          </p>
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-200 cursor-pointer">
          <input type="checkbox" checked={mine} onChange={(e) => setMine(e.target.checked)} className="accent-emerald-500" />
          Assigned to me
        </label>
      </div>

      <div className="grid lg:grid-cols-[320px_1fr] gap-4">
        {/* Conversation list */}
        <div className="bg-slate-900/70 border border-slate-600/40 rounded-3xl p-3 max-h-[560px] overflow-y-auto">
          {loading ? (
            <p className="text-slate-400 text-sm p-3">Loading conversations…</p>
          ) : threads.length === 0 ? (
            <p className="text-slate-400 text-sm p-3">No conversations yet.</p>
          ) : (
            <ul className="space-y-2">
              {threads.map((t) => (
                <li key={t.id}>
                  <button
                    type="button"
                    onClick={() => openThread(t.id)}
                    className={`w-full text-left p-3 rounded-2xl border transition ${
                      activeId === t.id
                        ? "bg-emerald-600/20 border-emerald-500/60"
                        : "bg-slate-800/60 border-slate-700/50 hover:border-emerald-500/40"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-bold text-white truncate text-sm">{t.user_email}</span>
                      {statusPill(t.status)}
                    </div>
                    <p className="text-xs text-slate-400 truncate mt-1">{t.last_message || "—"}</p>
                    {t.assigned_to && <p className="text-[11px] text-sky-300 mt-1">→ {t.assigned_to}</p>}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Thread + reply */}
        <div className="bg-slate-900/70 border border-slate-600/40 rounded-3xl p-4 flex flex-col min-h-[560px]">
          {!thread ? (
            <p className="text-slate-400 text-sm m-auto">Select a conversation to view and reply.</p>
          ) : (
            <>
              <div className="flex items-center justify-between gap-3 flex-wrap pb-3 border-b border-slate-700/50">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-white">{thread.messages?.[0] ? `Conversation #${activeId}` : `#${activeId}`}</span>
                  {statusPill(thread.status)}
                </div>
                <div className="flex items-center gap-2">
                  <select
                    value={assignTo}
                    onChange={(e) => setAssignTo(e.target.value)}
                    className="bg-slate-800 border border-slate-600 rounded-xl px-2 py-1 text-sm text-white"
                  >
                    <option value="">Unassigned</option>
                    <option value="me">Assign to me</option>
                    {staff.map((s) => (
                      <option key={s.email} value={s.email}>
                        {s.email} ({s.role})
                      </option>
                    ))}
                  </select>
                  <button type="button" onClick={assign}
                    className="inline-flex items-center gap-1 px-3 py-1 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-sm font-bold">
                    <FiUserPlus /> Assign
                  </button>
                  <button type="button" onClick={resolve}
                    className="inline-flex items-center gap-1 px-3 py-1 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-bold">
                    <FiCheckCircle /> Resolve
                  </button>
                </div>
              </div>

              <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-3 py-4 max-h-[380px]">
                {(thread.messages || []).map((m) => (
                  <div key={m.id} className={`flex ${m.role === "user" ? "justify-start" : "justify-end"}`}>
                    <div className={`max-w-[75%] px-3 py-2 rounded-2xl text-sm ${
                      m.role === "user"
                        ? "bg-slate-700/70 text-slate-100"
                        : m.role === "admin"
                          ? "bg-emerald-600/80 text-white"
                          : "bg-slate-800 text-slate-200"
                    }`}>
                      <p className="text-[10px] uppercase font-bold opacity-70 mb-0.5">
                        {m.role === "user" ? "Traveller" : m.role === "admin" ? "Support" : "Assistant"}
                      </p>
                      {m.content}
                    </div>
                  </div>
                ))}
              </div>

              <form onSubmit={sendReply} className="flex items-center gap-2 pt-3 border-t border-slate-700/50">
                <input
                  value={reply}
                  onChange={(e) => setReply(e.target.value)}
                  placeholder="Type a reply to the traveller…"
                  className="flex-1 bg-slate-800 border border-slate-600 rounded-xl px-3 py-2 text-sm text-white"
                />
                <button type="submit" disabled={sending || !reply.trim()}
                  className="inline-flex items-center gap-1 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-sm font-bold">
                  <FiSend /> {sending ? "Sending…" : "Send"}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
