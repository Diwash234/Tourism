import L from "leaflet"

const makeIcon = (color) =>
  new L.Icon({
    iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-${color}.png`,
    shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  })

export const userIcon = makeIcon("blue")
export const destinationIcon = makeIcon("red")
export const hospitalIcon = makeIcon("green")
export const policeIcon = makeIcon("violet")
export const attractionIcon = makeIcon("gold")