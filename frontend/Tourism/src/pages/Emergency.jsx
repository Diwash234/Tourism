import { useEffect, useState } from "react"
import useGeolocation from "../hooks/useGeolocation"
import alertApi from "../api/alertApi"
import MapView from "../components/map/MapView"
import nearbyApi from "../api/nearbyApi"
import Loader from "../components/common/Loader"
import PageHeader from "../components/common/PageHeader"
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
      if (c.status === "fulfilled") setContacts(c.value.data.items || c.value.data || [])
      if (h.status === "fulfilled") setHospitals(h.value.data.items || h.value.data || [])
      if (p.status === "fulfilled") setPolice(p.value.data.items || p.value.data || [])
      setLoading(false)
    })
  }, [position])

  return (
    <div className="container-app py-10">
      <PageHeader
        title="Emergency Assistance"
        subtitle="Quick access to nearby hospitals, police stations and emergency contacts."
        icon={FiAlertOctagon}
        theme="red"
      />

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
              <a key={c.id} href={`tel:${c.phone}`} className="card-base p-4 flex items-center justify-between hover:shadow-hover">
                <div>
                  <p className="font-medium text-sm">{c.name}</p>
                  <p className="text-xs text-gray-400">{c.type}</p>
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