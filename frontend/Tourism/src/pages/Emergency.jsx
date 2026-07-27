import { useEffect, useState } from "react"

import useGeolocation from "../hooks/useGeolocation"

import MapView from "../components/map/MapView"

import Loader from "../components/common/Loader"

import { FiPhoneCall, FiAlertOctagon, FiMapPin } from "react-icons/fi"

import { getEmergency } from "../services/mlService"


const Emergency = () => {


  const { position } = useGeolocation()


  const [hospitals, setHospitals] = useState([])

  const [police, setPolice] = useState([])

  const [contacts, setContacts] = useState([
    {
      name:"National Police",
      phone:"100"
    },
    {
      name:"Ambulance",
      phone:"102"
    },
    {
      name:"Fire Service",
      phone:"101"
    }
  ])


  const [loading,setLoading] = useState(true)



  async function loadEmergencyFacilities(){


    if(!position)
      return



    try{


      setLoading(true)



      // Hospitals

      const hospitalResponse =
      await getEmergency(
        position.lat,
        position.lng,
        "hospital",
        5
      )


      setHospitals(
        hospitalResponse.facilities || []
      )




      // Police Stations

      const policeResponse =
      await getEmergency(
        position.lat,
        position.lng,
        "police_station",
        5
      )


      setPolice(
        policeResponse.facilities || []
      )



    }

    catch(error){

      console.log(
        "Emergency error:",
        error
      )

    }

    finally{

      setLoading(false)

    }


  }





  useEffect(()=>{


    if(position){

      loadEmergencyFacilities()

    }


  },[position])





  return (

    <div className="container-app py-10">


      <h1 className="section-title flex items-center gap-2 text-red-500">

        <FiAlertOctagon />

        Emergency Assistance

      </h1>



      <p className="text-gray-500 text-sm mb-6">

        Find nearby hospitals, police stations and emergency services based on your current location.

      </p>





      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">





        {/* MAP */}

        <div className="lg:col-span-2">


          <MapView

            userLocation={position}

            hospitals={hospitals}

            policeStations={police}

            height="450px"

          />


        </div>






        {/* CONTACTS */}


        <div className="space-y-4">


          <h3 className="font-semibold">

            Emergency Contacts

          </h3>





          {

          contacts.map((item,index)=>(


            <a

            key={index}

            href={`tel:${item.phone}`}

            className="card-base p-4 flex justify-between items-center hover:shadow-hover"

            >


              <div>

                <p className="font-medium">

                  {item.name}

                </p>


                <p className="text-sm text-gray-400">

                  {item.phone}

                </p>


              </div>



              <FiPhoneCall

              className="text-primary-500"

              />


            </a>



          ))

          }





        </div>



      </div>







      {/* HOSPITAL LIST */}



      <div className="mt-10">


        <h2 className="text-xl font-semibold mb-4">

          Nearby Hospitals

        </h2>




        {

        loading ? (

          <Loader />

        )

        :

        hospitals.length ? (


          <div className="grid md:grid-cols-2 gap-4">


          {

          hospitals.map((hospital,index)=>(


            <div

            key={index}

            className="card-base p-5"

            >



              <h3 className="font-bold text-lg">

                {hospital["Hospital Name"] || hospital.Name}

              </h3>




              <p className="text-sm text-gray-500 flex gap-2 mt-2">

                <FiMapPin />

                {hospital.Address}

              </p>




              <p className="text-sm mt-2">

                📞 {hospital.Phone}

              </p>




              {

              hospital.distance_km &&

              <p className="text-sm text-green-600 mt-2">

                {hospital.distance_km} km away

              </p>

              }



            </div>


          ))

          }


          </div>


        )

        :

        (

          <p className="text-gray-500">

            No hospitals found nearby.

          </p>

        )

        }



      </div>








      {/* POLICE LIST */}




      <div className="mt-10">


        <h2 className="text-xl font-semibold mb-4">

          Nearby Police Stations

        </h2>




        {

        police.length ? (


          <div className="grid md:grid-cols-2 gap-4">


          {

          police.map((station,index)=>(


            <div

            key={index}

            className="card-base p-5"

            >


              <h3 className="font-bold">

                {

                station["Police Station"]

                ||

                station.Name

                }


              </h3>



              <p className="text-sm text-gray-500 mt-2">

                {station.Address}

              </p>




              <p className="text-sm mt-2">

                📞 {station.Phone}

              </p>




              {

              station.distance_km &&

              <p className="text-sm text-green-600">

                {station.distance_km} km away

              </p>

              }



            </div>


          ))

          }


          </div>


        )

        :

        (

          <p className="text-gray-500">

            No police stations found.

          </p>

        )

        }



      </div>





    </div>

  )

}


export default Emergency