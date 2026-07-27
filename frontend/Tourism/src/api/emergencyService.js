import axiosClient from "./axiosClient";


const emergencyService = {


    nearby: (
        latitude,
        longitude
    ) => {

        return axiosClient.get(
            "/emergency-contacts/nearest/",
            {
                params:{
                    latitude,
                    longitude,
                    radius_km:20
                }
            }
        );

    },


};


export default emergencyService;
