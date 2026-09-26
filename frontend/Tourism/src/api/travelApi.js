import axiosClient from "./axiosClient"

// Official traveller data served by Django:
// - NRB exchange rates (Nepal Rastra Bank, dated)
// - visa / TIMS / permit / park & heritage fees transcribed from
//   immigration.gov.np and ntb.gov.np (each item carries its source URL)
const travelApi = {
  fxRates: () => axiosClient.get("/fx/rates/"),
  requirements: (nationality = "foreign") =>
    axiosClient.get("/travel-requirements/", { params: { nationality } }),
  destinationRequirements: (id, params = {}) =>
    axiosClient.get(`/travel-requirements/destination/${id}/`, { params }),
}

export default travelApi
