import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { FiUser, FiPlus, FiEdit2, FiTrash2, FiX } from "react-icons/fi"
import userApi from "../api/userApi"
import PageHeader from "../components/common/PageHeader"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import useToast from "../hooks/useToast"
import CMSPageIntro from "../components/cms/CMSPageIntro"

const emptyForm = {
  fullName: "",
  relationTag: "self", // self | relative
  relation: "",
  phone: "",
  idType: "passport",
  idNumber: "",
  nationality: "",
  notes: "",
}

const PersonalDetails = () => {
  const [details, setDetails] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState("")
  const [editingId, setEditingId] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const { showToast } = useToast()
  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm({ defaultValues: emptyForm })

  const load = () => {
    setLoading(true)
    setLoadError("")
    userApi
      .getPersonalDetails()
      .then(({ data }) => setDetails(data.items || data || []))
      .catch((err) => {
        setDetails([])
        setLoadError(err?.response?.data?.detail || err?.message || "Could not load your personal details.")
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const openAddForm = () => {
    setEditingId(null)
    reset(emptyForm)
    setShowForm(true)
  }

  const openEditForm = (item) => {
    setEditingId(item.id)
    reset(item)
    setShowForm(true)
  }

  const closeForm = () => {
    setShowForm(false)
    setEditingId(null)
  }

  const onSubmit = async (data) => {
    try {
      if (editingId) {
        const { data: updated } = await userApi.updatePersonalDetails(editingId, data)
        setDetails((prev) => prev.map((d) => (d.id === editingId ? updated || { ...d, ...data } : d)))
        showToast("Personal details updated", "success")
      } else {
        const { data: created } = await userApi.addPersonalDetails(data)
        setDetails((prev) => [...prev, created || { id: Date.now().toString(), ...data }])
        showToast("Personal details added", "success")
      }
      closeForm()
    } catch (err) {
      // Keep the form open so nothing typed is lost; report the real reason.
      const detail = err?.response?.data
      const msg = typeof detail === "string" ? detail
        : detail?.detail || (detail && Object.entries(detail)[0] ? `${Object.entries(detail)[0][0]}: ${Object.values(detail)[0]}` : "")
        || err?.message || "Could not save details."
      showToast(msg, "error")
    }
  }

  const handleDelete = async (item) => {
    if (!window.confirm(`Remove ${item.fullName}'s details?`)) return
    try {
      await userApi.deletePersonalDetails(item.id)
      setDetails((prev) => prev.filter((d) => d.id !== item.id))
      showToast("Personal details removed", "success")
    } catch (err) {
      showToast(err?.response?.data?.detail || err?.message || "Could not remove this entry.", "error")
    }
  }

  return (
    <div>
      <CMSPageIntro pageKey="personal-details" />
      <PageHeader
        title="Personal Details"
        subtitle="Keep travel documents and emergency contacts for yourself and traveling relatives up to date."
        icon={FiUser}
        theme="indigo"
        actions={
          <button
            onClick={openAddForm}
            className="bg-white text-indigo-600 font-semibold px-4 py-2 rounded-xl flex items-center gap-2 hover:bg-gray-100"
          >
            <FiPlus /> Add Details
          </button>
        }
      />

      {showForm && (
        <div className="card-base p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">{editingId ? "Update Personal Details" : "Add Personal Details"}</h3>
            <button onClick={closeForm} className="text-gray-400 hover:text-dark"><FiX /></button>
          </div>
          <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-gray-500">Full Name</label>
              <input className="input-field mt-1" {...register("fullName", { required: true })} />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">This is for</label>
              <select className="input-field mt-1" {...register("relationTag")}>
                <option value="self">Myself</option>
                <option value="relative">A relative / companion</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">Relation (if relative)</label>
              <input className="input-field mt-1" placeholder="e.g. Spouse, Child, Friend" {...register("relation")} />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">Phone</label>
              <input className="input-field mt-1" {...register("phone")} />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">ID Type</label>
              <select className="input-field mt-1" {...register("idType")}>
                <option value="passport">Passport</option>
                <option value="national_id">National ID</option>
                <option value="driving_license">Driving License</option>
                <option value="citizenship">Citizenship Certificate</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">ID Number</label>
              <input className="input-field mt-1" {...register("idNumber")} />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">Nationality</label>
              <input className="input-field mt-1" {...register("nationality")} />
            </div>
            <div className="sm:col-span-2">
              <label className="text-xs font-medium text-gray-500">Notes (allergies, medical info, etc.)</label>
              <textarea rows={2} className="input-field mt-1" {...register("notes")} />
            </div>
            <div className="sm:col-span-2 flex gap-3">
              <button type="submit" className="bg-indigo-500 hover:bg-indigo-600 text-white font-semibold px-5 py-2.5 rounded-xl transition" disabled={isSubmitting}>
                {isSubmitting ? "Saving..." : editingId ? "Update Details" : "Save Details"}
              </button>
              <button type="button" onClick={closeForm} className="btn-outline">Cancel</button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <Loader />
      ) : loadError ? (
        <div className="card-base p-6 text-center">
          <p className="text-sm text-rose-600 mb-3">{loadError}</p>
          <button onClick={load} className="px-4 py-2 bg-indigo-500 text-white rounded-xl text-sm font-bold">Retry</button>
        </div>
      ) : details.length ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {details.map((item) => (
            <div key={item.id} className="card-base p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-semibold">{item.fullName}</p>
                  <p className="text-xs text-gray-400 capitalize">
                    {item.relationTag === "relative" ? item.relation || "Relative" : "Myself"}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => openEditForm(item)} className="text-gray-400 hover:text-indigo-500">
                    <FiEdit2 size={16} />
                  </button>
                  <button onClick={() => handleDelete(item)} className="text-gray-400 hover:text-red-500">
                    <FiTrash2 size={16} />
                  </button>
                </div>
              </div>
              <div className="mt-3 text-sm text-gray-500 space-y-1">
                {item.phone && <p>📞 {item.phone}</p>}
                {item.idType && <p>{item.idType}: {item.idNumber || "—"}</p>}
                {item.nationality && <p>🌍 {item.nationality}</p>}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="No personal details yet" subtitle="Add your details or a relative's so trip planning is faster." />
      )}
    </div>
  )
}

export default PersonalDetails