import axiosClient from "./axiosClient";

// CONFIRMED WORKING as-is. Matches POST /api/v1/navigation/route, which
// now resolves `destination_name` (free text, exactly what Navigation.jsx
// sends) against real Destination rows server-side, and returns both
// `route` and `destination` in the response — matching what Navigation.jsx
// reads (`response.data.route`, `response.data.destination`).
const navigationApi = {

    getRoute:(payload)=>{

        return axiosClient.post(
            "/navigation/route",
            payload
        );

    }

};

export default navigationApi;