import { useEffect, useState } from "react"
import { FiSun, FiCloud, FiCloudRain, FiMapPin, FiHeart } from "react-icons/fi"

import useAuth from "../hooks/useAuth"
import useGeolocation from "../hooks/useGeolocation"

import weatherApi from "../api/weatherApi"
import recommendationApi from "../api/recommendationApi"
import alertApi from "../api/alertApi"
import budgetApi from "../api/budgetApi"
import userApi from "../api/userApi"

import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"

import BudgetCard from "../components/cards/BudgetCard"
import AlertCard from "../components/cards/AlertCard"
import RecommendationCard from "../components/cards/RecommendationCard"
import DestinationCard from "../components/cards/DestinationCard"


const weatherIcons = {
  clear: FiSun,
  clouds: FiCloud,
  rain: FiCloudRain,
}


const Dashboard = () => {

  const { user } = useAuth()
  const { position } = useGeolocation()


  const [weather,setWeather] = useState(null)
  const [recommendations,setRecommendations] = useState([])
  const [alerts,setAlerts] = useState([])
  const [budget,setBudget] = useState(null)
  const [favorites,setFavorites] = useState([])

  const [loading,setLoading] = useState(true)


  useEffect(()=>{

    const loadDashboard = async()=>{

      try{

        const [
          recRes,
          alertRes,
          budgetRes,
          favRes
        ] = await Promise.all([

          recommendationApi.getPersonalized(),

          alertApi.getAlerts({
            limit:4
          }),

          budgetApi.getSummary(),

          userApi.getFavorites()

        ])


        setRecommendations(
          recRes.data.items ||
          recRes.data.recommendations ||
          recRes.data ||
          []
        )


        setAlerts(
          alertRes.data.items ||
          alertRes.data ||
          []
        )


        setBudget(
          budgetRes.data
        )


        setFavorites(
          favRes.data.items ||
          favRes.data ||
          []
        )


      }
      catch(error){

        console.log(
          "Dashboard error:",
          error.response?.data || error.message
        )

      }
      finally{

        setLoading(false)

      }

    }


    loadDashboard()


  },[])



  useEffect(()=>{


    if(position){

      weatherApi
      .getCurrentWeather({

        lat:position.lat,
        lng:position.lng

      })
      .then(res=>{

        setWeather(
          res.data
        )

      })
      .catch(err=>{

        console.log(
          "Weather error:",
          err.message
        )

      })

    }


  },[position])



  const WeatherIcon =
    weatherIcons[
      weather?.condition?.toLowerCase()
    ]
    ||
    FiSun



  if(loading){

    return <Loader fullScreen={false}/>

  }



return (

<div className="space-y-8">


<div>

<h1 className="text-2xl font-bold">

Welcome back,
{" "}
{user?.name || "Traveler"}
👋

</h1>


<p className="text-gray-500 text-sm">

Here is what is happening with your trips today.

</p>

</div>



<div className="grid grid-cols-1 md:grid-cols-3 gap-6">


<div className="card-base p-5 flex justify-between items-center">


<div>

<p className="text-sm text-gray-500 flex gap-1">

<FiMapPin/>

{weather?.location || "Current Location"}

</p>


<p className="text-3xl font-bold">

{weather?.temperature ?? "--"}°

</p>


<p className="text-gray-400">

{weather?.condition || "Loading..."}

</p>


</div>


<WeatherIcon size={40}/>


</div>



<BudgetCard
label="Total Budget"
amount={budget?.total}
/>


<BudgetCard
label="Spent"
amount={budget?.spent}
accent="secondary"
/>


</div>




<section>

<h2 className="font-semibold text-lg mb-4">

Latest Alerts

</h2>


{
alerts.length ?

<div className="grid md:grid-cols-2 gap-4">

{
alerts.map(a=>

<AlertCard
key={a.id}
alert={a}
/>

)
}

</div>

:

<EmptyState
title="No alerts"
subtitle="No safety alerts available"
/>

}


</section>





<section>


<h2 className="font-semibold text-lg mb-4">

Recommended For You

</h2>


{
recommendations.length ?

<div className="grid md:grid-cols-2 gap-4">

{
recommendations.map(r=>

<RecommendationCard
key={r.id}
item={r}
/>

)

}

</div>


:

<EmptyState
title="No recommendations"
subtitle="Explore places to get recommendations"
/>


}


</section>





<section>


<h2 className="font-semibold text-lg mb-4 flex gap-2">

<FiHeart/>

Favorite Places

</h2>


{
favorites.length ?

<div className="grid lg:grid-cols-3 gap-6">

{
favorites.map(d=>

<DestinationCard
key={d.id}
destination={d}
isFavorite
/>

)

}

</div>

:

<EmptyState
title="No favorites"
subtitle="Save destinations you like"
/>


}


</section>



</div>

)


}


export default Dashboard