import { useEffect, useState } from "react"
import { FiPlus, FiCheckCircle, FiX } from "react-icons/fi"
import adminPanelApi from "../../api/adminPanelApi"
import hotelApi from "../../api/hotelApi"
import adminApi from "../../api/adminApi"
import Loader from "../../components/common/Loader"
import EmptyState from "../../components/common/EmptyState"
import SearchSelect from "../../components/common/SearchSelect"
import useToast from "../../hooks/useToast"

const STATUS_OPTIONS = ["pending", "in_progress", "completed", "cancelled"]

const Tasks = () => {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [users, setUsers] = useState([])
  const [hotels, setHotels] = useState([])
  const [form, setForm] = useState({ title: "", assigned_to: "", related_hotel: "", priority: "medium" })
  const { showToast } = useToast()

  const load = () => {
    setLoading(true)
    adminPanelApi
      .getTasks()
      .then(({ data }) => setTasks(data.results || data || []))
      .catch(() => setTasks([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
    adminApi.getUsers({ limit: 500 }).then(({ data }) => {
      const list = data.results || data || []
      setUsers(list.filter((u) => u.is_staff || u.role === "admin" || u.role === "staff")
        .map((u) => ({ id: u.id, label: `${u.email} (${u.role})` })))
    }).catch(() => setUsers([]))
    hotelApi.list({ limit: 500 }).then(({ data }) => {
      setHotels((data.results || data || []).map((h) => ({ id: h.id, label: h.name })))
    }).catch(() => setHotels([]))
  }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    try {
      await adminPanelApi.createTask({
        title: form.title,
        assigned_to: form.assigned_to,
        related_hotel: form.related_hotel || null,
        priority: form.priority,
      })
      showToast("Task created", "success")
      setForm({ title: "", assigned_to: "", related_hotel: "", priority: "medium" })
      setShowForm(false)
      load()
    } catch (err) {
      showToast(
        err.response?.status === 403 ? "Only super admins can assign tasks to others." : "Could not create task.",
        "error"
      )
    }
  }

  const handleStatusChange = async (id, status) => {
    try {
      await adminPanelApi.updateTaskStatus(id, status)
      load()
    } catch {
      showToast("Could not update task status", "error")
    }
  }

  return (
    <div className="container-app py-10 fade-in">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <h1 className="section-title mb-0">Tasks</h1>
        <button
          type="button"
          onClick={() => setShowForm((v) => !v)}
          aria-expanded={showForm}
          className="btn-primary flex items-center gap-2 px-4 py-2 text-sm font-semibold"
        >
          {showForm ? <FiX /> : <FiPlus />} {showForm ? "Cancel" : "New Task"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="card-base p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8 animate-fade-in-up">
          <input
            className="input-field"
            placeholder="Task title"
            value={form.title}
            onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
            required
          />
          <SearchSelect
            label="Assign to"
            options={users}
            value={form.assigned_to}
            onChange={(id) => setForm((f) => ({ ...f, assigned_to: id }))}
            placeholder="Search staff by email…"
            required
          />
          <SearchSelect
            label="Related hotel (optional)"
            options={hotels}
            value={form.related_hotel}
            onChange={(id) => setForm((f) => ({ ...f, related_hotel: id }))}
            placeholder="Search hotel by name…"
          />
          <div>
            <label className="text-xs font-medium text-gray-500">Priority</label>
            <select
              className="input-field mt-1"
              value={form.priority}
              onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>
          <div className="sm:col-span-2 lg:col-span-4">
            <button type="submit" disabled={!form.title || !form.assigned_to} className="btn-primary disabled:opacity-50">Create Task</button>
            <p className="text-[11px] text-gray-400 mt-2">Assigning tasks to others requires super admin (enforced by the backend).</p>
          </div>
        </form>
      )}

      {loading ? (
        <Loader />
      ) : tasks.length ? (
        <div className="space-y-3">
          {tasks.map((t) => (
            <div key={t.id} className="card-base p-4 flex flex-wrap items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="font-semibold truncate">{t.title}</p>
                <p className="text-sm text-gray-500 truncate">
                  {t.hotel_name ? `${t.hotel_name} · ` : ""}Priority: {t.priority} · Assigned to {t.assigned_to_email}
                </p>
              </div>
              <select
                className="input-field w-40"
                value={t.status}
                onChange={(e) => handleStatusChange(t.id, e.target.value)}
              >
                {STATUS_OPTIONS.map((s) => (
                  <option key={s} value={s}>{s.replace("_", " ")}</option>
                ))}
              </select>
            </div>
          ))}
        </div>
      ) : (
        <div className="card-base p-10 text-center animate-fade-in-up">
          <div className="mx-auto w-14 h-14 rounded-full bg-emerald-50 flex items-center justify-center text-emerald-600 mb-4">
            <FiCheckCircle size={26} />
          </div>
          <p className="text-lg font-bold text-gray-900">No tasks yet</p>
          <p className="text-sm text-gray-500 mt-1 mb-5">Create a task to assign follow-ups to your staff team.</p>
          <button type="button" onClick={() => setShowForm(true)} className="btn-primary inline-flex items-center gap-2">
            <FiPlus /> Create your first task
          </button>
        </div>
      )}
    </div>
  )
}

export default Tasks
