import { useCallback, useEffect, useState, useRef } from "react"
import { Link } from "react-router-dom"
import { FiAlertCircle, FiBriefcase, FiCheck, FiCheckCircle, FiClock, FiRefreshCw, FiX } from "react-icons/fi"
import adminApi from "../api/adminApi"
import adminPanelApi from "../api/adminPanelApi"
import useAuth from "../hooks/useAuth"
import { userDisplayName } from "../utils/placeUtils"
import useToast from "../hooks/useToast"
import CMSPanel from "../components/admin/CMSPanel"
import TravelExpenditureForm from "../components/forms/TravelExpenditureForm"
import RiskAssessmentForm from "../components/forms/RiskAssessmentForm"
import SupportDeskPanel from "../components/admin/SupportDeskPanel"
import HotelOpsPanel from "../components/admin/HotelOpsPanel"
import ContentOpsPanel from "../components/admin/ContentOpsPanel"
import MediaPanel from "../components/admin/MediaPanel"

const names = { destinations: "Destination Queue", images: "Image Review", budget: "Budget Surveys", safety: "Safety Reports", reviews: "Review Queue", hotels: "Assigned Hotels", restaurants: "Restaurant Queue", transportation: "Transport Routes", travel_plans: "Travel Plans", content: "Content Drafts", feedback: "Feedback Queue" }
const paths = Object.fromEntries(Object.keys(names).map(key => [key, `/staff/${key.replace("_", "-")}`]))
const permits = (caps, module, action) => caps?.[module]?.includes(action) || caps?.[module]?.includes("*")

const STATUS_STYLE = {
  pending: "bg-slate-100 text-slate-600",
  in_progress: "bg-sky-100 text-sky-700",
  blocked: "bg-rose-100 text-rose-700",
  in_review: "bg-amber-100 text-amber-800",
  completed: "bg-emerald-100 text-emerald-700",
  cancelled: "bg-slate-100 text-slate-400 line-through",
}
const NOTE_ACTIONS = {
  complete: { label: "Complete task", placeholder: "What did you accomplish? (required)", cta: "Mark Completed" },
  block: { label: "Block task", placeholder: "What is blocking this task? (required)", cta: "Block Task" },
  escalate: { label: "Escalate task", placeholder: "Why does this need escalation? (required)", cta: "Escalate" },
  submit_review: { label: "Submit for review", placeholder: "Summary of your work (optional)", cta: "Submit for Review" },
  reject: { label: "Reject submission", placeholder: "What needs to change? (required)", cta: "Reject & Return" },
  approve: { label: "Approve submission", placeholder: "Approval note (optional)", cta: "Approve & Complete" },
}
const TASK_FILTERS = [
  { id: "all", label: "All" },
  { id: "pending", label: "Pending" },
  { id: "in_progress", label: "In Progress" },
  { id: "blocked", label: "Blocked" },
  { id: "in_review", label: "In Review" },
  { id: "completed", label: "Completed" },
  { id: "overdue", label: "Overdue" },
]
const greetingWord = () => { const h = new Date().getHours(); return h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening" }

export default function StaffDashboard({ module = "dashboard" }) {
  const { showToast } = useToast()
  const { user } = useAuth() || {}
  const canReview = ["admin", "super_admin", "tourism_admin"].includes(user?.role) || user?.is_superuser
  const [perf, setPerf] = useState(null)
  const [taskModal, setTaskModal] = useState(null)
  const [modalNote, setModalNote] = useState("")
  const [taskFilter, setTaskFilter] = useState("all")
  const [data, setData] = useState({ results: [], tasks: [], task_summary: {}, queue_counts: {}, capabilities: {} })
  const [loading, setLoading] = useState(true)
  const loadInFlight = useRef(false)
  const load = useCallback(async () => {
    if (loadInFlight.current) return
    loadInFlight.current = true
    setLoading(true)
    try {
      setData((await adminApi.getStaffWorkspace(module)).data)
      if (module === "dashboard") {
        adminPanelApi.myPerformance().then(({ data: p }) => setPerf(p)).catch(() => setPerf(null))
      }
    }
    catch (error) { showToast(error.response?.data?.detail || "This workspace is not assigned to you", "error") }
    finally { setLoading(false); loadInFlight.current = false }
  }, [module])
  useEffect(() => {
    // Deferred one tick so the loader's synchronous setLoading(true) runs
    // outside the effect flush (react-hooks/set-state-in-effect).
    const t = setTimeout(() => load(), 0)
    return () => clearTimeout(t)
  }, [load])

  const act = async (payload, confirmation) => {
    if (confirmation && !window.confirm(confirmation)) return
    try { const { data: result } = await adminApi.runStaffWorkspaceAction(payload); showToast(result.message, "success"); load() }
    catch (error) { showToast(error.response?.data?.detail || "Action denied", "error") }
  }
  const queueAction = (row, action) => act({ module, id: row.id, type: row.type, action }, `${action[0].toUpperCase()+action.slice(1)} ${row.title}?`)

  const runTaskAction = async (task, action, note = "") => {
    try {
      await adminPanelApi.taskAction(task.id, action, note)
      showToast(`Task ${action.replaceAll("_", " ")} recorded`, "success")
      setTaskModal(null)
      setModalNote("")
      load()
    } catch (error) { showToast(error.response?.data?.detail || "Action denied", "error") }
  }

  const openTaskModal = (task, action) => { setModalNote(""); setTaskModal({ task, action }) }

  const todayStr = new Date().toISOString().slice(0, 10)
  const openTasks = (data.tasks || []).filter((t) => !["completed", "cancelled"].includes(t.status))
  const todaysWork = openTasks
    .filter((t) => t.priority === "urgent" || (t.due_date && t.due_date <= todayStr))
    .slice(0, 6)
  const filteredTasks = (data.tasks || []).filter((t) => {
    if (taskFilter === "all") return true
    if (taskFilter === "overdue") return !["completed", "cancelled"].includes(t.status) && t.due_date && t.due_date < todayStr
    return t.status === taskFilter
  })

  return <div className="space-y-6">
    <header className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 border-b pb-4"><div><span className="text-xs uppercase tracking-widest font-black text-[#102A2E]">Capability-scoped operations</span><h1 className="text-3xl font-black text-slate-900 flex items-center gap-2"><FiBriefcase className="text-[#102A2E]"/>{module === "dashboard" ? "Staff Operations Desk" : names[module]}</h1><p className="text-sm text-slate-500">Only records in your backend-assigned scope are shown. Hidden modules are also denied by the API.</p>{data.managed_districts?.length > 0 && <p className="text-xs text-amber-700 mt-1">Assigned districts: {data.managed_districts.join(", ")}</p>}</div><button onClick={load} className="px-4 py-2 bg-white border rounded-xl text-sm font-bold flex items-center justify-center gap-2"><FiRefreshCw className={loading ? "animate-spin" : ""}/> Refresh</button></header>

    {module === "dashboard" ? <>
      <div>
        <h2 className="text-2xl font-black text-slate-900">{greetingWord()}, {userDisplayName(user) || "team member"}</h2>
        <p className="text-sm text-slate-500">Here is what requires your attention today. Only work assigned to your staff profile is shown — other admin tools stay hidden.</p>
      </div>

      {todaysWork.length > 0 && (
        <section className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
          <h2 className="font-black text-amber-900 mb-2">⚡ Today&apos;s Work</h2>
          <div className="space-y-2">
            {todaysWork.map((t) => (
              <div key={t.id} className="flex flex-col sm:flex-row sm:items-center gap-2 rounded-xl bg-white border border-amber-100 px-3 py-2">
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase w-fit ${t.priority === "urgent" ? "bg-rose-100 text-rose-700" : "bg-amber-100 text-amber-800"}`}>{t.priority}</span>
                <div className="min-w-0 flex-1">
                  <b className="text-sm text-slate-900 block truncate">{t.title}</b>
                  <span className="text-xs text-slate-500">Due {t.due_date && t.due_date < todayStr ? <span className="text-rose-600 font-bold">overdue ({t.due_date})</span> : (t.due_date || "not set")}{t.hotel ? ` · ${t.hotel}` : ""}</span>
                </div>
                <button onClick={() => (["pending", "blocked"].includes(t.status) ? runTaskAction(t, "start") : openTaskModal(t, "submit_review"))} className="px-3 py-1.5 bg-[#1D5146] text-white rounded-lg text-xs font-bold whitespace-nowrap">
                  {["pending", "blocked"].includes(t.status) ? "Start Task" : "Open Task"}
                </button>
              </div>
            ))}
          </div>
        </section>
      )}

      {perf && (
        <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            ["Completed", perf.tasks_completed, "text-emerald-700"],
            ["On-time rate", perf.on_time_rate != null ? `${perf.on_time_rate}%` : "—", "text-[#1D5146]"],
            ["In progress", perf.in_progress, "text-sky-700"],
            ["Blocked", perf.blocked, perf.blocked ? "text-rose-600" : "text-slate-400"],
            ["Overdue", perf.overdue_open, perf.overdue_open ? "text-rose-600" : "text-slate-400"],
            ["Escalations", perf.escalations, "text-amber-700"],
          ].map(([label, value, cls]) => (
            <div key={label} className="bg-white border rounded-2xl p-3 text-center">
              <b className={`text-2xl ${cls}`}>{value ?? 0}</b>
              <p className="text-[10px] text-slate-500 uppercase font-bold">{label}</p>
            </div>
          ))}
        </section>
      )}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">{Object.entries(data.task_summary || {}).map(([key, value]) => <div key={key} className="bg-white border rounded-2xl p-4"><b className={`text-3xl ${key === "overdue" && value ? "text-rose-600" : "text-[#1D5146]"}`}>{value || 0}</b><p className="text-xs text-slate-500 capitalize">{key.replaceAll("_", " ")} assigned tasks</p></div>)}</div>
      <section><h2 className="font-black text-slate-900 mb-3">Assigned module queues</h2><div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">{Object.entries(data.queue_counts || {}).map(([key, value]) => <Link key={key} to={paths[key]} className="bg-slate-900 text-white rounded-2xl p-4 hover:bg-[#102A2E]"><b className="text-3xl">{value}</b><p className="text-xs text-slate-300">{names[key] || key}</p></Link>)}{!loading && !Object.keys(data.queue_counts || {}).length && <p className="text-sm text-slate-500">No operational modules have been assigned. Contact an administrator.</p>}</div></section>
    </> : <>
      {module === "content" && permits(data.capabilities, "content", "view") && <CMSPanel />}
      {module === "content" && permits(data.capabilities, "content", "approve") && data.results?.length > 0 && <div className="bg-white border rounded-2xl p-4 text-xs text-slate-500">Use Publish on a draft section below, or edit live dashboard blocks in the studio above.</div>}
      {(module === "budget" && permits(data.capabilities, module, "add")) && <details className="bg-white border rounded-2xl p-5"><summary className="font-black cursor-pointer">Add verified expenditure survey</summary><div className="mt-4 max-w-2xl"><TravelExpenditureForm onSuccess={load}/></div></details>}
      {(module === "safety" && permits(data.capabilities, module, "add")) && <details className="bg-white border rounded-2xl p-5"><summary className="font-black cursor-pointer">Add field safety report</summary><div className="mt-4 max-w-2xl"><RiskAssessmentForm onSuccess={load}/></div></details>}
      {module === "feedback" && <SupportDeskPanel />}
      {(module === "hotels" || module === "bookings") && <HotelOpsPanel module={module} />}
      {module === "destinations" && <ContentOpsPanel canReview={canReview} />}
      {module === "images" && <MediaPanel canReview={canReview} />}
      {!["feedback", "hotels", "bookings", "destinations", "images"].includes(module) && <section className="bg-white border rounded-2xl overflow-hidden"><div className="p-4 border-b flex justify-between"><b>{names[module]}</b><span className="text-xs text-slate-500">{data.results?.length || 0} records loaded</span></div><div className="divide-y">{data.results?.map(row => <article key={`${row.type || module}-${row.id}`} className="p-4 flex flex-col md:flex-row gap-3"><div className="min-w-0 flex-1">{row.image_url && <img src={row.image_url} alt="Review candidate" className="w-28 h-20 object-cover rounded-lg float-left mr-3"/>}{row.video_url && <video src={row.video_url} controls className="mb-2 w-40 max-h-24 rounded-lg" />}{row.type === "video" && <span className="mr-2 text-[10px] uppercase tracking-widest text-sky-700">Video</span>}<div className="flex gap-2 items-center"><h3 className="font-black text-slate-900">{row.title}</h3><span className="text-[10px] px-2 py-0.5 bg-slate-100 rounded-full">{row.status}</span></div><p className="text-xs text-[#102A2E]">{row.subtitle}</p><p className="text-sm text-slate-600 mt-1 line-clamp-3">{row.description}</p>{row.amount != null && <p className="text-sm font-bold text-emerald-700 mt-1">NPR {Number(row.amount).toLocaleString()}</p>}</div>{["destinations", "images", "reviews"].includes(module) && permits(data.capabilities, module, "approve") && <div className="flex gap-2 self-start"><button onClick={() => queueAction(row, "approve")} className="p-2.5 bg-emerald-700 text-white rounded-xl" title="Approve"><FiCheck/></button><button onClick={() => queueAction(row, "reject")} className="p-2.5 bg-rose-700 text-white rounded-xl" title={module === "reviews" ? "Flag" : "Reject"}><FiX/></button></div>}{module==="restaurants"&&<div className="flex gap-1">{permits(data.capabilities,module,"approve")&&<><button onClick={()=>queueAction(row,"publish")} className="p-2 bg-emerald-700 text-white rounded-lg">Publish</button><button onClick={()=>queueAction(row,"verify")} className="p-2 bg-sky-700 text-white rounded-lg">Verify</button></>}{permits(data.capabilities,module,"delete")&&<button onClick={()=>queueAction(row,"archive")} className="p-2 bg-rose-700 text-white rounded-lg">Archive</button>}</div>}{module==="transportation"&&<div className="flex gap-1">{permits(data.capabilities,module,"approve")&&<button onClick={()=>queueAction(row,"verify")} className="p-2 bg-sky-700 text-white rounded-lg">Verify</button>}{permits(data.capabilities,module,"delete")&&<button onClick={()=>queueAction(row,"archive")} className="p-2 bg-rose-700 text-white rounded-lg">Archive</button>}</div>}{module==="travel_plans"&&permits(data.capabilities,module,"change")&&<div className="flex gap-1"><button onClick={()=>queueAction(row,"activate")} className="p-2 bg-emerald-700 text-white rounded-lg">Activate</button><button onClick={()=>queueAction(row,"complete")} className="p-2 bg-sky-700 text-white rounded-lg">Complete</button></div>}{module==="content"&&permits(data.capabilities,module,"approve")&&<div className="flex gap-1"><button onClick={()=>queueAction(row,"publish")} className="p-2 bg-emerald-700 text-white rounded-lg">Publish</button><button onClick={()=>queueAction(row,"unpublish")} className="p-2 bg-amber-700 text-white rounded-lg">Draft</button></div>}</article>)}{!loading && !data.results?.length && <p className="p-12 text-center text-slate-500">Your assigned queue is empty.</p>}</div></section>}
    </>}

    <section className="bg-white border rounded-2xl overflow-hidden">
      <div className="p-4 border-b flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="font-black text-slate-900">My Work Queue</h2>
          <p className="text-xs text-slate-500">Start, complete with a note, submit for review, block or escalate. Every action is reported to the assigning administrator and audited.</p>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {TASK_FILTERS.map((f) => (
            <button key={f.id} onClick={() => setTaskFilter(f.id)} aria-pressed={taskFilter === f.id}
              className={`px-2.5 py-1 rounded-full text-[11px] font-bold transition ${taskFilter === f.id ? "bg-[#102A2E] text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}>
              {f.label}
            </button>
          ))}
        </div>
      </div>
      <div className="divide-y">
        {filteredTasks.map((task) => (
          <div key={task.id} className="p-4 flex flex-col gap-3">
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap gap-2 items-center">
                  <b className="text-slate-900">{task.title}</b>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${STATUS_STYLE[task.status] || STATUS_STYLE.pending}`}>{task.status.replaceAll("_", " ")}</span>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full ${task.priority === "urgent" ? "bg-rose-100 text-rose-700" : "bg-amber-100 text-amber-700"}`}>{task.priority}</span>
                  {task.is_escalated && <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-600 text-white font-bold">ESCALATED</span>}
                </div>
                <p className="text-sm text-slate-600 mt-1">{task.description}</p>
                <p className="text-xs text-slate-400 mt-1"><FiClock className="inline"/> Due {task.due_date && task.due_date < todayStr && !["completed", "cancelled"].includes(task.status) ? <span className="text-rose-600 font-bold">{task.due_date} (overdue)</span> : (task.due_date || "not set")}{task.hotel ? ` · ${task.hotel}` : ""}</p>
                {task.completion_note && <p className="text-xs text-emerald-800 bg-emerald-50 border border-emerald-100 rounded-lg px-2 py-1 mt-2"><b>Note:</b> {task.completion_note}</p>}
                {task.review_note && <p className="text-xs text-amber-900 bg-amber-50 border border-amber-100 rounded-lg px-2 py-1 mt-1"><b>Review:</b> {task.review_note}</p>}
                {task.blocked_reason && task.status === "blocked" && <p className="text-xs text-rose-800 bg-rose-50 border border-rose-100 rounded-lg px-2 py-1 mt-1"><b>Blocked:</b> {task.blocked_reason}</p>}
              </div>
              <div className="flex flex-wrap gap-2 self-start">
                {["pending", "blocked"].includes(task.status) && (
                  <button onClick={() => runTaskAction(task, "start")} className="px-3 py-2 bg-sky-700 hover:bg-sky-800 text-white rounded-xl text-xs font-bold"><FiAlertCircle className="inline"/> Start</button>
                )}
                {["pending", "in_progress", "blocked"].includes(task.status) && (
                  <>
                    <button onClick={() => openTaskModal(task, "complete")} className="px-3 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded-xl text-xs font-bold"><FiCheckCircle className="inline"/> Complete</button>
                    <button onClick={() => openTaskModal(task, "submit_review")} className="px-3 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-bold">Submit for Review</button>
                    <button onClick={() => openTaskModal(task, "block")} className="px-3 py-2 bg-slate-200 hover:bg-slate-300 text-slate-800 rounded-xl text-xs font-bold">Block</button>
                    <button onClick={() => openTaskModal(task, "escalate")} className="px-3 py-2 bg-rose-700 hover:bg-rose-800 text-white rounded-xl text-xs font-bold">Escalate</button>
                  </>
                )}
                {task.status === "in_review" && !canReview && (
                  <span className="text-xs text-amber-700 font-bold px-3 py-2 bg-amber-50 rounded-xl">Awaiting administrator review…</span>
                )}
                {task.status === "in_review" && canReview && (
                  <>
                    <button onClick={() => openTaskModal(task, "approve")} className="px-3 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded-xl text-xs font-bold">Approve</button>
                    <button onClick={() => openTaskModal(task, "reject")} className="px-3 py-2 bg-rose-700 hover:bg-rose-800 text-white rounded-xl text-xs font-bold">Reject</button>
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
        {!loading && !filteredTasks.length && (
          <p className="p-8 text-center text-slate-500 text-sm">
            {taskFilter === "all" ? "No tasks assigned yet — you're all caught up 🎉" : `No ${taskFilter.replaceAll("_", " ")} tasks.`}
          </p>
        )}
      </div>
    </section>

    {taskModal && (
      <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label={NOTE_ACTIONS[taskModal.action].label}>
        <div className="bg-white rounded-3xl p-6 max-w-lg w-full space-y-4 shadow-2xl">
          <div>
            <span className="text-[10px] font-black uppercase tracking-widest text-[#102A2E]">{NOTE_ACTIONS[taskModal.action].label}</span>
            <h3 className="text-lg font-black text-slate-900">{taskModal.task.title}</h3>
          </div>
          <textarea
            value={modalNote}
            onChange={(e) => setModalNote(e.target.value)}
            placeholder={NOTE_ACTIONS[taskModal.action].placeholder}
            rows={4}
            autoFocus
            className="w-full border border-slate-300 rounded-xl p-3 text-sm focus:outline-none focus:border-[#1D5146]"
          />
          <div className="flex justify-end gap-2">
            <button onClick={() => { setTaskModal(null); setModalNote("") }} className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold">Cancel</button>
            <button
              onClick={() => runTaskAction(taskModal.task, taskModal.action, modalNote.trim())}
              className="px-5 py-2 rounded-xl bg-[#1D5146] hover:bg-[#102A2E] text-white text-xs font-black"
            >
              {NOTE_ACTIONS[taskModal.action].cta}
            </button>
          </div>
        </div>
      </div>
    )}
  </div>
}
