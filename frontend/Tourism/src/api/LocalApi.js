import axiosClient from "./axiosClient"

// Local-guide submissions ride the SAME real pipeline as SubmitPlacePage:
//   POST   /destinations/                  (multipart, cover_image in the same request)
//   GET    /destinations/my_submissions/   (the user's own queue, incl. pending/rejected)
//   DELETE /destinations/{slug}/           (submitter while pending, or staff)
//
// Errors propagate to callers so the UI can report honest failures.
// NOTE: this module previously swallowed every error and substituted a
// localStorage copy that faked "saved"/"deleted" success against endpoints
// that never existed on the backend (no /local/* routes were ever registered
// in tourist/urls.py). That fake-success layer was removed per the project
// brief ("no fake success messages"); nothing else imported it.
const localApi = {
  getMyPlaces: (params = {}) =>
    axiosClient.get("/destinations/my_submissions/", { params }),

  addPlace: (formData) => axiosClient.post("/destinations/", formData),

  deletePlace: (slugOrId) => axiosClient.delete(`/destinations/${slugOrId}/`),
}

export default localApi
