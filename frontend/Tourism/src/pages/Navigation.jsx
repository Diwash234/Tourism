import { useState } from "react";
import MapView from "../components/map/MapView";
import useGeolocation from "../hooks/useGeolocation";
import Loader from "../components/common/Loader";
import { FiNavigation, FiMapPin } from "react-icons/fi";

import axios from "axios";


const Navigation = () => {


    const { position } = useGeolocation();


    const [destinationQuery, setDestinationQuery] = useState("");

    const [destination, setDestination] = useState(null);

    const [route, setRoute] = useState([]);

    const [distance, setDistance] = useState(null);

    const [loading,setLoading] = useState(false);



    // Distance calculation

    const calculateDistance = (
        lat1,
        lon1,
        lat2,
        lon2
    )=>{

        const R = 6371;


        const dLat =
            (lat2-lat1) *
            Math.PI / 180;


        const dLon =
            (lon2-lon1) *
            Math.PI / 180;


        const a =
            Math.sin(dLat/2) *
            Math.sin(dLat/2)

            +

            Math.cos(lat1*Math.PI/180)
            *
            Math.cos(lat2*Math.PI/180)
            *
            Math.sin(dLon/2)
            *
            Math.sin(dLon/2);


        const c =
            2 *
            Math.atan2(
                Math.sqrt(a),
                Math.sqrt(1-a)
            );


        return (R*c).toFixed(2);

    };





    // Get route from OSRM free routing API

    const getRoadRoute = async(
        startLat,
        startLng,
        endLat,
        endLng
    )=>{


        try{


            const url =
            `https://router.project-osrm.org/route/v1/driving/`+
            `${startLng},${startLat};${endLng},${endLat}`+
            `?overview=full&geometries=geojson`;



            const response =
            await axios.get(url);



            const coordinates =
            response.data.routes[0]
            .geometry.coordinates;



            const formatted =
            coordinates.map(point=>({

                lat:point[1],

                lng:point[0]

            }));


            return formatted;



        }catch(error){

            console.log(
                "Route error:",
                error
            );

            return [];

        }


    };






    const handleGetRoute = async(e)=>{


        e.preventDefault();



        if(!position){

            alert(
                "Waiting for GPS location"
            );

            return;

        }



        if(!destinationQuery.trim()){

            return;

        }



        setLoading(true);



        try{


            // Find destination from Django

            const destinationResponse =
            await axios.get(
                "http://127.0.0.1:8000/api/destinations/",
                {
                    params:{
                        search:destinationQuery
                    }
                }
            );



            const dest =
            destinationResponse.data.results
            ?
            destinationResponse.data.results[0]
            :
            destinationResponse.data[0];



            if(!dest){

                alert(
                    "Destination not found"
                );

                return;

            }




            setDestination(dest);





            // Calculate distance

            const km =
            calculateDistance(

                position.lat,
                position.lng,

                Number(dest.latitude),
                Number(dest.longitude)

            );


            setDistance(km);





            // Get road route

            const roadRoute =
            await getRoadRoute(

                position.lat,
                position.lng,

                Number(dest.latitude),
                Number(dest.longitude)

            );


            setRoute(roadRoute);



        }
        catch(error){

            console.log(
                error
            );

            alert(
                "Navigation failed"
            );


        }
        finally{

            setLoading(false);

        }


    };






    return (

        <div className="container-app py-10">


            <h1 className="section-title flex items-center gap-2">

                <FiNavigation/>

                Navigation

            </h1>




            <form
            onSubmit={handleGetRoute}
            className="flex gap-3 mb-6"
            >


                <div className="relative flex-1">


                    <FiMapPin
                    className="
                    absolute left-4 top-1/2
                    -translate-y-1/2
                    "
                    />


                    <input

                    className="input-field pl-11"

                    placeholder="Where are you going?"

                    value={destinationQuery}

                    onChange={
                        e=>
                        setDestinationQuery(
                            e.target.value
                        )
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
                    "Finding..."
                    :
                    "Get Route"
                    }


                </button>



            </form>






            {
            distance &&

            <div className="mb-4">

                Distance:

                <b>
                    {distance} KM
                </b>

            </div>

            }







            <MapView

            userLocation={position}

            destination={destination}

            route={route}

            height="500px"

            />




        </div>

    );


};


export default Navigation;