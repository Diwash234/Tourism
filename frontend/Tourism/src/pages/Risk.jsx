import {useEffect,useState} from "react"

import {predictRisk} from "../services/mlService"

import Loader from "../components/common/Loader"



const Risk =()=>{


const [risk,setRisk]=useState(null)

const [loading,setLoading]=useState(true)



useEffect(()=>{


navigator.geolocation.getCurrentPosition(

async(position)=>{


const result =
await predictRisk({

latitude:
position.coords.latitude,

longitude:
position.coords.longitude

})


setRisk(result)

setLoading(false)


}


)



},[])





if(loading)

return <Loader />




return (

<div className="container-app py-10">


<h1 className="section-title">

Travel Safety Risk

</h1>



<div className="card-base p-6 mt-5">


<p>

Risk Category:

<strong>

{risk?.risk_category}

</strong>

</p>



<p>

Tourism Risk Index:

{risk?.tourism_risk_index}

</p>



</div>


</div>


)


}


export default Risk