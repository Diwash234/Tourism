import { useCallback, useEffect, useState } from "react"
import { FiRefreshCw, FiSend, FiUser, FiArrowLeft, FiAlertTriangle, FiCheckCircle, FiClock, FiInbox } from "react-icons/fi"
import adminPanelApi from "../../api/adminPanelApi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

const TABS = [
  { id: "", label: "All Open", key: "open" },
  { id: "waiting_user", label: "Waiting for Customer", key: "waiting_user" },
  { id: "escalated", label: "Escalated", key: "escalated" },
  { id: "urgent", label: "Urgent", key: "urgent" },
  { id: "resolved", label: "Resolved", key: "resolved" },
]

const STATUS_STYLE = {
  new: "bg-rose-100 text-rose-700",
  read: "bg-slate-100 text-slate-600",
  in_progress: "bg-sky-100 text-sky-700",
  waiting_user: "bg-amber-100 text-amber-800",
  replied: "bg-emerald-100 text-emerald-700",
  resolved: "bg-emerald-100 text-emerald-700",
  closed: "bg-slate-100 text-slate-500",
  archived: "bg-slate-100 text-slate-400",
}

/**
 * Customer Support Center (Staff Ops spec §7–10).
 * Staff see only tickets assigned to them plus the unassigned claim pool —
 * scoping and every action are enforced by the backend.
 */
export default function SupportDeskPanel() {
  const { showToast } = useToast()
  const [tab, setTab] = useState("")
  const [data, setData] = useState({ counts: {}, results: [] })
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [reply, setReply] = useState("")
  const [internal, setInternal] = useState(false)
  const [busy, setBusy] = useState(false)

  const load = useCallback(async (status = tab, keepSelection = false) => {
    setLoading(true)
    try {
      const { data: d } = await adminPanelApi.supportTickets(status)
      setData(d)
      if (keepSelection && selected) {
        const fresh = d.results.find((t) => t.id === selected.id)
        setSelected(fresh || null)
      }
    } catch (error) {
      showToast(error.response?.data?.detail || "Support queue unavailable", "error")
    } finally {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, selected])

  useEffect(() => {
    const t = setTimeout(() => load(tab), 0)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab])

  const runAction = async (action, note = "") => {
    if (!selected) return
    setBusy(true)
    try {
      const { data: updated } = await adminPanelApi.supportAction(selected.id, action, note)
      showToast(`Ticket ${action.replaceAll("_", " ")} recorded`, "success")
      setSelected(updated)
      setReply("")
      setInternal(false)
      load(tab, true)
    } catch (error) {
      showToast(error.response?.data?.detail || "Action denied", "error")
    } finally {
      setBusy(false)
    }
  }

  const sendReply = async () => {
    if (!selected || !reply.trim()) return
    setBusy(true)
    try {
      await adminApi.replyFeedback(selected.id, reply.trim(), internal)
      showToast(internal ? "Internal note added" : "Reply sent to customer", "success")
      setReply("")
      setInternal(false)
      load(tab, true)
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not send reply", "error")
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-1.5">
          {TABS.map((t) => (
            <button
              key={t.id || "all"}
              onClick={() => { setTab(t.id); setSelected(null) }}
              aria-pressed={tab === t.id}
              className={`px-3 py-1.5 rounded-full text-xs font-bold transition ${tab === t.id ? "bg-[#102A2E] text-white" : "bg-white border text-slate-600 hover:bg-slate-100"}`}
            >
              {t.label}
              <span className={`ml-1.5 ${tab === t.id ? "text-slate-300" : "text-slate-400"}`}>{data.counts?.[t.key] ?? 0}</span>
            </button>
          ))}
        </div>
        <button onClick={() => load(tab, true)} className="px-3 py-2 bg-white border rounded-xl text-xs font-bold flex items-center gap-2">
          <FiRefreshCw className={loading ? "animate-spin" : ""} /> Refresh
        </button>
      </div>

      {!selected ? (
        <section className="bg-white border rounded-2xl overflow-hidden">
          <div className="p-4 border-b flex justify-between items-center">
            <b className="text-slate-900">Support Tickets</b>
            <span className="text-xs text-slate-500">
              {data.counts?.unassigned ?? 0} unassigned in your claim pool
            </span>
          </div>
          <div className="divide-y">
            {data.results.map((t) => (
              <button
                key={t.id}
                onClick={() => setSelected(t)}
                className="w-full text-left p-4 hover:bg-slate-50 transition flex flex-col sm:flex-row sm:items-center gap-2"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <b className="text-sm text-slate-900 truncate">#{t.id} {t.subject}</b>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${STATUS_STYLE[t.status] || "bg-slate-100"}`}>{t.status.replaceAll("_", " ")}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${t.priority === "urgent" ? "bg-rose-600 text-white" : t.priority === "high" ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-600"}`}>{t.priority}</span>
                    {t.is_escalated && <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-600 text-white font-bold">ESCALATED</span>}
                    {!t.assigned_to && <span className="text-[10px] px-2 py-0.5 rounded-full bg-sky-100 text-sky-700 font-bold">UNASSIGNED</span>}
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    <FiUser className="inline" /> {t.customer_name} · {t.category} · {new Date(t.created_at).toLocaleString()}
                    {t.assigned_to_email ? ` · → ${t.assigned_to_email}` : ""}
                  </p>
                </div>
                <span className="text-xs font-bold text-[#1D5146] whitespace-nowrap">Open Ticket →</span>
              </button>
            ))}
            {!loading && !data.results.length && (
              <p className="p-10 text-center text-slate-500 text-sm"><FiInbox className="inline mr-1" /> No tickets in this view — nothing needs your attention right now.</p>
            )}
          </div>
        </section>
      ) : (
        <section className="bg-white border rounded-2xl overflow-hidden">
          <div className="p-4 border-b flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <button onClick={() => setSelected(null)} className="text-xs font-bold text-slate-500 hover:text-slate-800 flex items-center gap-1 w-fit">
              <FiArrowLeft /> Back to queue
            </button>
            <div className="flex flex-wrap gap-2">
              {!selected.assigned_to && (
                <button onClick={() => runAction("claim")} disabled={busy} className="px-3 py-1.5 bg-sky-700 text-white rounded-lg text-xs font-bold">Claim Ticket</button>
              )}
              {selected.status !== "waiting_user" && !["resolved", "closed"].includes(selected.status) && (
                <button onClick={() => runAction("waiting_user")} disabled={busy} className="px-3 py-1.5 bg-amber-600 text-white rounded-lg text-xs font-bold flex items-center gap-1"><FiClock /> Waiting for Customer</button>
              )}
              {!["resolved", "closed"].includes(selected.status) && (
                <button onClick={() => runAction("escalate", reply.trim() || window.prompt("Escalation reason (required):") || "")} disabled={busy} className="px-3 py-1.5 bg-rose-700 text-white rounded-lg text-xs font-bold flex items-center gap-1"><FiAlertTriangle /> Escalate</button>
              )}
              {["resolved", "closed"].includes(selected.status) ? (
                <button onClick={() => runAction("reopen")} disabled={busy} className="px-3 py-1.5 bg-slate-700 text-white rounded-lg text-xs font-bold">Reopen</button>
              ) : (
                <button onClick={() => runAction("resolve", reply.trim())} disabled={busy} className="px-3 py-1.5 bg-emerald-700 text-white rounded-lg text-xs font-bold flex items-center gap-1"><FiCheckCircle /> Resolve</button>
              )}
            </div>
          </div>

          <div className="p-4 space-y-4">
            <div>
              <h3 className="font-black text-slate-900">#{selected.id} {selected.subject}</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                {selected.customer_name} ({selected.customer_email || "no email"}) · category: {selected.category} · priority: {selected.priority}
                {selected.assigned_to_email ? ` · assigned: ${selected.assigned_to_email}` : " · unassigned"}
              </p>
              {selected.is_escalated && selected.escalation_reason && (
                <p className="text-xs text-rose-800 bg-rose-50 border border-rose-100 rounded-lg px-2 py-1 mt-2"><b>Escalated:</b> {selected.escalation_reason}</p>
              )}
            </div>

            <div className="rounded-xl bg-slate-50 border p-3">
              <p className="text-[10px] uppercase font-black text-slate-500 mb-1">Original request</p>
              <p className="text-sm text-slate-700">{selected.message}</p>
            </div>

            <div className="space-y-2">
              <p className="text-[10px] uppercase font-black text-slate-500">Conversation</p>
              {selected.messages.map((m) => (
                <div key={m.id} className={`rounded-xl px-3 py-2 text-sm border ${m.is_internal ? "bg-amber-50 border-amber-200" : m.sender_is_staff ? "bg-emerald-50 border-emerald-100 ml-6" : "bg-slate-50 border-slate-200 mr-6"}`}>
                  <p className="text-[10px] font-bold text-slate-500 uppercase">
                    {m.is_internal ? "Internal note" : m.sender_is_staff ? "Staff" : "Customer"} · {m.sender} · {new Date(m.created_at).toLocaleString()}
                  </p>
                  <p className="text-slate-700 mt-0.5">{m.body}</p>
                </div>
              ))}
              {!selected.messages.length && <p className="text-xs text-slate-400">No replies yet.</p>}
            </div>

            <div className="space-y-2">
              <textarea
                value={reply}
                onChange={(e) => setReply(e.target.value)}
                rows={3}
                placeholder={internal ? "Internal note — never shown to the customer…" : "Write a reply to the customer…"}
                className="w-full border border-slate-300 rounded-xl p-3 text-sm focus:outline-none focus:border-[#1D5146]"
              />
              <div className="flex flex-wrap items-center justify-between gap-2">
                <label className="text-xs font-bold text-slate-600 flex items-center gap-1.5 cursor-pointer">
                  <input type="checkbox" checked={internal} onChange={(e) => setInternal(e.target.checked)} />
                  Internal note (hidden from customer)
                </label>
                <button onClick={sendReply} disabled={busy || !reply.trim()} className="px-4 py-2 bg-[#1D5146] hover:bg-[#102A2E] disabled:opacity-40 text-white rounded-xl text-xs font-black flex items-center gap-1.5">
                  <FiSend /> {internal ? "Add Internal Note" : "Send Reply"}
                </button>
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  )
}
