import { FiPhoneCall, FiHome, FiShield, FiPlus } from "react-icons/fi"

export default function NearbyServices({ hospitalInfo, hotelInfo, policeInfo }) {
  return (
    <div className="card-base p-6 shadow-xl border border-purple-100 rounded-3xl space-y-4">
      <h3 className="font-bold text-base text-gray-900 flex items-center gap-2">
        <FiPhoneCall className="text-rose-600" /> Nearby Essential Services
      </h3>

      <div className="space-y-3 text-xs">
        <div className="p-3 rounded-xl bg-gray-50 border border-gray-100 flex items-start gap-2.5">
          <FiPhoneCall className="text-purple-600 mt-0.5 shrink-0" size={15} />
          <div>
            <p className="font-bold text-gray-800">Nearest Hospital / Clinic</p>
            <p className="text-purple-700 font-semibold mt-0.5">{hospitalInfo || "District Zonal Hospital"}</p>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-gray-50 border border-gray-100 flex items-start gap-2.5">
          <FiHome className="text-purple-600 mt-0.5 shrink-0" size={15} />
          <div>
            <p className="font-bold text-gray-800">Nearest Hotel / Lodge</p>
            <p className="text-purple-700 font-semibold mt-0.5">{hotelInfo || "Nearby boutique lodge & homestays"}</p>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-gray-50 border border-gray-100 flex items-start gap-2.5">
          <FiShield className="text-purple-600 mt-0.5 shrink-0" size={15} />
          <div>
            <p className="font-bold text-gray-800">Tourist Police Station</p>
            <p className="text-purple-700 font-semibold mt-0.5">{policeInfo || "Tourist Police Helpdesk (1144)"}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
