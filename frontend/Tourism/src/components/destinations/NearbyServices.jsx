import { FiPhoneCall, FiHome, FiShield, FiPlus } from "react-icons/fi"

export default function NearbyServices({ hospitalInfo, hotelInfo, policeInfo }) {
  return (
    <div className="ny-card p-6 space-y-4">
      <h3 className="font-bold text-base text-gray-900 flex items-center gap-2">
        <FiPhoneCall className="text-rose-600" /> Nearby Essential Services
      </h3>

      <div className="space-y-3 text-xs">
        <div className="p-3 rounded-xl bg-gray-50 border border-gray-100 flex items-start gap-2.5">
          <FiPhoneCall className="text-emerald-700 mt-0.5 shrink-0" size={15} />
          <div>
            <p className="font-bold text-gray-800">Nearest Hospital / Clinic</p>
            <p className="text-[#102A2E] font-semibold mt-0.5">{hospitalInfo || "Information unavailable"}</p>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-gray-50 border border-gray-100 flex items-start gap-2.5">
          <FiHome className="text-emerald-700 mt-0.5 shrink-0" size={15} />
          <div>
            <p className="font-bold text-gray-800">Nearest Hotel / Lodge</p>
            <p className="text-[#102A2E] font-semibold mt-0.5">{hotelInfo || "Information unavailable"}</p>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-gray-50 border border-gray-100 flex items-start gap-2.5">
          <FiShield className="text-emerald-700 mt-0.5 shrink-0" size={15} />
          <div>
            <p className="font-bold text-gray-800">Tourist Police Station</p>
            <p className="text-[#102A2E] font-semibold mt-0.5">{policeInfo || "Information unavailable"}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
