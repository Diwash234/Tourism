import { useState } from "react"
import { FiUsers, FiUserCheck, FiUserX, FiTrash2, FiEye, FiSearch, FiPlus } from "react-icons/fi"

const ROLES = [
  { id: "tourist", label: "Tourist" },
  { id: "staff", label: "Staff (Sub-Admin)" },
  { id: "content_moderator", label: "Content Moderator" },
  { id: "district_manager", label: "District Manager" },
  { id: "tourist_police", label: "Tourist Police" },
  { id: "admin", label: "Admin" },
  { id: "super_admin", label: "Super Admin" },
]

export default function UserManagement({
  users = [],
  onUpdateRole,
  onToggleStatus,
  onDeleteUser,
  onSelectUser,
  onOpenAddUser,
}) {
  const [search, setSearch] = useState("")

  const filtered = users.filter((u) => {
    const q = search.toLowerCase()
    return (
      u.email?.toLowerCase().includes(q) ||
      u.full_name?.toLowerCase().includes(q) ||
      u.role?.toLowerCase().includes(q) ||
      u.city?.toLowerCase().includes(q)
    )
  })

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <FiSearch className="absolute left-3.5 top-1/2 -translate-y-1/2 text-purple-300" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search users by name, email, district..."
            className="w-full pl-10 pr-4 py-2 bg-purple-950/80 border border-purple-700/60 rounded-xl text-xs text-white placeholder-purple-300 focus:outline-none focus:border-amber-400"
          />
        </div>
        <button
          onClick={onOpenAddUser}
          className="w-full sm:w-auto px-4 py-2 rounded-xl bg-amber-400 hover:bg-amber-500 text-gray-950 font-bold text-xs flex items-center justify-center gap-1.5 shadow"
        >
          <FiPlus size={15} /> Add Sub-Admin / Staff
        </button>
      </div>

      <div className="bg-purple-950/70 border border-purple-700/40 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-purple-900/60 text-purple-200 border-b border-purple-700/50 uppercase tracking-wider text-[11px]">
              <tr>
                <th className="px-4 py-3">User & Bio</th>
                <th className="px-4 py-3">Role (RBAC)</th>
                <th className="px-4 py-3">Location</th>
                <th className="px-4 py-3">Activity</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-purple-800/40 text-purple-100">
              {filtered.map((u) => (
                <tr key={u.id} className="hover:bg-purple-900/30 transition-colors">
                  <td className="px-4 py-3.5">
                    <div className="flex items-start gap-2.5">
                      <div className="w-8 h-8 rounded-lg bg-amber-400 text-gray-950 font-bold flex items-center justify-center text-xs shrink-0 mt-0.5">
                        {u.first_name?.[0] || u.email[0].toUpperCase()}
                      </div>
                      <div className="min-w-0">
                        <p className="font-bold text-white leading-tight">{u.full_name || "Traveler"}</p>
                        <p className="text-[11px] text-purple-300">{u.email}</p>
                        <p className="text-[10px] text-purple-400 italic line-clamp-1">{u.bio || "Nepal explorer"}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3.5">
                    <select
                      value={u.role}
                      onChange={(e) => onUpdateRole?.(u.id, e.target.value)}
                      className="bg-purple-900/80 border border-purple-600/50 rounded-lg px-2 py-1 text-[11px] text-amber-300 font-bold"
                    >
                      {ROLES.map((r) => (
                        <option key={r.id} value={r.id} className="bg-purple-950 text-white">{r.label}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3.5">
                    {u.city ? <span className="text-emerald-400">📍 {u.city}</span> : <span className="text-purple-400">Inactive</span>}
                  </td>
                  <td className="px-4 py-3.5">
                    <button
                      onClick={() => onSelectUser?.(u)}
                      className="text-amber-300 hover:underline font-bold"
                    >
                      {u.history_count} Places
                    </button>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      u.is_active ? "bg-emerald-500/20 text-emerald-300" : "bg-rose-500/20 text-rose-300"
                    }`}>
                      {u.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 text-right space-x-1.5">
                    <button
                      onClick={() => onToggleStatus?.(u.id, u.is_active)}
                      className="p-1.5 rounded-lg bg-purple-800/60 hover:bg-purple-700 text-purple-200"
                      title="Toggle Active Status"
                    >
                      {u.is_active ? <FiUserX size={13} /> : <FiUserCheck size={13} />}
                    </button>
                    <button
                      onClick={() => onDeleteUser?.(u.id)}
                      className="p-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white"
                      title="Remove User"
                    >
                      <FiTrash2 size={13} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
