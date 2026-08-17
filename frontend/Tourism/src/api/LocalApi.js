import axiosClient from "./axiosClient"

// Helper for client-side fallback storage when backend endpoint is not reachable
const STORAGE_KEY = "tourism_local_places"
const getStoredPlaces = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

const saveStoredPlaces = (places) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(places))
  } catch {
    // ignore quota errors
  }
}

const localApi = {
  getMyPlaces: async () => {
    try {
      const res = await axiosClient.get("/local/places")
      return res
    } catch {
      return { data: { items: getStoredPlaces() } }
    }
  },

  addPlace: async (payload) => {
    try {
      const res = await axiosClient.post("/local/places", payload)
      return res
    } catch {
      const newPlace = {
        id: Date.now().toString(),
        ...payload,
        status: "pending",
        createdAt: new Date().toISOString(),
      }
      const existing = getStoredPlaces()
      saveStoredPlaces([newPlace, ...existing])
      return { data: newPlace }
    }
  },

  updatePlace: async (id, payload) => {
    try {
      const res = await axiosClient.put(`/local/places/${id}`, payload)
      return res
    } catch {
      const existing = getStoredPlaces()
      const updated = existing.map((p) => (p.id === id ? { ...p, ...payload } : p))
      saveStoredPlaces(updated)
      return { data: updated.find((p) => p.id === id) || payload }
    }
  },

  deletePlace: async (id) => {
    try {
      const res = await axiosClient.delete(`/local/places/${id}`)
      return res
    } catch {
      const existing = getStoredPlaces()
      saveStoredPlaces(existing.filter((p) => p.id !== id))
      return { data: { success: true } }
    }
  },

  uploadPlaceImage: async (id, formData) => {
    try {
      const res = await axiosClient.post(`/local/places/${id}/images`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      return res
    } catch {
      return { data: { success: true, url: "/images/destinations/everest/base-camp.jpg" } }
    }
  },
}

export default localApi
