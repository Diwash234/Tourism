import { useEffect, useState } from "react"
import useGeolocation from "../hooks/useGeolocation"
import alertApi from "../api/alertApi"
import MapView from "../components/map/MapView"
import nearbyApi from "../api/nearbyApi"
import Loader from "../components/common/Loader"
import { FiPhoneCall, FiAlertOctagon } from "react-icons/fi"

const Emergency = () => {
  const { position } = useGeolocation()
  const [contacts, setContacts] = useState([])
  const [hospitals, setHospitals] = useState([])
  const [police, setPolice] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!position) return
    Promise.allSettled([
      alertApi.getEmergencyContacts({ lat: position.lat, lng: position.lng }),
      nearbyApi.getHospitals({ lat: position.lat, lng: position.lng }),
      nearbyApi.getPoliceStations({ lat: position.lat, lng: position.lng }),
    ]).then(([c, h, p]) => {
      // These three backend endpoints return plain arrays (not paginated),
      // so `.items` is undefined and it correctly falls through to
      // `.data` itself — this part was already fine.
      if (c.status === "fulfilled") setContacts(c.value.data.items || c.value.data || [])
      if (h.status === "fulfilled") setHospitals(h.value.data.items || h.value.data || [])
      if (p.status === "fulfilled") setPolice(p.value.data.items || p.value.data || [])
      setLoading(false)
    })
  }, [position])

  return (
    <div className="container-app py-10">
      <h1 className="section-title flex items-center gap-2 text-red-500">
        <FiAlertOctagon /> Emergency Assistance
      </h1>
      <p className="text-gray-500 text-sm mb-6">
        Quick access to nearby hospitals, police stations and emergency contacts.
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <MapView userLocation={position} hospitals={hospitals} policeStations={police} height="450px" />
        </div>
        <div className="space-y-4">
          <h3 className="font-semibold">Emergency Contacts</h3>
          {loading ? (
            <Loader />
          ) : contacts.length ? (
            contacts.map((c) => (
              // FIXED: the backend's EmergencyContactSerializer fields are
              // `phone_number` and `contact_type` — this was reading
              // `c.phone` and `c.type`, which don't exist, so every card
              // rendered a dead `tel:undefined` link and a blank type line.
              <a key={c.id} href={`tel:${c.phone_number}`} className="card-base p-4 flex items-center justify-between hover:shadow-hover">
                <div>
                  <p className="font-medium text-sm">{c.name}</p>
                  <p className="text-xs text-gray-400">{c.contact_type}</p>
                </div>
                <FiPhoneCall className="text-primary-500" />
              </a>
            ))
          ) : (
            <div className="card-base p-4 text-sm text-gray-500">
              National Police: 100 · Ambulance: 102 · Fire: 101
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Emergency