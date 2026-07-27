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
