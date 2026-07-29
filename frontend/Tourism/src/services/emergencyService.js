// NOTE: this file is not currently imported anywhere. Emergency.jsx gets
// its data from src/services/mlService.js's getEmergency() instead, which
// hits a different endpoint (/chatbot/nearby-emergency/). There is also
// an unrelated, differently-implemented src/api/emergencyService.js that
// hits /emergency-contacts/nearest/ and is ALSO unused. Three files, same
// concept, none wired together — pick one before building more on top of
// this. See the chat notes for the recommended consolidation.
import axiosClient from "../api/axiosClient"


export const getEmergency = (
    latitude,
    longitude,
    category,
    limit=5
)=>{

return axiosClient.get(
    "/chatbot/nearby-emergency/",
    {
        params:{
            latitude,
            longitude,
            category,
            limit
        }
    }
)
.then(res=>res.data)

}