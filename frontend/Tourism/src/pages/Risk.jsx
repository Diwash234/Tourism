import { useEffect, useState } from "react"
import PageHeader from "../components/common/PageHeader"

import { getRisk as predictRisk } from "../services/mlService"

import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"


const Risk = () => {

  const [risk, setRisk] = useState(null)
  const [loading, setLoading] = useState(true)


  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => {

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

          console.log(
            "Risk prediction error:",
            error
          )

          setRisk(null)


        } finally {

          setLoading(false)

        }

      },


      (error) => {

        console.log(
          "Location error:",
          error
        )

        setLoading(false)

      }

    )
    }, 0)
    return () => clearTimeout(t)
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


      <PageHeader title="Travel Safety Risk" />



      <div className="card-base p-6 mt-5">


        <p>

          Risk Category:

          <strong className="ml-2">

            {risk?.risk_category || "Unknown"}

          </strong>

        </p>

        {risk?.degraded && (
          <p className="mt-2 text-xs font-semibold text-amber-800 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">
            ⚠️ {risk.data_note || "Limited local risk data for this location — showing a general estimate."}
          </p>
        )}



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