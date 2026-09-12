import { useState } from "react"
import destinationApi from "../../api/destinationApi"
import useToast from "../../hooks/useToast"

export default function PlaceSuggestionForm({ onSuccess }) {
  const { showToast } = useToast()
  const [loading, setLoading] = useState(false)
  const [name, setName] = useState("")
  const [district, setDistrict] = useState("Kaski")
  const [description, setDescription] = useState("")
  // Optional, user-provided coordinates. NEVER fabricated client-side:
  // a suggestion without coordinates goes to the approval desk and the
  // coordinate-candidate workflow instead of being pinned to a fake point.
  const [lat, setLat] = useState("")
  const [lng, setLng] = useState("")

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name.trim()) return showToast("Place name required", "error")
    setLoading(true)
    try {
      const formData = new FormData()
      formData.append("name", name)
      formData.append("district", district)
      formData.append("description", description)
      const latNum = parseFloat(lat)
      const lngNum = parseFloat(lng)
      if (lat.trim() !== "" || lng.trim() !== "") {
        const coordsValid =
          Number.isFinite(latNum) && Number.isFinite(lngNum) &&
          latNum >= -90 && latNum <= 90 && lngNum >= -180 && lngNum <= 180
        if (!coordsValid) return showToast("Coordinates look invalid (lat -90..90, lng -180..180)", "error")
        formData.append("latitude", String(latNum))
        formData.append("longitude", String(lngNum))
      }
      await destinationApi.submit(formData)
      showToast("Place suggested! Sent to Admin Approval Desk.", "success")
      setName("")
      setDescription("")
      setLat("")
      setLng("")
      onSuccess?.()
    } catch {
      showToast("Submission failed", "error")
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 text-xs">
      <div>
        <label className="font-semibold text-gray-700">Place Name *</label>
        <input
          required
          placeholder="e.g. Hidden Cliff Cave Bandipur"
          className="input-field mt-1 text-sm"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </div>
      <div>
        <label className="font-semibold text-gray-700">District / Region</label>
        <input
          placeholder="e.g. Kaski / Mustang"
          className="input-field mt-1 text-sm"
          value={district}
          onChange={(e) => setDistrict(e.target.value)}
        />
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="font-semibold text-gray-700">Latitude (optional)</label>
          <input
            type="number" step="any" min={-90} max={90}
            placeholder="e.g. 28.2096"
            className="input-field mt-1 text-sm"
            value={lat}
            onChange={(e) => setLat(e.target.value)}
          />
        </div>
        <div>
          <label className="font-semibold text-gray-700">Longitude (optional)</label>
          <input
            type="number" step="any" min={-180} max={180}
            placeholder="e.g. 83.9856"
            className="input-field mt-1 text-sm"
            value={lng}
            onChange={(e) => setLng(e.target.value)}
          />
        </div>
      </div>
      <div>
        <label className="font-semibold text-gray-700">Description</label>
        <textarea
          rows={3}
          placeholder="What makes this place worth visiting?"
          className="input-field mt-1 text-sm"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>
      <button
        type="submit"
        disabled={loading}
        className="btn-primary w-full py-2.5 text-xs font-bold bg-[#102A2E] hover:bg-[#1D5146] text-white rounded-xl shadow-md"
      >
        {loading ? "Submitting..." : "Submit Suggestion to Admin"}
      </button>
    </form>
  )
}
