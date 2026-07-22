import api from "../services/api";


const photoApi = {

  // Get photos for a destination
  get: (slug) =>
    api.get(`/destinations/${slug}/photos/`),


  // Upload destination photo
  upload: (slug, formData) =>
    api.post(
      `/destinations/${slug}/photos/`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    ),


  // Optional: get single photo
  detail: (id) =>
    api.get(`/destination-images/${id}/`),


  // Optional: delete uploaded photo
  remove: (id) =>
    api.delete(`/destination-images/${id}/`),


  // Optional: increase photo views
  incrementView: (id) =>
    api.post(`/destination-images/${id}/view/`),

};


export default photoApi;