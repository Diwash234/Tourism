import { useEffect, useState } from "react"
import { FiUserPlus, FiTrash2 } from "react-icons/fi"
import adminPanelApi from "../../api/adminPanelApi"
import Loader from "../../components/common/Loader"
import EmptyState from "../../components/common/EmptyState"
import useToast from "../../hooks/useToast"

/**
 * Super-admin-only page: assign a hotel to a staff admin. Route this
 * behind <AdminRoute superAdminOnly /> (or equivalent guard) — the
 * backend also enforces this (only is_superuser can create/delete here),
 * but gate the UI too so staff admins don't see a broken "Assign" button.
 */
const HotelAssignments = () => {
  const [assignments, setAssignments] = useState([])
  const [hotelId, setHotelId] = useState("")
  const [adminId, setAdminId] = useState("")
  const [notes, setNotes] = useState("")
  const [loading, setLoading] = useState(true)
  const { showToast } = useToast()

  const load = () => {
    setLoading(true)
    adminPanelApi
      .getHotelAssignments()
      .then(({ data }) => setAssignments(data.results || data || []))
      .catch(() => setAssignments([]))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const handleAssign = async (e) => {
    e.preventDefault()
    if (!hotelId || !adminId) return
    try {
      await adminPanelApi.assignHotel(hotelId, adminId, notes)
      showToast("Hotel assigned", "success")
      setHotelId("")
      setAdminId("")
      setNotes("")
      load()
    } catch (err) {
      showToast(
        err.response?.status === 403 ? "Only super admins can assign hotels." : "Could not assign hotel.",
        "error"
      )
    }
  }

  const handleRemove = async (id) => {
    try {
      await adminPanelApi.removeAssignment(id)
      showToast("Assignment removed", "info")
      load()
    } catch {
      showToast("Could not remove assignment", "error")
    }
  }

  return (
    <div className="container-app py-10">
      <h1 className="section-title mb-6">Hotel Assignments</h1>

      <form onSubmit={handleAssign} className="card-base p-6 grid grid-cols-1 sm:grid-cols-4 gap-4 mb-8">
        <div>
          <label className="text-xs font-medium text-gray-500">Hotel ID</label>
          <input className="input-field mt-1" value={hotelId} onChange={(e) => setHotelId(e.target.value)} placeholder="e.g. 3" />
        </div>
        <div>
          <label className="text-xs font-medium text-gray-500">Admin User ID</label>
          <input className="input-field mt-1" value={adminId} onChange={(e) => setAdminId(e.target.value)} placeholder="e.g. 7" />
        </div>
        <div className="sm:col-span-1">
          <label className="text-xs font-medium text-gray-500">Notes (optional)</label>
          <input className="input-field mt-1" value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>
        <button type="submit" className="btn-primary self-end flex items-center justify-center gap-2">
          <FiUserPlus /> Assign
        </button>
      </form>

      {loading ? (
        <Loader />
      ) : assignments.length ? (
        <div className="space-y-3">
          {assignments.map((a) => (
            <div key={a.id} className="card-base p-4 flex items-center justify-between">
              <div>
                <p className="font-semibold">{a.hotel_name}</p>
                <p className="text-sm text-gray-500">Managed by {a.admin_email}</p>
                {a.notes && <p className="text-xs text-gray-400 mt-1">{a.notes}</p>}
              </div>
              <button onClick={() => handleRemove(a.id)} className="text-red-500" aria-label="Remove assignment">
                <FiTrash2 />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="No hotel assignments yet" subtitle="Assign a hotel to a staff admin using the form above." />
      )}
    </div>
  )
}

export default HotelAssignments