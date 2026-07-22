import { useEffect, useState } from "react"
import { FiPlus, FiCheckCircle } from "react-icons/fi"
import adminPanelApi from "../../api/adminPanelApi"
import Loader from "../../components/common/Loader"
import EmptyState from "../../components/common/EmptyState"
import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"

const STATUS_OPTIONS = ["pending", "in_progress", "completed", "cancelled"]

const Tasks = () => {
  const { user } = useAuth()
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
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

  useEffect(load, [])

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
    <div className="container-app py-10">
      <div className="flex items-center justify-between mb-6">
        <h1 className="section-title mb-0">Tasks</h1>
        {user?.is_superuser && (
          <button onClick={() => setShowForm((v) => !v)} className="btn-primary flex items-center gap-2">
            <FiPlus /> New Task
          </button>
        )}
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="card-base p-6 grid grid-cols-1 sm:grid-cols-4 gap-4 mb-8">
          <input
            className="input-field"
            placeholder="Task title"
            value={form.title}
            onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
            required
          />
          <input
            className="input-field"
            placeholder="Assign to (User ID)"
            value={form.assigned_to}
            onChange={(e) => setForm((f) => ({ ...f, assigned_to: e.target.value }))}
            required
          />
          <input
            className="input-field"
            placeholder="Related Hotel ID (optional)"
            value={form.related_hotel}
            onChange={(e) => setForm((f) => ({ ...f, related_hotel: e.target.value }))}
          />
          <select
            className="input-field"
            value={form.priority}
            onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>
          <button type="submit" className="btn-primary sm:col-span-4">Create Task</button>
        </form>
      )}

      {loading ? (
        <Loader />
      ) : tasks.length ? (
        <div className="space-y-3">
          {tasks.map((t) => (
            <div key={t.id} className="card-base p-4 flex items-center justify-between">
              <div>
                <p className="font-semibold">{t.title}</p>
                <p className="text-sm text-gray-500">
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
        <EmptyState title="No tasks" subtitle="Tasks assigned to you will show up here." icon={FiCheckCircle} />
      )}
    </div>
  )
}

export default Tasks