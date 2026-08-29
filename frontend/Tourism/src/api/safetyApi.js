import axiosClient from "./axiosClient"

const safetyApi = {

  // Trusted contacts
  getContacts: () =>
    axiosClient.get("/safety/trusted-contacts/"),

  addContact: (payload) =>
    axiosClient.post("/safety/trusted-contacts/", payload),

  deleteContact: (id) =>
    axiosClient.delete(`/safety/trusted-contacts/${id}/`),



  // Trip sharing (owner side - authenticated)
  getTrips: () =>
    axiosClient.get("/safety/trips/"),

  startTrip: (payload) =>
    axiosClient.post("/safety/trips/", payload),

  sendPing: (tripId, coords) =>
    axiosClient.post(
      `/safety/trips/${tripId}/ping/`,
      coords
    ),

  endTrip: (tripId) =>
    axiosClient.post(
      `/safety/trips/${tripId}/end/`
    ),



  // Public shared trip view
  // Trusted contact opens this using token
  getSharedTrip: (token) =>
    axiosClient.get(
      `/safety/shared/${token}/`
    ),



  // SOS emergency system
  getSosAlerts: () =>
    axiosClient.get("/safety/sos/"),

  triggerSos: (payload) =>
    axiosClient.post(
      "/safety/sos/",
      payload
    ),

  resolveSos: (id, status) =>
    axiosClient.post(
      `/safety/sos/${id}/resolve/`,
      {
        status,
      }
    ),

}


// --- Family linking (account <-> account) ---
export const familyApi = {

  // Links involving me (sent + received)
  getLinks: () =>
    axiosClient.get("/safety/family-links/"),

  sendLinkRequest: (payload) =>
    axiosClient.post("/safety/family-links/", payload),

  acceptLink: (id) =>
    axiosClient.post(`/safety/family-links/${id}/accept/`),

  declineLink: (id) =>
    axiosClient.post(`/safety/family-links/${id}/decline/`),

  removeLink: (id) =>
    axiosClient.delete(`/safety/family-links/${id}/`),

  // Live status of every accepted family member
  getFamilyMembers: () =>
    axiosClient.get("/safety/family/members/"),
}

export default safetyApi
