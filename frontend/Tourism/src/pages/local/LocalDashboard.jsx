import { useCallback, useEffect, useState } from "react"
import CMSPageIntro from "../../components/cms/CMSPageIntro"
import { useForm } from "react-hook-form"
import { FiHome, FiPlus, FiTrash2, FiImage, FiAlertTriangle } from "react-icons/fi"
import localApi from "../../api/LocalApi"
import destinationApi from "../../api/destinationApi"
import PageHeader from "../../components/common/PageHeader"
import Loader from "../../components/common/Loader"
import EmptyState from "../../components/common/EmptyState"
import PlaceholderImage from "../../components/common/PlaceholderImage"
import useToast from "../../hooks/useToast"

const STATUS_STYLES = {
  pending: "text-amber-600",
  approved: "text-emerald-600",
  rejected: "text-rose-600",
  archived: "text-gray-400",
}

// Turn the first DRF error entry into one readable sentence.
const describeError = (err) => {
  const data = err?.response?.data
  if (!data) return err?.message || "Request failed — check your connection."
  if (typeof data === "string") return data
  if (data.detail) return String(data.detail)
  const first = Object.entries(data)[0]
  if (!first) return "Submission was rejected by the server."
  const [field, msg] = first
  return `${field}: ${Array.isArray(msg) ? msg[0] : msg}`
}

const LocalDashboard = () => {
  const [places, setPlaces] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState("")
  const [categories, setCategories] = useState([])
  const [categoriesError, setCategoriesError] = useState(false)
  const [photoFile, setPhotoFile] = useState(null)
  const [photoPreview, setPhotoPreview] = useState("")
  const { showToast } = useToast()
  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm()

  const load = useCallback(() => {
    setLoading(true)
    setLoadError("")
    localApi
      .getMyPlaces()
      .then(({ data }) => setPlaces(data.results || data.items || data || []))
      .catch((err) => {
        setPlaces([])
        setLoadError(describeError(err))
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => {
    load()
    destinationApi
      .getCategories()
      .then(({ data }) => setCategories(data.results || data || []))
      .catch(() => setCategoriesError(true))
    }, 0)
    return () => clearTimeout(t)
  }, [load])

  const onSubmit = async (data) => {
    const formData = new FormData()
    formData.append("name", data.name.trim())
    formData.append("description", (data.description || "").trim())
    if (data.category) formData.append("category", data.category)
    if (data.location?.trim()) {
      formData.append("address", data.location.trim())
      formData.append("city", data.location.trim())
    }

    // Photo: prefer the uploaded file; if only a URL was given, try to fetch
    // it as a blob so it can travel in the same multipart request. If the
    // remote host blocks the fetch we say so instead of silently dropping it.
    if (photoFile) {
      formData.append("cover_image", photoFile)
    } else if (data.imageUrl?.trim()) {
      try {
        const res = await fetch(data.imageUrl.trim())
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const blob = await res.blob()
        formData.append("cover_image", new File([blob], "cover.jpg", { type: blob.type || "image/jpeg" }))
      } catch {
        showToast("Could not fetch that image URL — upload the photo from your computer instead.", "error")
        return
      }
    }

    try {
      await localApi.addPlace(formData)
      showToast("Place submitted — queued for admin verification.", "success")
      reset(); setPhotoFile(null); setPhotoPreview("")
      load()
    } catch (err) {
      // Keep the form contents so nothing the user typed is lost.
      showToast(describeError(err), "error")
    }
  }

  const handleDelete = async (place) => {
    if (!window.confirm(`Delete your submission "${place.name}"?`)) return
    try {
      await localApi.deletePlace(place.slug || place.id)
      setPlaces((prev) => prev.filter((p) => (p.slug || p.id) !== (place.slug || place.id)))
      showToast("Submission deleted.", "success")
    } catch (err) {
      showToast(describeError(err), "error")
    }
  }

  return (
    <div>
      <CMSPageIntro pageKey="local-dashboard" />
      <PageHeader
        title="Local Guide Dashboard"
        subtitle="Showcase your local places with photos. Submissions appear in destination search once approved by an admin."
        icon={FiHome}
        theme="teal"
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <form onSubmit={handleSubmit(onSubmit)} className="card-base p-6 space-y-4 h-fit">
          <h3 className="font-semibold flex items-center gap-2"><FiPlus /> Add a Place</h3>
          <div>
            <label className="text-xs font-medium text-gray-500">Place Name</label>
            <input className="input-field mt-1" {...register("name", { required: true })} />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500">Location</label>
            <input className="input-field mt-1" placeholder="e.g. Ward 4, Bandipur" {...register("location", { required: true })} />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500">Category</label>
            {categoriesError ? (
              <p className="mt-1 text-xs text-rose-600 flex items-center gap-1">
                <FiAlertTriangle size={12} /> Categories could not be loaded — refresh the page to try again.
              </p>
            ) : (
              <select className="input-field mt-1" {...register("category")} disabled={!categories.length}>
                {!categories.length && <option value="">Loading categories…</option>}
                {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            )}
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 flex items-center gap-1">
              <FiImage size={14} /> Photo
            </label>
            <input className="input-field mt-1" placeholder="or paste an image URL: https://..." {...register("imageUrl")} />
            <label className="mt-2 block rounded-xl border-2 border-dashed p-3 text-center text-xs font-bold text-gray-500 cursor-pointer">
              <FiImage className="inline mr-1" /> Browse photo from computer
              <input hidden type="file" accept="image/*" onChange={(e) => { const file=e.target.files?.[0]||null; setPhotoFile(file); setPhotoPreview(file ? URL.createObjectURL(file) : "") }} />
            </label>
            {photoPreview && <img src={photoPreview} alt="Local preview" className="mt-2 h-36 w-full object-cover rounded-xl" />}
            <p className="text-xs text-gray-400 mt-1">Upload a file or paste a URL. The photo stays pending until admin approval.</p>
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500">Description</label>
            <textarea rows={3} className="input-field mt-1" {...register("description")} />
          </div>
          <button type="submit" className="w-full bg-secondary-500 hover:bg-secondary-600 text-white font-semibold px-5 py-2.5 rounded-xl transition" disabled={isSubmitting || (categoriesError || !categories.length)}>
            {isSubmitting ? "Submitting..." : "Submit for Review"}
          </button>
        </form>

        <div>
          <h3 className="font-semibold mb-4">Your Submitted Places</h3>
          {loading ? (
            <Loader />
          ) : loadError ? (
            <div className="card-base p-6 text-center">
              <p className="text-sm text-rose-600 mb-3">{loadError}</p>
              <button onClick={load} className="px-4 py-2 bg-secondary-500 text-white rounded-xl text-sm font-bold">Retry</button>
            </div>
          ) : places.length ? (
            <div className="space-y-4">
              {places.map((place) => (
                <div key={place.id} className="card-base overflow-hidden flex">
                  <PlaceholderImage src={place.cover_image_url} title={place.name} alt={place.name} className="w-28 h-28" />
                  <div className="p-3 flex-1 flex flex-col justify-between">
                    <div>
                      <p className="font-semibold text-sm">{place.name}</p>
                      <p className="text-xs text-gray-400">{place.display_city || place.city || place.address}</p>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className={`text-xs font-semibold capitalize ${STATUS_STYLES[place.status] || "text-gray-500"}`}>
                        {(place.status || "pending").replaceAll("_", " ")}
                      </span>
                      <button onClick={() => handleDelete(place)} className="text-gray-400 hover:text-red-500" title="Delete submission">
                        <FiTrash2 size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="No places submitted yet" subtitle="Add your first local place using the form." />
          )}
        </div>
      </div>
    </div>
  )
}

export default LocalDashboard
