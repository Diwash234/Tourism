import { useEffect, useState } from "react"
import { FiUserPlus, FiTrash2 } from "react-icons/fi"
import adminPanelApi from "../../api/adminPanelApi"
import hotelApi from "../../api/hotelApi"
import adminApi from "../../api/adminApi"
import Loader from "../../components/common/Loader"
import EmptyState from "../../components/common/EmptyState"
import useToast from "../../hooks/useToast"
import SearchSelect from "../../components/common/SearchSelect"

const HotelAssignments = () => {
  const [assignments, setAssignments] = useState([])
  const [hotels, setHotels] = useState([])
  const [admins, setAdmins] = useState([])
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

  useEffect(() => {
    load()
    hotelApi.list({ limit: 500 }).then(({ data }) => {
      setHotels((data.results || data || []).map((h) => ({ id: h.id, label: h.name })))
    }).catch(() => setHotels([]))
    adminApi.getUsers({ limit: 500 }).then(({ data }) => {
      const users = data.results || data || []
      setAdmins(users.filter((u) => u.is_staff || u.role === "admin" || u.role === "staff")
        .map((u) => ({ id: u.id, label: `${u.email} (${u.role})` })))
    }).catch(() => setAdmins([]))
  }, [])

  const handleAssign = async (e) => {
    e.preventDefault()
    if (!hotelId || !adminId) return
    try {
      await adminPanelApi.assignHotel(hotelId, adminId, notes)
      showToast("Hotel assigned", "success")
      setHotelId(""); setAdminId(""); setNotes("")
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
    <div className="container-app py-10 fade-in">
      <h1 className="section-title mb-2">Hotel Assignments</h1>
      <p className="text-xs text-saffron-600 bg-saffron-50 inline-block px-3 py-1.5 rounded-full mb-6">
        Assign/remove requires super admin — enforced by the backend.
      </p>

      <form onSubmit={handleAssign} className="card-base p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <SearchSelect label="Hotel" options={hotels} value={hotelId} onChange={setHotelId} placeholder="Search hotel by name…" />
        <SearchSelect label="Admin / Manager" options={admins} value={adminId} onChange={setAdminId} placeholder="Search admin by email…" />
        <div>
          <label className="text-xs font-medium text-gray-500">Notes (optional)</label>
          <input className="input-field mt-1" value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>
        <button type="submit" disabled={!hotelId || !adminId} className="btn-primary self-end flex items-center justify-center gap-2 disabled:opacity-50">
          <FiUserPlus /> Assign
        </button>
      </form>

      {loading ? (
        <Loader />
      ) : assignments.length ? (
        <div className="space-y-3">
          {assignments.map((a) => (
            <div key={a.id} className="card-base p-4 flex items-center justify-between">
              <div className="min-w-0">
                <p className="font-semibold truncate">{a.hotel_name}</p>
                <p className="text-sm text-gray-500 truncate">Managed by {a.admin_email}</p>
                {a.notes && <p className="text-xs text-gray-400 mt-1 truncate">{a.notes}</p>}
              </div>
              <button onClick={() => handleRemove(a.id)} className="text-nepalred-500 shrink-0" aria-label="Remove assignment">
                <FiTrash2 />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="No hotel assignments yet" subtitle="Use the searchable form above to assign a hotel to a staff admin." />
      )}
    </div>
  )
}

export default HotelAssignments
