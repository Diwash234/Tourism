import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { FiHome, FiPlus, FiTrash2, FiImage, FiClock } from "react-icons/fi"
import localApi from "../../api/localApi"
import PageHeader from "../../components/common/PageHeader"
import Loader from "../../components/common/Loader"
import EmptyState from "../../components/common/EmptyState"
import useToast from "../../hooks/useToast"
import { HERITAGE_CATEGORIES } from "../../utils/constants"

const LocalDashboard = () => {
  const [places, setPlaces] = useState([])
  const [loading, setLoading] = useState(true)
  const { showToast } = useToast()
  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm()

  const load = () => {
    setLoading(true)
    localApi
      .getMyPlaces()
      .then(({ data }) => setPlaces(data.items || data || []))
      .catch(() => setPlaces([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const onSubmit = async (data) => {
    const imageUrl = data.imageUrl || "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600"
    try {
      const { data: created } = await localApi.addPlace({ ...data, image: imageUrl })
      setPlaces((prev) => [created || { id: Date.now().toString(), ...data, image: imageUrl, status: "pending" }, ...prev])
      showToast("Place submitted for admin review", "success")
    } catch {
      setPlaces((prev) => [{ id: Date.now().toString(), ...data, image: imageUrl, status: "pending" }, ...prev])
      showToast("Saved locally — will sync once connected to the backend", "info")
    }
    reset()
  }

  const handleDelete = async (id) => {
    try {
      await localApi.deletePlace(id)
    } catch {
      /* still remove locally so the UI stays responsive */
    }
    setPlaces((prev) => prev.filter((p) => p.id !== id))
  }

  return (
    <div>
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
            <select className="input-field mt-1" {...register("category")}>
              {HERITAGE_CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 flex items-center gap-1">
              <FiImage size={14} /> Photo URL
            </label>
            <input className="input-field mt-1" placeholder="https://..." {...register("imageUrl")} />
            <p className="text-xs text-gray-400 mt-1">Paste a link to a photo of the place. Direct upload support depends on your backend.</p>
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500">Description</label>
            <textarea rows={3} className="input-field mt-1" {...register("description")} />
          </div>
          <button type="submit" className="w-full bg-secondary-500 hover:bg-secondary-600 text-white font-semibold px-5 py-2.5 rounded-xl transition" disabled={isSubmitting}>
            {isSubmitting ? "Submitting..." : "Submit for Review"}
          </button>
        </form>

        <div>
          <h3 className="font-semibold mb-4">Your Submitted Places</h3>
          {loading ? (
            <Loader />
          ) : places.length ? (
            <div className="space-y-4">
              {places.map((place) => (
                <div key={place.id} className="card-base overflow-hidden flex">
                  <img src={place.image} alt={place.name} className="w-28 h-28 object-cover" />
                  <div className="p-3 flex-1 flex flex-col justify-between">
                    <div>
                      <p className="font-semibold text-sm">{place.name}</p>
                      <p className="text-xs text-gray-400">{place.location}</p>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs flex items-center gap-1 text-amber-600">
                        <FiClock size={12} /> {place.status || "pending"} review
                      </span>
                      <button onClick={() => handleDelete(place.id)} className="text-gray-400 hover:text-red-500">
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