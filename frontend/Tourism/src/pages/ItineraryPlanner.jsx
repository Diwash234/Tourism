import { useState } from "react"
import { motion } from "framer-motion"

import {
    FiCalendar,
    FiMapPin,
    FiSearch,
    FiDollarSign,
    FiClock,
    FiSun,
    FiMoon
} from "react-icons/fi"

import destinationApi from "../api/destinationApi"
import itineraryApi from "../api/itineraryApi"

import EmptyState from "../components/common/EmptyState"



const ItineraryPlanner = ()=>{


const [search,setSearch] = useState("")

const [destination,setdestination] = useState([])

const [selectedPlaces,setSelectedPlaces] = useState([])


const [days,setDays] = useState(3)

const [budget,setBudget] = useState(10000)


const [travelStyle,setTravelStyle] =
useState("Normal")


const [travelType,setTravelType] =
useState("Solo")


const [interests,setInterests] =
useState([])


const [itinerary,setItinerary] =
useState(null)


const [loading,setLoading] =
useState(false)



const interestOptions=[
"Nature",
"Adventure",
"Culture",
"Food",
"History",
"Hiking"
]





const searchDestination = async(value)=>{


setSearch(value)


if(!value.trim()){

setdestination([])

return

}


try{


const response =
await destinationApi.search(value)


setdestination(
response.data.results ||
response.data ||
[]
)


}

catch(error){

console.log(error)

setdestination([])

}


}






const toggleDestination=(place)=>{


const exists =
selectedPlaces.find(
p=>p.id===place.id
)



if(exists){


setSelectedPlaces(
selectedPlaces.filter(
p=>p.id!==place.id
)
)


}

else{


setSelectedPlaces([
...selectedPlaces,
place
])


}


}







const toggleInterest=(item)=>{


if(interests.includes(item)){


setInterests(
interests.filter(
i=>i!==item
)
)


}

else{


setInterests([
...interests,
item
])


}


}








const generateItinerary=async()=>{


if(selectedPlaces.length===0){

alert(
"Please select destination"
)

return

}


setLoading(true)


try{


const payload={

destination: selectedPlaces[0].name,

days:Number(days),

budget:Number(budget),

travel_style:travelStyle,

travel_type:travelType,

interests

}


console.log(
"ITINERARY PAYLOAD",
payload
)



const response =
await itineraryApi.createItinerary(
payload
)



setItinerary(
response.data.itinerary
)


}


catch(error){


console.log(
error.response?.data
)


alert(
JSON.stringify(
error.response?.data
)
)


}


finally{

setLoading(false)

}



}








return(

<div className="container-app py-10 theme-forest">


<h1 className="
section-title
flex
gap-3
items-center
">


<FiCalendar/>

Smart Travel Itinerary Planner


</h1>





<div className="
grid
lg:grid-cols-3
gap-6
mt-8
">



{/* LEFT PANEL */}


<div className="
card-base
p-6
space-y-5
">



<h2 className="
font-bold
text-xl
">

Trip Configuration

</h2>




<div className="relative">


<FiSearch
className="
absolute
top-3
left-3
text-gray-400
"
/>


<input

value={search}

onChange={
e=>
searchDestination(
e.target.value
)
}

placeholder="
Search destination...
"

className="
w-full
border
rounded-lg
p-3
pl-10
"

/>



{
destination.length>0 &&


<div className="
absolute
z-30
bg-white
border
w-full
shadow
rounded-lg
mt-2
">


{
destination.map(place=>(


<div

key={place.id}

onClick={()=>
toggleDestination(place)
}

className="
p-3
cursor-pointer
hover:bg-green-50
flex
gap-2
items-center
"


>


<input

type="checkbox"

checked={
selectedPlaces.some(
p=>p.id===place.id
)
}

readOnly

/>


<FiMapPin/>


{place.name}


</div>


))


}


</div>


}



</div>





{
selectedPlaces.map(place=>(

<div

key={place.id}

className="
bg-green-50
rounded-lg
p-3
"

>

📍 {place.name}


</div>


))

}







<div>


<label>
Number of Days
</label>


<input

type="number"

value={days}

onChange={
e=>setDays(e.target.value)
}

className="
border
rounded
w-full
p-2
"

/>


</div>







<div>


<label>
Budget NPR
</label>


<input

type="number"

value={budget}

onChange={
e=>setBudget(e.target.value)
}

className="
border
rounded
w-full
p-2
"

/>


</div>








<div>


<label>
Travel Style
</label>


<select

value={travelStyle}

onChange={
e=>setTravelStyle(e.target.value)
}

className="
border
rounded
w-full
p-2
"

>


<option>
Budget
</option>


<option>
Normal
</option>


<option>
Luxury
</option>


</select>


</div>







<div>


<label>
Travel Type
</label>


<select

value={travelType}

onChange={
e=>setTravelType(e.target.value)
}

className="
border
rounded
w-full
p-2
"

>


<option>
Solo
</option>


<option>
Couple
</option>


<option>
Family
</option>


<option>
Group
</option>


</select>


</div>






<div>


<label>
Interests
</label>


<div className="
grid
grid-cols-2
gap-2
">


{
interestOptions.map(item=>(


<button

key={item}

onClick={()=>
toggleInterest(item)
}

className={`
border
rounded
p-2
text-sm
${interests.includes(item)
?
"bg-green-600 text-white"
:
""
}
`}

>


{item}


</button>


))


}


</div>


</div>






<button

onClick={generateItinerary}

disabled={loading}

className="
bg-green-600
text-white
rounded-lg
p-3
w-full
"


>


{
loading
?
"Generating..."
:
"Generate Itinerary"
}


</button>





</div>









{/* RESULT */}



<div className="
lg:col-span-2
">


{

itinerary ?



<div className="space-y-6">


<div className="
card-base
p-5
">


<h2 className="
text-2xl
font-bold
">

{itinerary.destination}

</h2>


<p>

📍 Latitude:
{itinerary.coordinates.latitude}

</p>


<p>

📍 Longitude:
{itinerary.coordinates.longitude}

</p>



<div className="
flex
gap-5
mt-3
">


<span>

<FiClock className="inline"/>

{itinerary.days} Days

</span>


<span>

<FiDollarSign className="inline"/>

NPR {itinerary.budget}

</span>


</div>


</div>








{
itinerary.plan.map(day=>(


<motion.div

key={day.day}

initial={{
opacity:0,
y:20
}}

animate={{
opacity:1,
y:0
}}

className="
card-base
p-6
"


>


<h3 className="
text-xl
font-bold
mb-4
">

Day {day.day}

</h3>




<div className="
grid
md:grid-cols-3
gap-4
">


<div className="
bg-yellow-50
p-4
rounded
">

<FiSun/>

<h4>
Morning
</h4>


{
day.morning.map(
(item,i)=>(

<p key={i}>
• {item}
</p>

)

)
}


</div>






<div className="
bg-orange-50
p-4
rounded
">


<h4>
Afternoon
</h4>


{
day.afternoon.map(
(item,i)=>(

<p key={i}>
• {item}
</p>

)

)
}


</div>






<div className="
bg-blue-50
p-4
rounded
">


<FiMoon/>


<h4>
Evening
</h4>


{
day.evening.map(
(item,i)=>(

<p key={i}>
• {item}
</p>

)

)
}


</div>



</div>




</motion.div>


))

}



</div>



:


<EmptyState

title="
Create your travel plan
"

subtitle="
Select destination and generate smart itinerary
"

/>


}



</div>



</div>



</div>


)

}


export default ItineraryPlanner