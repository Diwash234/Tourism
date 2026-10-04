import { useState, useEffect, useCallback } from "react"
import { FiPlus, FiSearch, FiEdit, FiTrash, FiMapPin, FiImage, FiEye, FiDownload, FiUpload, FiFilter, FiX, FiChevronDown, FiChevronUp } from "react-icons/fi"
import { motion, AnimatePresence } from "framer-motion"
import adminApi from "../../api/adminApi"
import destinationApi from "../../api/destinationApi"
import useToast from "../../hooks/useToast"

const CATEGORIES = [
  "nature", "adventure", "culture", "spiritual", "wildlife",
  "heritage", "lakes", "mountains", "trekking", "cities",
  "hot-springs", "viewpoints", "camping", "bird-watching",
  "parks-gardens", "museums", "festivals", "food-culinary",
  "shopping", "villages", "eco-tourism", "cycling",
  "air-sports", "water-sports", "winter", "pilgrimage",
  "buddhist-sites", "temples", "spiritual-wellness", "hill-stations"
]

const PROVINCES = [
  "Koshi Province", "Madhesh Province", "Bagmati Province",
  "Gandaki Province", "Lumbini Province", "Karnali Province",
  "Sudurpashchim Province"
]

const STATUS_OPTIONS = [
  { value: "draft", label: "Draft" },
  { value: "pending", label: "Pending Review" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
  { value: "archived", label: "Archived" }
]

const initialForm = {
  name: "",
  slug: "",
  description: "",
  short_description: "",
  category: "",
  district: "",
  province: "",
  city: "",
  latitude: "",
  longitude: "",
  altitude: "",
  status: "draft",
  is_active: true,
  is_featured: false,
  opening_hours: "",
  entry_fee: "",
  best_time_to_visit: "",
  cultural_significance: "",
  aliases: "",
  source: "admin",
  cover_image: null,
  gallery_images: []
}

export default function DestinationManagementPanel() {
  const { showToast } = useToast()

  // State
  const [destinations, setDestinations] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [categoryFilter, setCategoryFilter] = useState("")
  const [statusFilter, setStatusFilter] = useState("")
  const [provinceFilter, setProvinceFilter] = useState("")
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [totalCount, setTotalCount] = useState(0)
  const [totalPages, setTotalPages] = useState(0)

  // Modal state
  const [showModal, setShowModal] = useState(false)
  const [editingDestination, setEditingDestination] = useState(null)
  const [form, setForm] = useState(initialForm)
  const [formErrors, setFormErrors] = useState({})
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)

  // View state
  const [viewMode, setViewMode] = useState("table") // table, cards, map
  const [selectedIds, setSelectedIds] = useState([])
  const [sortConfig, setSortConfig] = useState({ key: "name", direction: "asc" })

  // Coordinates picker
  const [showCoordPicker, setShowCoordPicker] = useState(false)
  const [coordField, setCoordField] = useState("latitude")

  // Fetch destinations
  const fetchDestinations = useCallback(async () => {
    setLoading(true)
    try {
      const params = {
        page: currentPage,
        page_size: pageSize,
        search: search || undefined,
        category: categoryFilter || undefined,
        status: statusFilter || undefined,
        province: provinceFilter || undefined,
        ordering: `${sortConfig.direction === "desc" ? "-" : ""}${sortConfig.key}`
      }
      const { data } = await destinationApi.getDestinations(params)
      const results = data.results || data || []
      setDestinations(results)
      setTotalCount(data.count || results.length)
      setTotalPages(Math.ceil((data.count || results.length) / pageSize))
    } catch (err) {
      showToast("Failed to load destinations", "error")
      setDestinations([])
    } finally {
      setLoading(false)
    }
  }, [currentPage, pageSize, search, categoryFilter, statusFilter, provinceFilter, sortConfig, showToast])

  useEffect(() => { fetchDestinations() }, [fetchDestinations])

  // Handlers
  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === "asc" ? "desc" : "asc"
    }))
  }

  const openCreateModal = () => {
    setEditingDestination(null)
    setForm(initialForm)
    setFormErrors({})
    setShowModal(true)
  }

  const openEditModal = (dest) => {
    setEditingDestination(dest)
    setForm({
      ...initialForm,
      id: dest.id,
      name: dest.name || "",
      slug: dest.slug || "",
      description: dest.description || "",
      short_description: dest.short_description || "",
      category: dest.category?.slug || dest.category?.name || "",
      district: dest.district || "",
      province: dest.province || "",
      city: dest.city || "",
      latitude: dest.latitude?.toString() || "",
      longitude: dest.longitude?.toString() || "",
      altitude: dest.altitude?.toString() || "",
      status: dest.status || "draft",
      is_active: dest.is_active !== false,
      is_featured: dest.is_featured === true,
      opening_hours: dest.opening_hours || "",
      entry_fee: dest.entry_fee?.toString() || "",
      best_time_to_visit: dest.best_time_to_visit || "",
      cultural_significance: dest.cultural_significance || "",
      aliases: Array.isArray(dest.aliases) ? dest.aliases.join(", ") : (dest.aliases || ""),
      source: dest.source || "admin"
    })
    setFormErrors({})
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setEditingDestination(null)
    setForm(initialForm)
    setFormErrors({})
  }

  const validateForm = () => {
    const errors = {}
    if (!form.name.trim()) errors.name = "Name is required"
    if (!form.slug.trim()) errors.slug = "Slug is required"
    if (!form.category) errors.category = "Category is required"
    if (!form.district.trim()) errors.district = "District is required"
    if (!form.province) errors.province = "Province is required"
    if (form.latitude && (parseFloat(form.latitude) < -90 || parseFloat(form.latitude) > 90)) {
      errors.latitude = "Latitude must be between -90 and 90"
    }
    if (form.longitude && (parseFloat(form.longitude) < -180 || parseFloat(form.longitude) > 180)) {
      errors.longitude = "Longitude must be between -180 and 180"
    }
    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSave = async () => {
    if (!validateForm()) return
    setSaving(true)
    try {
      const payload = {
        ...form,
        latitude: form.latitude ? parseFloat(form.latitude) : null,
        longitude: form.longitude ? parseFloat(form.longitude) : null,
        altitude: form.altitude ? parseInt(form.altitude) : null,
        entry_fee: form.entry_fee ? parseFloat(form.entry_fee) : null,
        aliases: form.aliases.split(",").map(a => a.trim()).filter(Boolean),
        is_active: form.is_active,
        is_featured: form.is_featured
      }

      if (editingDestination) {
        await adminApi.updateDestination(editingDestination.id, payload)
        showToast("Destination updated successfully", "success")
      } else {
        await adminApi.createDestination(payload)
        showToast("Destination created successfully", "success")
      }
      closeModal()
      fetchDestinations()
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || "Save failed"
      showToast(msg, "error")
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id, name) => {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return
    try {
      await adminApi.deleteDestination(id)
      showToast("Destination deleted", "success")
      fetchDestinations()
    } catch (err) {
      showToast(err.response?.data?.detail || "Delete failed", "error")
    }
  }

  const handleBulkDelete = async () => {
    if (!selectedIds.length) return
    if (!confirm(`Delete ${selectedIds.length} destinations?`)) return
    try {
      await Promise.all(selectedIds.map(id => adminApi.deleteDestination(id)))
      showToast(`${selectedIds.length} destinations deleted`, "success")
      setSelectedIds([])
      fetchDestinations()
    } catch (err) {
      showToast("Bulk delete failed", "error")
    }
  }

  const handleBulkStatusChange = async (status) => {
    if (!selectedIds.length) return
    try {
      await Promise.all(selectedIds.map(id =>
        adminApi.updateDestination(id, { status })
      ))
      showToast(`${selectedIds.length} destinations updated to ${status}`, "success")
      setSelectedIds([])
      fetchDestinations()
    } catch (err) {
      showToast("Bulk update failed", "error")
    }
  }

  const exportCSV = () => {
    const headers = ["ID", "Name", "Slug", "Category", "District", "Province", "City", "Latitude", "Longitude", "Status", "Featured"]
    const rows = destinations.map(d => [
      d.id, d.name, d.slug, d.category?.name || d.category, d.district,
      d.province, d.city, d.latitude || "", d.longitude || "", d.status, d.is_featured
    ])
    const csv = [headers, ...rows].map(r => r.map(v => `"${v}"`).join(",")).join("\n")
    const blob = new Blob([csv], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `destinations_${new Date().toISOString().split("T")[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleImageUpload = async (field, file) => {
    if (!file) return
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append("file", file)
      // Use the admin upload endpoin
      const { data } = await adminApi.uploadBrandingAsset(formData)
      setForm(prev => ({ ...prev, [field]: data.url || data.path }))
      showToast("Image uploaded", "success")
    } catch (err) {
      showToast("Upload failed", "error")
    } finally {
      setUploading(false)
    }
  }

  const handleCoordPick = (lat, lng) => {
    setForm(prev => ({ ...prev, [coordField]: lat, [coordField === "latitude" ? "longitude" : "latitude"]: lng }))
    setShowCoordPicker(false)
  }

  const toggleSelect = (id) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])
  }

  const toggleSelectAll = () => {
    if (selectedIds.length === destinations.length) {
      setSelectedIds([])
    } else {
      setSelectedIds(destinations.map(d => d.id))
    }
  }

  // Render
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <FiMapPin className="text-emerald-600" />
            Destination Managemen
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage all destinations — create, edit, bulk actions, coordinates, images
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={exportCSV} className="px-4 py-2 rounded-xl bg-white border border-slate-200 text-slate-700 text-sm font-bold flex items-center gap-2 hover:bg-slate-50 transition">
            <FiDownload /> Export CSV
          </button>
          <button onClick={openCreateModal} className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold flex items-center gap-2">
            <FiPlus /> Add Destination
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-4">
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <inpu
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              placeholder="Search by name, slug, city, district..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setCurrentPage(1) }}
            />
          </div>
          <selec
            value={categoryFilter}
            onChange={(e) => { setCategoryFilter(e.target.value); setCurrentPage(1) }}
            className="input-field px-4 py-2.5 rounded-xl text-sm min-w-[180px]"
          >
            <option value="">All Categories</option>
            {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <selec
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setCurrentPage(1) }}
            className="input-field px-4 py-2.5 rounded-xl text-sm min-w-[160px]"
          >
            <option value="">All Status</option>
            {STATUS_OPTIONS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
          <selec
            value={provinceFilter}
            onChange={(e) => { setProvinceFilter(e.target.value); setCurrentPage(1) }}
            className="input-field px-4 py-2.5 rounded-xl text-sm min-w-[200px]"
          >
            <option value="">All Provinces</option>
            {PROVINCES.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-500">View:</span>
            <button onClick={() => setViewMode("table")} className={`px-3 py-1.5 rounded-lg text-sm font-bold ${viewMode === "table" ? "bg-emerald-600 text-white" : "bg-white text-slate-600 border border-slate-200"}`}>Table</button>
            <button onClick={() => setViewMode("cards")} className={`px-3 py-1.5 rounded-lg text-sm font-bold ${viewMode === "cards" ? "bg-emerald-600 text-white" : "bg-white text-slate-600 border border-slate-200"}`}>Cards</button>
          </div>
        </div>

        {/* Bulk Actions */}
        {selectedIds.length > 0 && (
          <div className="flex items-center gap-3 p-3 bg-amber-50 border border-amber-200 rounded-xl">
            <span className="text-sm font-bold text-amber-800">{selectedIds.length} selected</span>
            <button onClick={() => handleBulkStatusChange("approved")} className="px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-xs font-bold hover:bg-emerald-700">Approve</button>
            <button onClick={() => handleBulkStatusChange("rejected")} className="px-3 py-1.5 rounded-lg bg-rose-600 text-white text-xs font-bold hover:bg-rose-700">Reject</button>
            <button onClick={() => handleBulkStatusChange("published")} className="px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-bold hover:bg-blue-700">Publish</button>
            <button onClick={handleBulkDelete} className="px-3 py-1.5 rounded-lg bg-red-600 text-white text-xs font-bold hover:bg-red-700 ml-auto">Delete All</button>
            <button onClick={() => setSelectedIds([])} className="px-3 py-1.5 rounded-lg bg-slate-200 text-slate-600 text-xs font-bold hover:bg-slate-300">Clear</button>
          </div>
        )}
      </div>

      {/* Table View */}
      <AnimatePresence mode="wait">
        {viewMode === "table" && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3 text-left">
                      <input type="checkbox" checked={selectedIds.length === destinations.length && destinations.length > 0} onChange={toggleSelectAll} className="rounded border-slate-300" />
                    </th>
                    {["Name", "Category", "Location", "Coordinates", "Status", "Featured", "Actions"].map(h => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-bold uppercase text-slate-500 cursor-pointer hover:text-emerald-600">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {loading ? (
                    <tr><td colSpan={8} className="px-4 py-8 text-center text-slate-500">Loading...</td></tr>
                  ) : destinations.length === 0 ? (
                    <tr><td colSpan={8} className="px-4 py-8 text-center text-slate-500">No destinations found</td></tr>
                  ) : (
                    destinations.map(dest => (
                      <tr key={dest.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3">
                          <input type="checkbox" checked={selectedIds.includes(dest.id)} onChange={() => toggleSelect(dest.id)} className="rounded border-slate-300" />
                        </td>
                        <td className="px-4 py-3">
                          <div className="font-medium text-slate-900">{dest.name}</div>
                          <div className="text-xs text-slate-500">{dest.slug}</div>
                        </td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-700 text-xs font-bold">
                            {dest.category?.name || dest.category}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-xs text-slate-600">
                          <div>{dest.district}, {dest.province}</div>
                          {dest.city && <div>{dest.city}</div>}
                        </td>
                        <td className="px-4 py-3 text-xs font-mono text-slate-500">
                          {dest.latitude && dest.longitude ? `${parseFloat(dest.latitude).toFixed(4)}, ${parseFloat(dest.longitude).toFixed(4)}` : "—"}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                            dest.status === "approved" ? "bg-emerald-100 text-emerald-700" :
                            dest.status === "pending" ? "bg-amber-100 text-amber-700" :
                            dest.status === "rejected" ? "bg-rose-100 text-rose-700" :
                            "bg-slate-100 text-slate-700"
                          }`}>
                            {dest.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          {dest.is_featured && <span className="text-amber-500" title="Featured">⭐</span>}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            <button onClick={() => openEditModal(dest)} className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition" title="Edit">
                              <FiEdit size={14} />
                            </button>
                            <button onClick={() => handleDelete(dest.id, dest.name)} className="p-2 rounded-lg bg-slate-100 hover:bg-rose-100 text-slate-600 hover:text-rose-600 transition" title="Delete">
                              <FiTrash size={14} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-4 py-3 border-t border-slate-200 flex items-center justify-between">
                <span className="text-sm text-slate-500">
                  Page {currentPage} of {totalPages} • {totalCount} total
                </span>
                <div className="flex gap-1">
                  <button onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1} className="px-3 py-1.5 rounded-lg bg-white border border-slate-200 disabled:opacity-40 text-sm font-bold">Prev</button>
                  <button onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages} className="px-3 py-1.5 rounded-lg bg-white border border-slate-200 disabled:opacity-40 text-sm font-bold">Next</button>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Cards View */}
      <AnimatePresence mode="wait">
        {viewMode === "cards" && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {loading ? Array(8).fill(0).map((_, i) => (
              <div key={i} className="bg-white rounded-2xl border border-slate-200 p-5 animate-pulse">
                <div className="h-4 bg-slate-200 rounded w-3/4 mb-3"></div>
                <div className="h-3 bg-slate-200 rounded w-1/2 mb-2"></div>
                <div className="h-3 bg-slate-200 rounded w-1/3"></div>
              </div>
            )) : destinations.map(dest => (
              <div key={dest.id} className="bg-white rounded-2xl border border-slate-200 p-5 hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-bold text-slate-900 truncate">{dest.name}</h3>
                    <p className="text-xs text-slate-500">{dest.slug}</p>
                  </div>
                  <input type="checkbox" checked={selectedIds.includes(dest.id)} onChange={() => toggleSelect(dest.id)} className="rounded border-slate-300 ml-2 mt-1" />
                </div>
                <div className="space-y-2 text-xs text-slate-600">
                  <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-700 font-bold inline-block">{dest.category?.name || dest.category}</span>
                  <div>{dest.district}, {dest.province}</div>
                  <div className="font-mono">{dest.latitude && dest.longitude ? `${parseFloat(dest.latitude).toFixed(4)}, ${parseFloat(dest.longitude).toFixed(4)}` : "No coordinates"}</div>
                  <span className={`px-2 py-0.5 rounded font-bold ${
                    dest.status === "approved" ? "bg-emerald-100 text-emerald-700" :
                    dest.status === "pending" ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-700"
                  }`}>{dest.status}</span>
                  {dest.is_featured && <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-700 font-bold">⭐ Featured</span>}
                </div>
                <div className="flex gap-2 mt-4 pt-3 border-t border-slate-100">
                  <button onClick={() => openEditModal(dest)} className="flex-1 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold flex items-center justify-center gap-1"><FiEdit size={12} /> Edit</button>
                  <button onClick={() => handleDelete(dest.id, dest.name)} className="px-3 py-2 rounded-lg bg-rose-100 hover:bg-rose-200 text-rose-700 text-xs font-bold flex items-center gap-1"><FiTrash size={12} /></button>
                </div>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Modal */}
      <AnimatePresence>
        {showModal && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
            <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }} className="bg-white rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
              <div className="p-6 border-b border-slate-200 flex items-center justify-between sticky top-0 bg-white z-10 rounded-t-3xl">
                <h2 className="text-xl font-black text-slate-900 flex items-center gap-2">
                  <FiMapPin className="text-emerald-600" />
                  {editingDestination ? "Edit Destination" : "New Destination"}
                </h2>
                <button onClick={closeModal} className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 transition">✕</button>
              </div>

              <form onSubmit={(e) => { e.preventDefault(); handleSave() }} className="p-6 space-y-6">
                <div className="grid lg:grid-cols-2 gap-6">
                  {/* Left Column */}
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-1">Name *</label>
                      <input value={form.name} onChange={e => setForm({...form, name: e.target.value})} className={`w-full px-4 py-2.5 rounded-xl border ${formErrors.name ? "border-red-400" : "border-slate-200"} focus:outline-none focus:ring-2 focus:ring-emerald-500`} placeholder="e.g. Phewa Lake" />
                      {formErrors.name && <p className="text-red-500 text-xs mt-1">{formErrors.name}</p>}
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-1">Slug *</label>
                      <input value={form.slug} onChange={e => setForm({...form, slug: e.target.value.toLowerCase().replace(/\s+/g, "-")})} className={`w-full px-4 py-2.5 rounded-xl border ${formErrors.slug ? "border-red-400" : "border-slate-200"} focus:outline-none focus:ring-2 focus:ring-emerald-500`} placeholder="e.g. phewa-lake" />
                      {formErrors.slug && <p className="text-red-500 text-xs mt-1">{formErrors.slug}</p>}
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-1">Category *</label>
                      <select value={form.category} onChange={e => setForm({...form, category: e.target.value})} className={`w-full px-4 py-2.5 rounded-xl border ${formErrors.category ? "border-red-400" : "border-slate-200"} focus:outline-none focus:ring-2 focus:ring-emerald-500`}>
                        <option value="">Select category</option>
                        {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                      </select>
                      {formErrors.category && <p className="text-red-500 text-xs mt-1">{formErrors.category}</p>}
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-sm font-bold text-slate-700 mb-1">District *</label>
                        <input value={form.district} onChange={e => setForm({...form, district: e.target.value})} className={`w-full px-4 py-2.5 rounded-xl border ${formErrors.district ? "border-red-400" : "border-slate-200"} focus:outline-none focus:ring-2 focus:ring-emerald-500`} placeholder="Kaski" />
                        {formErrors.district && <p className="text-red-500 text-xs mt-1">{formErrors.district}</p>}
                      </div>
                      <div>
                        <label className="block text-sm font-bold text-slate-700 mb-1">Province *</label>
                        <select value={form.province} onChange={e => setForm({...form, province: e.target.value})} className={`w-full px-4 py-2.5 rounded-xl border ${formErrors.province ? "border-red-400" : "border-slate-200"} focus:outline-none focus:ring-2 focus:ring-emerald-500`}>
                          <option value="">Select province</option>
                          {PROVINCES.map(p => <option key={p} value={p}>{p}</option>)}
                        </select>
                        {formErrors.province && <p className="text-red-500 text-xs mt-1">{formErrors.province}</p>}
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-1">City</label>
                      <input value={form.city} onChange={e => setForm({...form, city: e.target.value})} className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="Pokhara" />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-sm font-bold text-slate-700 mb-1">Latitude</label>
                        <div className="flex gap-2">
                          <input value={form.latitude} onChange={e => setForm({...form, latitude: e.target.value})} className={`flex-1 px-4 py-2.5 rounded-xl border ${formErrors.latitude ? "border-red-400" : "border-slate-200"} focus:outline-none focus:ring-2 focus:ring-emerald-500`} placeholder="28.2096" type="number" step="any" />
                          <button type="button" onClick={() => { setCoordField("latitude"); setShowCoordPicker(true) }} className="px-3 py-2.5 rounded-xl bg-emerald-100 hover:bg-emerald-200 text-emerald-700 font-bold flex items-center gap-1"><FiMapPin size={14} /> Pick</button>
                        </div>
                        {formErrors.latitude && <p className="text-red-500 text-xs mt-1">{formErrors.latitude}</p>}
                      </div>
                      <div>
                        <label className="block text-sm font-bold text-slate-700 mb-1">Longitude</label>
                        <div className="flex gap-2">
                          <input value={form.longitude} onChange={e => setForm({...form, longitude: e.target.value})} className={`flex-1 px-4 py-2.5 rounded-xl border ${formErrors.longitude ? "border-red-400" : "border-slate-200"} focus:outline-none focus:ring-2 focus:ring-emerald-500`} placeholder="83.9856" type="number" step="any" />
                          <button type="button" onClick={() => { setCoordField("longitude"); setShowCoordPicker(true) }} className="px-3 py-2.5 rounded-xl bg-emerald-100 hover:bg-emerald-200 text-emerald-700 font-bold flex items-center gap-1"><FiMapPin size={14} /> Pick</button>
                        </div>
                        {formErrors.longitude && <p className="text-red-500 text-xs mt-1">{formErrors.longitude}</p>}
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-1">Altitude (meters)</label>
                      <input value={form.altitude} onChange={e => setForm({...form, altitude: e.target.value})} className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="827" type="number" />
                    </div>
                  </div>

                  {/* Right Column */}
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-1">Short Description</label>
                      <textarea value={form.short_description} onChange={e => setForm({...form, short_description: e.target.value})} rows={3} className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="Brief description for cards/listings..." />
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-1">Full Description</label>
                      <textarea value={form.description} onChange={e => setForm({...form, description: e.target.value})} rows={5} className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="Detailed description..." />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-sm font-bold text-slate-700 mb-1">Entry Fee (NPR)</label>
                        <input value={form.entry_fee} onChange={e => setForm({...form, entry_fee: e.target.value})} className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="0" type="number" step="0.01" />
                      </div>
                      <div>
                        <label className="block text-sm font-bold text-slate-700 mb-1">Best Time to Visit</label>
                        <input value={form.best_time_to_visit} onChange={e => setForm({...form, best_time_to_visit: e.target.value})} className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="Oct - Apr" />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-1">Opening Hours</label>
                      <input value={form.opening_hours} onChange={e => setForm({...form, opening_hours: e.target.value})} className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="6:00 AM - 6:00 PM" />
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-1">Cultural Significance</label>
                      <textarea value={form.cultural_significance} onChange={e => setForm({...form, cultural_significance: e.target.value})} rows={3} className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="Historical/cultural importance..." />
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-1">Aliases (comma-separated)</label>
                      <input value={form.aliases} onChange={e => setForm({...form, aliases: e.target.value})} className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="Fewa Lake, Phewa Tal" />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" checked={form.is_active} onChange={e => setForm({...form, is_active: e.target.checked})} className="rounded border-slate-300 text-emerald-600" />
                        <span className="text-sm font-medium text-slate-700">Active</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" checked={form.is_featured} onChange={e => setForm({...form, is_featured: e.target.checked})} className="rounded border-slate-300 text-emerald-600" />
                        <span className="text-sm font-medium text-slate-700">Featured</span>
                      </label>
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-1">Status</label>
                      <select value={form.status} onChange={e => setForm({...form, status: e.target.value})} className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500">
                        {STATUS_OPTIONS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-slate-700 mb-1">Source</label>
                      <input value={form.source} onChange={e => setForm({...form, source: e.target.value})} className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500" placeholder="admin" />
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200 sticky bottom-0 bg-white z-10 rounded-b-3xl">
                  <button type="button" onClick={closeModal} className="px-5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold">Cancel</button>
                  <button type="submit" disabled={saving} className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-black disabled:opacity-50 flex items-center gap-2">
                    {saving ? "Saving..." : (editingDestination ? "Update Destination" : "Create Destination")}
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Coordinate Picker Modal */}
      <AnimatePresence>
        {showCoordPicker && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="bg-white rounded-3xl max-w-2xl w-full max-h-[80vh] overflow-hidden shadow-2xl">
              <div className="p-4 border-b border-slate-200 flex items-center justify-between">
                <h3 className="font-bold text-slate-900">Pick Coordinates on Map</h3>
                <button onClick={() => setShowCoordPicker(false)} className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200">✕</button>
              </div>
              <div className="h-[500px]">
                <MapView
                  center={{ lat: parseFloat(form.latitude) || 27.7172, lng: parseFloat(form.longitude) || 85.3240 }}
                  zoom={10}
                  onClick={(lat, lng) => handleCoordPick(lat, lng)}
                />
              </div>
              <div className="p-4 border-t border-slate-200 flex justify-end gap-2">
                <button onClick={() => setShowCoordPicker(false)} className="px-4 py-2 rounded-xl bg-emerald-600 text-white font-bold">Use This Location</button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// Simple MapView for coordinate picking
function MapView({ center, zoom, onClick }) {
  const mapRef = useRef(null)
  const [map, setMap] = useState(null)

  useEffect(() => {
    if (typeof window !== "undefined" && !map) {
      import("leaflet").then(L => {
        const m = L.map("coord-map").setView([center.lat, center.lng], zoom)
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: "© OpenStreetMap"
        }).addTo(m)

        m.on("click", (e) => {
          onClick(e.latlng.lat, e.latlng.lng)
        })
        setMap(m)
      })
    }
  }, [center, zoom, onClick, map])

  return <div id="coord-map" style={{ width: "100%", height: "100%" }} />
}

export default DestinationManagementPanel