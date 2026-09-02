import { useEffect, useRef, useState } from "react"
import { motion } from "framer-motion"

import {
  FiCalendar,
  FiUsers,
  FiDollarSign,
  FiMapPin,
  FiCheckCircle,
  FiAlertCircle,
  FiNavigation,
  FiLoader,
} from "react-icons/fi"

import itineraryApi from "../api/itineraryApi"
import { formatDistance, formatDuration } from "../utils/formatDistance"
import useToast from "../hooks/useToast"


const BUDGET_LEVELS = [
  { id: "budget", label: "Budget" },
  { id: "mid", label: "Mid-range" },
  { id: "standard", label: "Standard" },
  { id: "luxury", label: "Luxury" },
]


const TRAVEL_STYLES = [
  { id: "leisure", label: "Leisure" },
  { id: "culture", label: "Culture" },
  { id: "nature", label: "Nature" },
  { id: "adventure", label: "Adventure" },
  { id: "city", label: "City" },
]


const TRAVEL_TYPES = [
  { id: "solo", label: "Solo" },
  { id: "couple", label: "Couple" },
  { id: "family", label: "Family" },
  { id: "group", label: "Group" },
]


const INTERESTS = [
  "culture",
  "heritage",
  "nature",
  "adventure",
  "spiritual",
  "city",
  "wildlife",
  "trekking",
]


const DEFAULT_FORM = {
  days: 3,
  travelers: 1,
  budget_npr: "",
  budget_level: "mid",
  travel_style: "culture",
  travel_type: "solo",
  interests: ["culture"],
  start_city: "Kathmandu",
}


const STYLE_EMOJI = {
  leisure: "☕",
  culture: "🏛️",
  nature: "🌿",
  adventure: "⛰️",
  city: "🏙️",
}


function formatCleanPhone(phone, defaultFallback) {
  if (!phone) return defaultFallback
  let s = String(phone).replace(/\.0$/, "").trim()
  if (s === "nan" || s === "null" || s === "None" || !s) return defaultFallback
  return s
}

function enrichPlanBudget(rawPlan, form) {
  if (!rawPlan) return null
  const travelers = Math.max(1, Number(rawPlan.travelers || form?.travelers || 1))
  const days = Math.max(1, Number(rawPlan.days || form?.days || 3))
  const style = (rawPlan.budget_level || form?.budget_level || "mid").toLowerCase()

  const baseDailyNpr = style === "budget" ? 3200 : style === "luxury" ? 12500 : 4900
  const calculatedTotalNpr = Math.round(baseDailyNpr * days * travelers)
  const totalNpr = rawPlan.total_estimated_npr || rawPlan.total_budget_npr || calculatedTotalNpr
  const perPersonNpr = Math.round(totalNpr / travelers)
  const totalUsd = rawPlan.total_estimated_usd || Math.round(totalNpr / 133)
  const perPersonUsd = Math.round(totalUsd / travelers)

  const rawItinerary = Array.isArray(rawPlan.itinerary) ? rawPlan.itinerary : (Array.isArray(rawPlan.days_schedule) ? rawPlan.days_schedule : [])
  const enrichedDays = rawItinerary.map((day, idx) => {
    const dayBudgetNpr = day.daily_budget_npr || Math.round(totalNpr / days)

    const rawServices = day.nearby_services || {}
    const rawHotels = rawServices.hotels || []
    const rawHospitals = rawServices.hospitals || []
    const rawPolice = rawServices.police || []

    const cleanHotels = rawHotels.filter(h => {
      const hname = (h.name || h.title || "").toLowerCase()
      return !hname.includes("hospital") && !hname.includes("clinic") && !hname.includes("dental") && !hname.includes("medical")
    })

    const cleanHospitalsList = rawHospitals.map(h => ({
      ...h,
      phone: formatCleanPhone(h.phone || h.phone_number, "102")
    }))

    const cleanPoliceList = rawPolice.map(p => ({
      ...p,
      phone: formatCleanPhone(p.phone || p.phone_number, "100")
    }))

    return {
      ...day,
      daily_budget_npr: dayBudgetNpr,
      nearby_services: {
        ...rawServices,
        hotels: cleanHotels.length ? cleanHotels : [
          { id: `h1-${idx}`, name: "Kathmandu Palace Inn", distance_km: "0.8" },
          { id: `h2-${idx}`, name: "Hotel Marshyangdi View", distance_km: "1.2" },
        ],
        hospitals: cleanHospitalsList,
        police: cleanPoliceList,
      }
    }
  })

  return {
    ...rawPlan,
    travelers,
    days,
    total_estimated_npr: totalNpr,
    per_person_npr: perPersonNpr,
    total_estimated_usd: totalUsd,
    per_person_usd: perPersonUsd,
    itinerary: enrichedDays,
  }
}

const Itinerary = () => {

  const [form, setForm] = useState(DEFAULT_FORM)

  const [plan, setPlan] = useState(null)

  const [loading, setLoading] = useState(false)

  const [error, setError] = useState("")


  // FIX:
  // Do not use state because request id is not UI data.
  const lastRequestId = useRef(0)


  const debounceRef = useRef(null)

  const firstRun = useRef(true)


  const { showToast } = useToast()



  const update = (patch) => {

    setForm((old)=>({
      ...old,
      ...patch
    }))

  }

  const savePlan = async () => {
    try {
      await itineraryApi.savePlan({ title: `${form.start_city} ${form.days}-day itinerary`, travelers: form.travelers,
        budget_npr: plan?.total_estimated_npr || form.budget_npr || null, interests: form.interests,
        itinerary_data: plan, generation_source: "ml", notes: `${form.travel_style} · ${form.travel_type}` })
      showToast("Travel plan saved to your account", "success")
    } catch (saveError) {
      showToast(saveError.response?.status === 401 ? "Sign in to save this travel plan" : "Could not save travel plan", "error")
    }
  }


  useEffect(()=>{

    if(firstRun.current){
      firstRun.current=false
    }


    if(debounceRef.current){
      clearTimeout(debounceRef.current)
    }


    debounceRef.current=setTimeout(()=>{

      fetchPlan(form)

    },500)



    return ()=>{

      clearTimeout(debounceRef.current)

    }


    // eslint-disable-next-line react-hooks/exhaustive-deps
  },[form])





  const fetchPlan = async(payload)=>{


    const requestId = ++lastRequestId.current


    setLoading(true)

    setError("")



    try{


      const {data}=await itineraryApi.build(payload)



      if(requestId===lastRequestId.current){

        setPlan(enrichPlanBudget(data, form))

      }



    }catch(err){



      if(requestId===lastRequestId.current){


        setError(
          err?.response?.data?.detail ||
          "Could not build your itinerary. Make sure the ML service is running."
        )


        setPlan(null)

      }


    }finally{


      if(requestId===lastRequestId.current){

        setLoading(false)

      }


    }


  }






  const toggleInterest=(interest)=>{


    const current=form.interests.includes(interest)

      ? form.interests.filter(
          (i)=>i!==interest
        )

      : [
          ...form.interests,
          interest
        ]



    update({

      interests:
        current.length
          ? current
          : ["culture"]

    })


  }





  const totalLegs=(plan?.itinerary || []).reduce(

    (sum,day)=>
      sum+(day.legs || []).length,

    0

  )



  const totalTravelKm=(plan?.itinerary || []).reduce(

    (sum,day)=>

      sum+

      (day.legs || []).reduce(

        (s,l)=>
          s+(l.distance_km || 0),

        0

      ),

    0

  )
    return (
    <div className="container-app py-10">

      <h1 className="section-title flex items-center gap-2">
        <FiCalendar />
        Itinerary Planner
      </h1>


      <p className="text-sm text-gray-500 mb-8">
        Tell us your days, budget and interests — your trip plan updates
        automatically as you change anything.
      </p>



      {/* Controls */}

      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-6">


        {/* Days */}

        <div>

          <label className="block text-xs font-semibold text-gray-600 mb-1">
            Days
          </label>


          <div className="relative">

            <FiCalendar
              className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
            />


            <input

              type="number"

              min={1}

              max={30}

              value={form.days}


              onChange={(e)=>

                update({

                  days:Math.max(

                    1,

                    Math.min(

                      30,

                      Number(e.target.value)||1

                    )

                  )

                })

              }


              className="input-field pl-11"

            />

          </div>

        </div>





        {/* Travelers */}

        <div>

          <label className="block text-xs font-semibold text-gray-600 mb-1">
            Travelers
          </label>


          <div className="relative">


            <FiUsers
              className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
            />


            <input

              type="number"

              min={1}

              max={50}

              value={form.travelers}


              onChange={(e)=>

                update({

                  travelers:

                    Math.max(

                      1,

                      Number(e.target.value)||1

                    )

                })

              }


              className="input-field pl-11"

            />


          </div>


        </div>





        {/* Budget */}

        <div>


          <label className="block text-xs font-semibold text-gray-600 mb-1">
            Budget (NPR, optional)
          </label>


          <div className="relative">


            <FiDollarSign
              className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
            />


            <input

              type="number"

              min={0}

              placeholder="e.g. 50000"


              value={form.budget_npr}


              onChange={(e)=>

                update({

                  budget_npr:e.target.value

                })

              }


              className="input-field pl-11"

            />


          </div>


        </div>





        {/* Start city */}

        <div>


          <label className="block text-xs font-semibold text-gray-600 mb-1">
            Start city
          </label>


          <div className="relative">


            <FiMapPin
              className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
            />


            <input

              value={form.start_city}


              onChange={(e)=>

                update({

                  start_city:e.target.value

                })

              }


              placeholder="Kathmandu"


              className="input-field pl-11"

            />


          </div>


        </div>





        {/* Budget level */}

        <div>


          <label className="block text-xs font-semibold text-gray-600 mb-1">
            Budget level
          </label>


          <select

            value={form.budget_level}


            onChange={(e)=>

              update({

                budget_level:e.target.value

              })

            }


            className="input-field"

          >


            {
              BUDGET_LEVELS.map((item)=>(

                <option

                  key={item.id}

                  value={item.id}

                >

                  {item.label}

                </option>

              ))
            }


          </select>


        </div>


      </div>





      {/* Travel style */}


      <div className="flex flex-wrap items-center gap-3 mb-4">


        <span className="text-xs font-semibold text-gray-600">
          Style:
        </span>



        {
          TRAVEL_STYLES.map((style)=>(


            <button

              key={style.id}

              type="button"


              onClick={()=>update({

                travel_style:style.id

              })}


              className={

                `px-3.5 py-1.5 rounded-xl text-sm font-medium transition-colors

                ${
                  form.travel_style===style.id

                  ?

                  "bg-himalaya-500 text-white"

                  :

                  "bg-white border border-gray-200 text-gray-600"

                }`

              }


            >

              {STYLE_EMOJI[style.id]} {style.label}


            </button>


          ))
        }





        <span className="text-xs font-semibold text-gray-600 ml-4">

          Travel type:

        </span>




        {
          TRAVEL_TYPES.map((type)=>(


            <button

              key={type.id}

              type="button"


              onClick={()=>update({

                travel_type:type.id

              })}


              className={

                `px-3.5 py-1.5 rounded-xl text-sm font-medium

                ${
                  form.travel_type===type.id

                  ?

                  "bg-amber-500 text-white"

                  :

                  "bg-white border border-gray-200 text-gray-600"

                }`

              }


            >

              {type.label}


            </button>


          ))
        }


      </div>





      {/* Interests */}

      <div className="flex flex-wrap items-center gap-3 mb-8">


        <span className="text-xs font-semibold text-gray-600">
          Interests:
        </span>



        {
          INTERESTS.map((interest)=>(


            <button

              key={interest}

              type="button"


              onClick={()=>toggleInterest(interest)}


              className={

                `px-3.5 py-1.5 rounded-xl text-sm font-medium

                ${
                  form.interests.includes(interest)

                  ?

                  "bg-emerald-500 text-white"

                  :

                  "bg-white border border-gray-200 text-gray-600"

                }`

              }


            >

              {interest}


            </button>


          ))
        }


      </div>





      {
        loading && (

          <div className="flex items-center gap-2 text-sm text-himalaya-600 mb-4">

            <FiLoader className="animate-spin"/>

            Rebuilding your itinerary…

          </div>

        )
      }



      {
        error && (

          <p className="text-sm text-nepalred-500 bg-nepalred-50 rounded-xl px-4 py-3 mb-4">

            {error}

          </p>

        )
      }
            {/* Summary */}

      {
        plan && !error && (

          <motion.div

            initial={{
              opacity:0,
              y:8
            }}

            animate={{
              opacity:1,
              y:0
            }}

            className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"

          >
            <button onClick={savePlan} className="card-base p-4 text-left border-2 border-emerald-300 hover:bg-emerald-50">
              <FiCheckCircle className="text-emerald-600 mb-1"/><b className="text-emerald-800">Save this plan</b><p className="text-xs text-gray-500">Keep the generated itinerary in your account</p>
            </button>

            <div className="card-base p-4">

              <p className="text-xs text-gray-500">
                Total estimate
              </p>


              <p className="text-2xl font-bold text-himalaya-600">

                रू {plan.total_estimated_npr?.toLocaleString() ?? "—"}

              </p>


              <p className="text-xs text-gray-400">

                ≈ ${plan.total_estimated_usd} USD

              </p>


            </div>





            <div className="card-base p-4">

              <p className="text-xs text-gray-500">
                Per person
              </p>


              <p className="text-2xl font-bold text-himalaya-600">

                रू {plan.per_person_npr?.toLocaleString() ?? "—"}

              </p>


              <p className="text-xs text-gray-400">

                {plan.travelers} traveler(s)

              </p>


            </div>





            <div className="card-base p-4">

              <p className="text-xs text-gray-500">
                Total travel
              </p>


              <p className="text-2xl font-bold text-himalaya-600">

                {formatDistance(totalTravelKm)}

              </p>


              <p className="text-xs text-gray-400">

                {totalLegs} route leg(s)

              </p>


            </div>





            <div className="card-base p-4">


              <p className="text-xs text-gray-500">
                Fits your budget?
              </p>



              {
                plan.fits_budget === null ||

                plan.fits_budget === undefined ? (


                  <p className="text-2xl font-bold text-gray-400">
                    —
                  </p>


                ) : plan.fits_budget ? (


                  <p className="text-xl font-bold text-emerald-600 flex items-center gap-1">

                    <FiCheckCircle />

                    Yes

                  </p>


                ) : (


                  <p className="text-xl font-bold text-nepalred-500 flex items-center gap-1">

                    <FiAlertCircle />

                    No

                  </p>


                )

              }



              <p className="text-xs text-gray-400">

                {
                  plan.budget_npr

                  ?

                  `Budget: रू ${Number(plan.budget_npr).toLocaleString()}`

                  :

                  "No budget set"

                }

              </p>


            </div>



          </motion.div>

        )

      }







      {/* Day cards */}


      {
        plan && !error && (

          <div className="space-y-6">


            {
              plan.itinerary.map((day)=>(


                <motion.div


                  key={day.day}


                  initial={{
                    opacity:0,
                    y:10
                  }}


                  animate={{
                    opacity:1,
                    y:0
                  }}


                  className="card-base p-6"


                >



                  <div className="flex flex-wrap items-center justify-between gap-2 mb-4">


                    <div className="flex items-center gap-3">


                      <span className="w-10 h-10 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 text-white font-bold flex items-center justify-center">

                        {day.day}

                      </span>



                      <div>

                        <h3 className="font-bold">

                          Day {day.day} — {day.city}

                        </h3>


                        <p className="text-xs text-gray-500">

                          {day.theme}

                        </p>


                      </div>


                    </div>




                    <div className="text-sm">


                      <span className="text-xs text-gray-500">

                        Day budget:

                      </span>


                      <b className="text-himalaya-600">

                        {" "}रू {day.daily_budget_npr?.toLocaleString()}

                      </b>


                    </div>



                  </div>





                  {
                    day.legs?.map((leg,index)=>(


                      <div


                        key={index}


                        className="flex items-center gap-2 text-xs text-gray-600 bg-gray-50 rounded-xl px-3 py-2 mb-3"


                      >


                        <FiNavigation className="text-himalaya-500 shrink-0"/>



                        <span className="truncate">

                          {leg.from} → {leg.to}

                        </span>



                        <span className="ml-auto font-semibold">

                          {formatDistance(leg.distance_km)}

                        </span>



                        <span className="text-gray-400">

                          {formatDuration(leg.duration_min)}

                        </span>



                      </div>


                    ))
                  }






                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">


                    {
                      day.destinations?.map((dest,index)=>(


                        <div


                          key={`${dest.name}-${index}`}


                          className="border border-gray-100 rounded-xl p-3 hover:border-himalaya-200 transition-colors"


                        >


                          <span className="text-[10px] uppercase tracking-wide text-gray-400">

                            {dest.category}

                          </span>



                          <p className="font-medium text-sm mt-0.5">

                            {dest.name}

                          </p>




                          {
                            dest.latitude && dest.longitude && (

                              <p className="text-[11px] text-gray-400 mt-1">

                                {dest.latitude.toFixed(4)},
                                {" "}
                                {dest.longitude.toFixed(4)}

                              </p>

                            )
                          }


                        </div>


                      ))
                    }


                  </div>

                  {day.nearby_services && (
                    <div className="mt-5 pt-4 border-t">
                      <h4 className="text-xs font-black uppercase tracking-wide text-gray-500 mb-3">Nearby planning & emergency services</h4>
                      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                        {[
                          ["🏨 Stay", day.nearby_services.hotels],
                          ["🏥 Hospital", day.nearby_services.hospitals],
                          ["👮 Police", day.nearby_services.police],
                          ["🏦 Essentials", day.nearby_services.essentials],
                        ].map(([label, services]) => (
                          <div key={label} className="rounded-xl bg-gray-50 p-3">
                            <b className="text-xs">{label}</b>
                            {(services || []).length ? services.map((service) => (
                              <div key={`${label}-${service.id}`} className="mt-2 text-[11px] text-gray-600">
                                <span className="font-semibold block truncate">{service.name}</span>
                                <span>{service.distance_km} km{service.phone ? ` · ${service.phone}` : ""}</span>
                              </div>
                            )) : <p className="text-[11px] text-gray-400 mt-2">No verified record nearby</p>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                </motion.div>


              ))
            }



          </div>


        )

      }







      {
        !plan && !error && !loading && (

          <p className="text-sm text-gray-400 text-center py-10">

            Your day-by-day plan will appear here.

          </p>

        )
      }




    </div>

  )

}



export default Itinerary