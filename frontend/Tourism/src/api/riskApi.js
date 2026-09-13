import axiosClient from "./axiosClient"

const riskApi = {
  assessDestination: (destinationRef) =>
    axiosClient.get(`/destinations/${encodeURIComponent(destinationRef)}/risk/`),
}

export default riskApi
