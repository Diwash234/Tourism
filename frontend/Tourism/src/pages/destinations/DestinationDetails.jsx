import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import {
  FiStar,
  FiMapPin,
  FiHeart,
  FiGlobe,
  FiPhoneCall,
  FiDollarSign
} from "react-icons/fi"

import destinationApi from "../../api/destinationApi"
import budgetApi from "../../api/budgetApi"
import userApi from "../../api/userApi"

import MapView from "../../components/map/MapView"
import Loader from "../../components/common/Loader"
import useGeolocation from "../../hooks/useGeolocation"

import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"

import { RISK_LEVELS } from "../../utils/constants"
import { formatCurrency } from "../../utils/helpers"


const DestinationDetails = () => {

  const { slug } = useParams()

  const { isAuthenticated } = useAuth()
  const { showToast } = useToast()


  const [destination,setDestination] = useState(null)
  const [budget,setBudget] = useState(null)
  const [essentials,setEssentials] = useState(null)

  const [risk,setRisk] = useState(null)

  const [isFavorite,setIsFavorite] = useState(false)

  const [loading,setLoading] = useState(true)
  const { position } = useGeolocation()



  useEffect(()=>{

    setLoading(true)


    const params = {}
    if (position) {
      params.latitude = position.lat
      params.longitude = position.lng
    }

    Promise.allSettled([

      destinationApi.getById(slug, params),
      destinationApi.getEssentials(slug, params),

      // Remove this if backend does not exist
      // alertApi.getRiskStatus(slug),


      budgetApi.estimate({
        destinationId:slug,
        travelers:1,
        days:3
      })

    ])

    .then(([destRes,essentialsRes,budgetRes])=>{


      if(destRes.status==="fulfilled"){
        setDestination(destRes.value.data)
      }

      if(essentialsRes?.status==="fulfilled"){
        setEssentials(essentialsRes.value.data)
      }


      if(budgetRes.status==="fulfilled"){
        setBudget(budgetRes.value.data)
      }


    })

    .finally(()=>{

      setLoading(false)

    })


  },[slug, position])




  const toggleFavorite = async()=>{


    if(!isAuthenticated){

      return showToast(
        "Please login to save favorites",
        "info"
      )

    }


    try{


      if(isFavorite){

        await userApi.removeFavorite(slug)

      }
      else{

        await userApi.addFavorite(slug)

      }


      setIsFavorite(!isFavorite)


    }
    catch(error){

      showToast(
        "Could not update favorite",
        "error"
      )

    }


  }




  if(loading)
    return <Loader fullScreen />



  if(!destination){

    return (

      <div className="container-app py-16 text-center text-gray-400">

        Destination not found.

      </div>

    )

  }



  const level =
    RISK_LEVELS[
      risk?.level?.toUpperCase()
    ]
    ||
    RISK_LEVELS.LOW





return (

<div className="container-app py-10">


{/* Images */}

<div className="
grid grid-cols-1 lg:grid-cols-3
gap-3 mb-8 rounded-xl overflow-hidden
">


<img

src={
destination.cover_image_url ||
"https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=900"
}

alt={destination.name}

className="
lg:col-span-2
h-80
w-full
object-cover
"

/>



<div className="grid grid-rows-2 gap-3">


<img

src={
destination.gallery?.[0]?.image ||
destination.gallery?.[0]?.external_url ||
"https://images.unsplash.com/photo-1519681393784-d120267933ba?w=500"
}

alt="gallery"

className="
h-full
w-full
object-cover
"

/>



<img

src={
destination.gallery?.[1]?.image ||
destination.gallery?.[1]?.external_url ||
"https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=500"
}

alt="gallery"

className="
h-full
w-full
object-cover
"

/>


</div>


</div>





<div className="
grid grid-cols-1 lg:grid-cols-3 gap-8
">



<div className="
lg:col-span-2 space-y-8
">


{/* Title */}

<div>


<div className="
flex justify-between items-center
">


<h1 className="text-3xl font-bold">

{destination.name}

</h1>



<button

onClick={toggleFavorite}

className="
p-2 rounded-full border
"

>


<FiHeart

className={
isFavorite
?
"text-primary-500 fill-primary-500"
:
"text-gray-500"
}

/>


</button>


</div>





<p className="
text-gray-500 flex gap-1 mt-2
">

<FiMapPin size={14}/>


{
destination.address
},

{
destination.city
},

{
destination.country
}


</p>





<div className="
flex items-center gap-1
text-yellow-500 mt-2
">


<FiStar className="fill-yellow-400"/>


{
destination.average_rating || "4.5"
}

rating


</div>


</div>





{/* Description */}


<div>

<h2 className="font-semibold text-lg mb-2">

About this place

</h2>


<p className="
text-gray-600 text-sm
">

{
destination.description ||
"No description available"
}


</p>


</div>







{/* Videos */}


{
destination.videos?.length > 0 &&


<div>


<h2 className="
font-semibold text-lg mb-2
">

Video

</h2>


<video

controls

className="
w-full rounded-xl
"

src={
destination.videos[0].video ||
destination.videos[0].url
}

/>


</div>


}







{/* Map */}


<div>


<h2 className="
font-semibold text-lg mb-2
">

Location

</h2>



<MapView


center={[
destination.latitude,
destination.longitude
]}



destination={{

latitude:
destination.latitude,

longitude:
destination.longitude,

name:
destination.name

}}



nearbyAttractions={[]}



height="380px"


/>


</div>



</div>








{/* Sidebar */}


<div className="space-y-6">





<div className="card-base p-5">


<h3 className="
font-semibold mb-3 flex gap-2
">

<FiGlobe/>

Safety Status

</h3>



<span className={`
${level.color}
px-3 py-1 rounded-full text-xs
`}>

{level.label}

Risk

</span>


<p className="
text-sm text-gray-500 mt-2
">

{
risk?.summary ||
"No active risk advisory"
}


</p>


</div>






<div className="card-base p-5">


<h3 className="
font-semibold mb-3 flex gap-2
">


<FiDollarSign/>

Budget Estimate


</h3>



<p className="
text-2xl font-bold text-primary-500
">


{
formatCurrency(
budget?.total || 0
)

}


</p>


<p className="text-xs text-gray-400">

Estimated for 1 traveler, 3 days

</p>



</div>






<div className="card-base p-5">


<h3 className="
font-semibold mb-3 flex gap-2
">

<FiPhoneCall/>

Emergency Contacts

</h3>



<p className="
text-sm text-gray-500
">

Police:100 · Ambulance:102 · Fire:101

</p>


</div>






<button className="btn-outline w-full">

Translate Page

</button>




</div>




</div>


</div>


)

}


export default DestinationDetails
