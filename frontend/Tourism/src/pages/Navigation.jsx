// CONFIRMED WORKING as-is — no changes needed. The backend's
// /navigation/route endpoint now resolves `destination_name` (exactly
// what this page sends) against real Destination rows and returns both
// `route` and `destination` in the response, matching what's read below.
import { useState } from "react";
import MapView from "../components/map/MapView";
import useGeolocation from "../hooks/useGeolocation";
import { FiNavigation, FiMapPin } from "react-icons/fi";

import navigationApi from "../api/navigationApi";


const Navigation = () => {

  const { position } = useGeolocation();

  const [destinationQuery, setDestinationQuery] = useState("");
  const [destination, setDestination] = useState(null);
  const [route, setRoute] = useState([]);
  const [error, setError] = useState("");

  const [loading, setLoading] = useState(false);


  const handleGetRoute = async (e) => {

    e.preventDefault();


    if (!position) {
      console.log("Waiting for location");
      return;
    }


    if (!destinationQuery.trim()) {
      return;
    }


    setLoading(true);


    try {


      const payload = {

        start_latitude: position.lat,

        start_longitude: position.lng,

        destination_name: destinationQuery

      };


      console.log("Sending navigation payload:", payload);



      const response = await navigationApi.getRoute(payload);



      console.log(
        "Navigation response:",
        response.data
      );



      setError("");
      setDestination(
        response.data.destination
          ? {
              ...response.data.destination,
              lat: parseFloat(response.data.destination.latitude),
              lng: parseFloat(response.data.destination.longitude),
            }
          : null
      );

      setRoute(
        response.data.route || []
      );



    } catch(error) {


      const message =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        error.message ||
        "Unable to load route."

      console.error(
        "Navigation error:",
        error.response?.data || error.message
      );

      setError(message)
      setRoute([]);

    }
    finally {

      setLoading(false);

    }

  };




  return (

    <div className="container-app py-10">


      <h1 className="section-title flex items-center gap-2">

        <FiNavigation className="text-primary-500"/>

        Navigation

      </h1>



      <form
        onSubmit={handleGetRoute}
        className="flex flex-col sm:flex-row gap-3 mb-6"
      >


        <div className="relative flex-1">


          <FiMapPin
            className="absolute left-4 top-1/2 
            -translate-y-1/2 text-gray-400"
          />


          <input

            className="input-field pl-11"

            placeholder="Where are you headed?"

            value={destinationQuery}

            onChange={(e)=>
              setDestinationQuery(e.target.value)
            }

          />


        </div>



        <button

          className="btn-primary"

          disabled={loading}

        >

          {
            loading
            ?
            "Finding route..."
            :
            "Get Directions"
          }


        </button>



      </form>



      {error && (
        <p className="text-sm text-red-500 mb-4">{error}</p>
      )}

      <MapView
        center={destination || position}
        userLocation={position}
        destination={destination}
        route={route}
        height="500px"
      />

    </div>

  );

};


export default Navigation;