import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  useMap,
} from "react-leaflet"

import { useEffect } from "react"

import { MAP_TILE_URL, DEFAULT_MAP_CENTER } from "../../utils/constants"

import {
  userIcon,
  destinationIcon,
  hospitalIcon,
  policeIcon,
  attractionIcon,
} from "./icons"



const normalizeLocation = (place) => {

  if (!place) return null


  return {
    lat:
      Number(place.lat) ||
      Number(place.latitude),

    lng:
      Number(place.lng) ||
      Number(place.longitude),

    name:
      place.name ||
      place.Name ||
      "Location"
  }

}



const Recenter = ({center}) => {

  const map = useMap()

  useEffect(()=>{

    if(center){
      map.setView(
        [center.lat, center.lng],
        13
      )
    }

  },[center,map])


  return null
}



const MapView = ({

  center,

  userLocation,

  destination,

  nearbyAttractions=[],

  hospitals=[],

  policeStations=[],

  route=[],

  height="420px"

})=>{


  const user =
    normalizeLocation(userLocation)


  const dest =
    normalizeLocation(destination)



  const mapCenter =
    normalizeLocation(center)
    ||
    user
    ||
    DEFAULT_MAP_CENTER



  const fixedRoute =
    route.map(point=>{


      if(Array.isArray(point)){
        return point
      }


      return [
        Number(point.lat || point.latitude),
        Number(point.lng || point.longitude)
      ]

    })



return (

<div
style={{height}}
className="rounded-xl overflow-hidden shadow-card"
>


<MapContainer

center={[
mapCenter.lat,
mapCenter.lng
]}

zoom={13}

scrollWheelZoom={true}

style={{
height:"100%",
width:"100%"
}}

>


<TileLayer

attribution="&copy; OpenStreetMap contributors"

url={MAP_TILE_URL}

/>



<Recenter center={mapCenter}/>




{
user &&
(

<Marker

position={[
user.lat,
user.lng
]}

icon={userIcon}

>

<Popup>
You are here
</Popup>

</Marker>

)

}





{
dest &&

(

<Marker

position={[
dest.lat,
dest.lng
]}

icon={destinationIcon}

>

<Popup>

{dest.name}

</Popup>


</Marker>

)

}





{
nearbyAttractions.map((p,index)=>{


const place =
normalizeLocation(p)


if(!place.lat || !place.lng)
return null


return (

<Marker

key={"attr"+index}

position={[
place.lat,
place.lng
]}

icon={attractionIcon}

>

<Popup>

{place.name}

</Popup>


</Marker>

)


})

}





{
hospitals.map((p,index)=>{


const place =
normalizeLocation(p)


if(!place.lat || !place.lng)
return null


return (

<Marker

key={"hospital"+index}

position={[
place.lat,
place.lng
]}

icon={hospitalIcon}

>

<Popup>

🏥 {place.name}

</Popup>

</Marker>

)


})

}





{
policeStations.map((p,index)=>{


const place =
normalizeLocation(p)


if(!place.lat || !place.lng)
return null


return (

<Marker

key={"police"+index}

position={[
place.lat,
place.lng
]}

icon={policeIcon}

>

<Popup>

🚓 {place.name}

</Popup>


</Marker>

)


})

}





{
fixedRoute.length > 1 &&

<Polyline

positions={fixedRoute}

color="red"

weight={5}

/>

}



</MapContainer>


</div>

)


}


export default MapView