import { useCallback, useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { FiAlertCircle, FiBriefcase, FiCheck, FiCheckCircle, FiClock, FiRefreshCw, FiX } from "react-icons/fi"
import adminApi from "../api/adminApi"
import useToast from "../hooks/useToast"
import TravelExpenditureForm from "../components/forms/TravelExpenditureForm"
import RiskAssessmentForm from "../components/forms/RiskAssessmentForm"

const names = { destinations: "Destination Queue", images: "Image Review", budget: "Budget Surveys", safety: "Safety Reports", reviews: "Review Queue", hotels: "Assigned Hotels", restaurants: "Restaurant Queue", transportation: "Transport Routes", travel_plans: "Travel Plans", content: "Content Drafts", feedback: "Feedback Queue" }
const paths = Object.fromEntries(Object.keys(names).map(key => [key, `/staff/${key.replace("_", "-")}`]))
const permits = (caps, module, action) => caps?.[module]?.includes(action) || caps?.[module]?.includes("*")

export default function StaffDashboard({ module = "dashboard" }) {
  const { showToast } = useToast()
  const [data, setData] = useState({ results: [], tasks: [], task_summary: {}, queue_counts: {}, capabilities: {} })
  const [loading, setLoading] = useState(false)
  const load = useCallback(async () => {
    setLoading(true)
    try { setData((await adminApi.getStaffWorkspace(module)).data) }
    catch (error) { showToast(error.response?.data?.detail || "This workspace is not assigned to you", "error") }
    finally { setLoading(false) }
  }, [module])
  useEffect(() => { load() }, [load])

  const act = async (payload, confirmation) => {
    if (confirmation && !window.confirm(confirmation)) return
    try { const { data: result } = await adminApi.runStaffWorkspaceAction(payload); showToast(result.message, "success"); load() }
    catch (error) { showToast(error.response?.data?.detail || "Action denied", "error") }
  }
  const queueAction = (row, action) => act({ module, id: row.id, type: row.type, action }, `${action[0].toUpperCase()+action.slice(1)} ${row.title}?`)

  return <div className="space-y-6">
    <header className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 border-b pb-4"><div><span className="text-xs uppercase tracking-widest font-black text-purple-700">Capability-scoped operations</span><h1 className="text-3xl font-black text-slate-900 flex items-center gap-2"><FiBriefcase className="text-purple-700"/>{module === "dashboard" ? "Staff Operations Desk" : names[module]}</h1><p className="text-sm text-slate-500">Only records in your backend-assigned scope are shown. Hidden modules are also denied by the API.</p>{data.managed_districts?.length > 0 && <p className="text-xs text-amber-700 mt-1">Assigned districts: {data.managed_districts.join(", ")}</p>}</div><button onClick={load} className="px-4 py-2 bg-white border rounded-xl text-sm font-bold flex items-center justify-center gap-2"><FiRefreshCw className={loading ? "animate-spin" : ""}/> Refresh</button></header>

    {module === "dashboard" ? <>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">{Object.entries(data.task_summary || {}).map(([key, value]) => <div key={key} className="bg-white border rounded-2xl p-4"><b className={`text-3xl ${key === "overdue" && value ? "text-rose-600" : "text-purple-800"}`}>{value || 0}</b><p className="text-xs text-slate-500 capitalize">{key.replaceAll("_", " ")} tasks</p></div>)}</div>
      <section><h2 className="font-black text-slate-900 mb-3">Assigned module queues</h2><div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">{Object.entries(data.queue_counts || {}).map(([key, value]) => <Link key={key} to={paths[key]} className="bg-slate-900 text-white rounded-2xl p-4 hover:bg-purple-900"><b className="text-3xl">{value}</b><p className="text-xs text-slate-300">{names[key] || key}</p></Link>)}{!Object.keys(data.queue_counts || {}).length && <p className="text-sm text-slate-500">No operational modules have been assigned. Contact an administrator.</p>}</div></section>
    </> : <>
      {(module === "budget" && permits(data.capabilities, module, "add")) && <details className="bg-white border rounded-2xl p-5"><summary className="font-black cursor-pointer">Add verified expenditure survey</summary><div className="mt-4 max-w-2xl"><TravelExpenditureForm onSuccess={load}/></div></details>}
      {(module === "safety" && permits(data.capabilities, module, "add")) && <details className="bg-white border rounded-2xl p-5"><summary className="font-black cursor-pointer">Add field safety report</summary><div className="mt-4 max-w-2xl"><RiskAssessmentForm onSuccess={load}/></div></details>}
      <section className="bg-white border rounded-2xl overflow-hidden"><div className="p-4 border-b flex justify-between"><b>{names[module]}</b><span className="text-xs text-slate-500">{data.results?.length || 0} records loaded</span></div><div className="divide-y">{data.results?.map(row => <article key={`${row.type || module}-${row.id}`} className="p-4 flex flex-col md:flex-row gap-3"><div className="min-w-0 flex-1">{row.image_url && <img src={row.image_url} alt="Review candidate" className="w-28 h-20 object-cover rounded-lg float-left mr-3"/>}<div className="flex gap-2 items-center"><h3 className="font-black text-slate-900">{row.title}</h3><span className="text-[10px] px-2 py-0.5 bg-slate-100 rounded-full">{row.status}</span></div><p className="text-xs text-purple-700">{row.subtitle}</p><p className="text-sm text-slate-600 mt-1 line-clamp-3">{row.description}</p>{row.amount != null && <p className="text-sm font-bold text-emerald-700 mt-1">NPR {Number(row.amount).toLocaleString()}</p>}</div>{["destinations", "images", "reviews"].includes(module) && permits(data.capabilities, module, "approve") && <div className="flex gap-2 self-start"><button onClick={() => queueAction(row, "approve")} className="p-2.5 bg-emerald-700 text-white rounded-xl" title="Approve"><FiCheck/></button><button onClick={() => queueAction(row, "reject")} className="p-2.5 bg-rose-700 text-white rounded-xl" title={module === "reviews" ? "Flag" : "Reject"}><FiX/></button></div>}{module==="restaurants"&&<div className="flex gap-1">{permits(data.capabilities,module,"approve")&&<><button onClick={()=>queueAction(row,"publish")} className="p-2 bg-emerald-700 text-white rounded-lg">Publish</button><button onClick={()=>queueAction(row,"verify")} className="p-2 bg-sky-700 text-white rounded-lg">Verify</button></>}{permits(data.capabilities,module,"delete")&&<button onClick={()=>queueAction(row,"archive")} className="p-2 bg-rose-700 text-white rounded-lg">Archive</button>}</div>}{module==="transportation"&&<div className="flex gap-1">{permits(data.capabilities,module,"approve")&&<button onClick={()=>queueAction(row,"verify")} className="p-2 bg-sky-700 text-white rounded-lg">Verify</button>}{permits(data.capabilities,module,"delete")&&<button onClick={()=>queueAction(row,"archive")} className="p-2 bg-rose-700 text-white rounded-lg">Archive</button>}</div>}{module==="travel_plans"&&permits(data.capabilities,module,"change")&&<div className="flex gap-1"><button onClick={()=>queueAction(row,"activate")} className="p-2 bg-emerald-700 text-white rounded-lg">Activate</button><button onClick={()=>queueAction(row,"complete")} className="p-2 bg-sky-700 text-white rounded-lg">Complete</button></div>}</article>)}{!loading && !data.results?.length && <p className="p-12 text-center text-slate-500">Your assigned queue is empty.</p>}</div></section>
    </>}

    <section className="bg-white border rounded-2xl overflow-hidden"><div className="p-4 border-b"><h2 className="font-black text-slate-900">My assigned tasks</h2><p className="text-xs text-slate-500">Task completion is reported to the assigning administrator.</p></div><div className="divide-y">{data.tasks?.map(task => <div key={task.id} className="p-4 flex flex-col sm:flex-row gap-3"><div className="flex-1"><div className="flex gap-2"><b>{task.title}</b><span className={`text-[10px] px-2 py-0.5 rounded-full ${task.priority === "urgent" ? "bg-rose-100 text-rose-700" : "bg-amber-100 text-amber-700"}`}>{task.priority}</span></div><p className="text-sm text-slate-600">{task.description}</p><p className="text-xs text-slate-400 mt-1"><FiClock className="inline"/> Due {task.due_date || "not set"}{task.hotel ? ` · ${task.hotel}` : ""}</p></div><div className="flex gap-2">{task.status === "pending" && <button onClick={() => act({ module: "tasks", id: task.id, action: "in_progress" })} className="px-3 py-2 bg-sky-700 text-white rounded-xl text-xs font-bold"><FiAlertCircle className="inline"/> Start</button>}{!["completed", "cancelled"].includes(task.status) && <button onClick={() => act({ module: "tasks", id: task.id, action: "completed" }, "Mark this task completed?")} className="px-3 py-2 bg-emerald-700 text-white rounded-xl text-xs font-bold"><FiCheckCircle className="inline"/> Complete</button>}</div></div>)}{!data.tasks?.length && <p className="p-8 text-center text-slate-500 text-sm">No tasks assigned.</p>}</div></section>
  </div>
}
