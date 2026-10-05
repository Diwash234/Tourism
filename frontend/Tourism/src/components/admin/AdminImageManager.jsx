import { useEffect, useState } from "react"
import { FiPlus, FiTrash2, FiSearch, FiCheck, FiMapPin, FiAlertCircle, FiNavigation } from "react-icons/fi"
import axiosClient from "../../api/axiosClient"
import useToast from "../../hooks/useToast"

/**
 * Admin Image Manager — search destinations by name and manage their images.

 * Features:
 * - Search destinations by name or district
 * - View all images for a destination
 * - Add new image by URL
 * - Update image metadata (cover, verification status)
 * - Remove images
 * - Also shows hotels with images
 */
export default function AdminImageManager() {
  const { showToast } = useToast()
  const [query, setQuery] = useState("")
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [selectedDest, setSelectedDest] = useState(null)
  const [newImageUrl, setNewImageUrl] = useState("")
  const [adding, setAdding] = useState(false)

  const search = async () => {
    if (!query.trim()) {
      showToast("Enter a destination name to search", "error")
      return
    }
    setLoading(true)
    try {
      const { data } = await axiosClient.get("/admin/image-manager/", {
        params: { q: query },
      })
      setResults(data)
      setSelectedDest(null)
    } catch {
      showToast("Search failed", "error")
    } finally {
      setLoading(false)
    }
  }

  const selectDest = (dest) => {
    setSelectedDest(dest)
    setNewImageUrl("")
  }

  const addImage = async () => {
    if (!newImageUrl.trim() || !selectedDest) return
    setAdding(true)
    try {
      await axiosClient.post("/admin/image-manager/", {
        action: "add",
        destination_id: selectedDest.id,
        image_url: newImageUrl.trim(),
        is_cover: true,
      })
      showToast("Image added", "success")
      setNewImageUrl("")
      // Refresh
      search()
    } catch {
      showToast("Failed to add image", "error")
    } finally {
      setAdding(false)
    }
  }

  const updateImage = async (imageId, updates) => {
    try {
      await axiosClient.post("/admin/image-manager/", {
        action: "update",
        image_id: imageId,
        ...updates,
      })
      showToast("Image updated", "success")
      search()
    } catch {
      showToast("Failed to update image", "error")
    }
  }

  const removeImage = async (imageId) => {
    if (!confirm("Remove this image?")) return
    try {
      await axiosClient.post("/admin/image-manager/", {
        action: "remove",
        image_id: imageId,
      })
      showToast("Image removed", "success")
      search()
    } catch {
      showToast("Failed to remove image", "error")
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && search()}
            placeholder="Search destination name (e.g. Pokhara, Kathmandu)..."
            className="w-full pl-9 pr-3 py-2 text-sm border rounded-lg"
          />
        </div>
        <button
          onClick={search}
          disabled={loading}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg disabled:opacity-50"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {results && (
        <div className="grid gap-4 lg:grid-cols-2">
          {/* Destinations */}
          <div className="space-y-2">
            <h3 className="text-sm font-bold uppercase tracking-wider text-gray-500">
              Destinations ({results.destinations.length})
            </h3>
            {results.destinations.map((d) => (
              <div
                key={d.id}
                onClick={() => selectDest(d)}
                className={`p-3 border rounded-lg cursor-pointer transition ${
                  selectedDest?.id === d.id
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-200 hover:bg-gray-50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{d.name}</p>
                    <p className="text-xs text-gray-500">{d.district}</p>
                  </div>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                    {d.image_count} images
                  </span>
                </div>
              </div>
            ))}
            {!results.destinations.length && (
              <p className="text-sm text-gray-500">No destinations found.</p>
            )}
          </div>

          {/* Selected destination images */}
          <div className="space-y-2">
            <h3 className="text-sm font-bold uppercase tracking-wider text-gray-500">
              {selectedDest ? `Images: ${selectedDest.name}` : "Select a destination"}
            </h3>
            {selectedDest && (
              <>
                {/* Add image */}
                <div className="flex gap-2">
                  <input
                    value={newImageUrl}
                    onChange={(e) => setNewImageUrl(e.target.value)}
                    placeholder="Paste image URL..."
                    className="flex-1 px-3 py-2 text-sm border rounded-lg"
                  />
                  <button
                    onClick={addImage}
                    disabled={adding || !newImageUrl.trim()}
                    className="px-3 py-2 text-sm text-white bg-green-600 rounded-lg disabled:opacity-50"
                  >
                    <FiPlus />
                  </button>
                </div>

                {/* Nearby places */}
                {selectedDest.nearby_places?.length > 0 && (
                  <div className="p-3 border rounded-lg space-y-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 flex items-center gap-1.5">
                      <FiMapPin size={12} /> Nearby Places (within 50km)
                    </h4>
                    {selectedDest.nearby_places.map((p) => (
                      <div key={p.id} className="flex items-center justify-between text-sm">
                        <span className="text-gray-700">{p.name}</span>
                        <span className="text-xs text-gray-500">{p.distance_km} km</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Emergency services */}
                {selectedDest.emergency_services?.length > 0 && (
                  <div className="p-3 border rounded-lg space-y-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 flex items-center gap-1.5">
                      <FiAlertCircle size={12} /> Emergency Services (within 50km)
                    </h4>
                    {selectedDest.emergency_services.map((e, idx) => (
                      <div key={idx} className="flex items-center justify-between text-sm">
                        <div>
                          <span className="text-gray-700">{e.name}</span>
                          <span className="text-xs text-gray-400 ml-1">({e.type})</span>
                        </div>
                        <div className="text-right">
                          <span className="text-xs text-gray-500">{e.distance_km} km</span>
                          {e.phone && <p className="text-xs text-green-600">{e.phone}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Image list */}
                {selectedDest.images.map((img) => (
                  <div key={img.id} className="p-3 border rounded-lg space-y-2">
                    <div className="flex items-start gap-3">
                      <img
                        src={img.url}
                        alt=""
                        className="w-16 h-16 object-cover rounded"
                        onError={(e) => { e.target.src = "/images/placeholder.jpg" }}
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-gray-500 truncate">{img.url}</p>
                        <div className="flex items-center gap-2 mt-1">
                          {img.is_cover && (
                            <span className="text-xs px-1.5 py-0.5 rounded bg-green-100 text-green-800">Cover</span>
                          )}
                          <span className={`text-xs px-1.5 py-0.5 rounded ${
                            img.verification_status === "approved"
                              ? "bg-green-100 text-green-800"
                              : "bg-orange-100 text-orange-800"
                          }`}>
                            {img.verification_status}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => updateImage(img.id, { is_cover: !img.is_cover })}
                          className="p-1.5 text-gray-400 hover:text-blue-600"
                          title="Toggle cover"
                        >
                          <FiCheck />
                        </button>
                        <button
                          onClick={() => removeImage(img.id)}
                          className="p-1.5 text-gray-400 hover:text-red-600"
                          title="Remove image"
                        >
                          <FiTrash2 />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
                {!selectedDest.images.length && (
                  <p className="text-sm text-gray-500">No images for this destination.</p>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {/* Hotels */}
      {results && results.hotels.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-bold uppercase tracking-wider text-gray-500">
            Hotels ({results.hotels.length})
          </h3>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {results.hotels.map((h) => (
              <div key={h.id} className="p-3 border rounded-lg">
                <p className="font-medium text-gray-900">{h.name}</p>
                <p className="text-xs text-gray-500">{h.destination}</p>
                {h.cover_image && (
                  <p className="text-xs text-gray-400 truncate mt-1">{h.cover_image}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
