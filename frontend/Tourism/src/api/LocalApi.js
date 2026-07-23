import axiosClient from "./axiosClient"

// Endpoints used by users with the "local" (local guide) role to showcase
// their own places with photos, which then surface in destination search
// and filters once approved by an admin.
const localApi = {
  getMyPlaces: () => axiosClient.get("/local/places"),
  addPlace: (payload) => axiosClient.post("/local/places", payload),
  updatePlace: (id, payload) => axiosClient.put(`/local/places/${id}`, payload),
  deletePlace: (id) => axiosClient.delete(`/local/places/${id}`),
  uploadPlaceImage: (id, formData) =>
    axiosClient.post(`/local/places/${id}/images`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
}

export default localApi