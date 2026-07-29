// Hits /emergency-contacts/nearest/ on tourist.EmergencyContactViewSet —
// a real, structured endpoint (contact_type, name, phone_number,
// address, distance_km, is_24_hours) that's a much better fit for
// Emergency.jsx's "big button per service type" UI than the CSV-based
// mlService.getEmergency() the page used to rely on exclusively.
import axiosClient from "./axiosClient";


const emergencyService = {


    // contactType is optional — omit it to get the nearest contact of
    // EVERY type in one call (police, hospital, tourism_office,
    // fire_station, ambulance, embassy, ward_office).
    nearby: (
        latitude,
        longitude,
        contactType
    ) => {

        return axiosClient.get(
            "/emergency-contacts/nearest/",
            {
                params:{
                    latitude,
                    longitude,
                    radius_km:20,
                    ...(contactType ? { contact_type: contactType } : {}),
                }
            }
        );

    },


};


export default emergencyService;