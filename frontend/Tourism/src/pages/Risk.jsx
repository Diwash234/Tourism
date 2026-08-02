import { useEffect, useState } from "react"

import { predictRisk } from "../services/mlService"

import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"


const Risk = () => {

  const [risk, setRisk] = useState(null)
  const [loading, setLoading] = useState(true)


  useEffect(() => {

    if (!navigator.geolocation) {
      setLoading(false)
      return
    }


    navigator.geolocation.getCurrentPosition(

      async (position) => {

        try {

          const result = await predictRisk({

            latitude: position.coords.latitude,

            longitude: position.coords.longitude

          })


          setRisk(result)

        } catch (error) {

          console.log("Risk prediction error:", error)

          setRisk(null)

        } finally {

          setLoading(false)

        }

      },


      (error) => {

        console.log("Location error:", error)

        setLoading(false)

      }

    )


  }, [])



  if (loading)

    return <Loader />



  if (!risk)

    return (

      <div className="container-app py-10 theme-amber">

        <EmptyState

          title="Risk data unavailable"

          subtitle="Enable location access to check travel safety risk."

        />

      </div>

    )



  return (

    <div className="container-app py-10 theme-amber">


      <h1 className="section-title">

        Travel Safety Risk

      </h1>



      <div className="card-base p-6 mt-5">


        <p>

          Risk Category:

          <strong className="ml-2">

            {risk?.risk_category || "Unknown"}

          </strong>

        </p>



        <p className="mt-3">

          Tourism Risk Index:

          <strong className="ml-2">

            {risk?.tourism_risk_index ?? "N/A"}

          </strong>

        </p>


      </div>


    </div>

  )

}


export default Risk