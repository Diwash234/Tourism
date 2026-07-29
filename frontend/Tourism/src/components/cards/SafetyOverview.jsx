import { FiShield, FiCloudRain, FiActivity, FiHeart, FiShield as FiPolice } from "react-icons/fi"

const Stat = ({ icon: Icon, label, value, tone = "text-himalaya-500" }) => (
  <div className="flex items-center gap-3">
    <div className={`p-2 rounded-lg bg-gray-50 ${tone}`}>
      <Icon size={16} />
    </div>
    <div>
      <p className="text-xs text-gray-400">{label}</p>
      <p className="font-semibold text-dark text-sm">{value}</p>
    </div>
  </div>
)

/**
 * SafetyOverview
 * props: { score, weatherStatus, earthquakeRisk, hospitalsNearby, policeNearby }
 */
const SafetyOverview = ({
  score = 0,
  weatherStatus = "Good",
  earthquakeRisk = "Low",
  hospitalsNearby = 0,
  policeNearby = 0,
}) => {
  return (
    <div className="card-base p-6">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-xl bg-forest-50 text-forest-500">
            <FiShield size={20} />
          </div>
          <h3 className="font-bold text-dark">Nepal Safety Score</h3>
        </div>
        <span className="text-3xl font-extrabold text-forest-600">{score}%</span>
      </div>

      <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden mb-6">
        <div
          className="h-full rounded-full bg-gradient-to-r from-forest-500 to-himalaya-500 transition-all duration-700"
          style={{ width: `${score}%` }}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Stat icon={FiCloudRain} label="Weather" value={weatherStatus} tone="text-himalaya-500" />
        <Stat icon={FiActivity} label="Earthquake Risk" value={earthquakeRisk} tone="text-saffron-500" />
        <Stat icon={FiHeart} label="Hospitals Nearby" value={hospitalsNearby} tone="text-nepalred-500" />
        <Stat icon={FiPolice} label="Police" value={policeNearby} tone="text-himalaya-500" />
      </div>
    </div>
  )
}

export default SafetyOverview