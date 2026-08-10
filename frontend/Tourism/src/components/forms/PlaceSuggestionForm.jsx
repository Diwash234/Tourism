import { useState } from "react"
import { FiPlus, FiCheck } from "react-icons/fi"
import destinationApi from "../../api/destinationApi"
import useToast from "../../hooks/useToast"

export default function PlaceSuggestionForm({ onSuccess }) {
  const { showToast } = useToast()
  const [loading, setLoading] = useState(false)
  const [name, setName] = useState("")
  const [district, setDistrict] = useState("Kaski")
  const [description, setDescription] = useState("")

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name.trim()) return showToast("Place name required", "error")
    setLoading(true)
    try {
      const formData = new FormData()
      formData.append("name", name)
      formData.append("district", district)
      formData.append("description", description)
      formData.append("latitude", "28.209600")
      formData.append("longitude", "83.985600")
      await destinationApi.submit(formData)
      showToast("Place suggested! Sent to Admin Approval Desk.", "success")
      setName("")
      setDescription("")
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
        className="btn-primary w-full py-2.5 text-xs font-bold bg-purple-700 hover:bg-purple-800 text-white rounded-xl shadow-md"
      >
        {loading ? "Submitting..." : "Submit Suggestion to Admin"}
      </button>
    </form>
  )
}
