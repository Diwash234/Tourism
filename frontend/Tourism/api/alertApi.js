import axiosClient from "./axiosClient"

const alertApi = {
  getAlerts: (params) => axiosClient.get("/alerts", { params }),
  getRiskStatus: (destinationId) => axiosClient.get(`/alerts/risk/${destinationId}`),
  getEmergencyContacts: (params) => axiosClient.get("/emergency/contacts", { params }),
}

export default alertApi