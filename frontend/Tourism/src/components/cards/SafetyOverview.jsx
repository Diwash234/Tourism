import { FiShield, FiCloudRain, FiActivity, FiHeart, FiShield as FiPolice, FiCheckCircle } from "react-icons/fi"

const Stat = ({ icon: Icon, label, value, tone = "text-emerald-600 bg-emerald-50" }) => (
  <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100 flex items-center gap-3">
    <div className={`p-2.5 rounded-xl ${tone}`}>
      <Icon size={18} />
    </div>
    <div>
      <p className="text-[11px] text-gray-500 font-bold uppercase tracking-wider">{label}</p>
      <p className="font-extrabold text-slate-900 text-sm mt-0.5">{value}</p>
    </div>
  </div>
)

const SafetyOverview = ({
  score = 92,
  weatherStatus = "Clear / Safe Highlands",
  earthquakeRisk = "Low Seismic Risk",
  hospitalsNearby = 8,
  policeNearby = 12,
}) => {
  const displayScore = score || 92
  const isHigh = displayScore >= 80

  return (
    <div className="card-base p-6 sm:p-8 bg-white border border-slate-200 shadow-xl rounded-3xl space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-emerald-100 text-emerald-800 shadow-sm">
            <FiShield size={26} />
          </div>
          <div>
            <span className="text-[10px] font-black uppercase text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
              Live Regional Safety Sentinel
            </span>
            <h3 className="font-black text-xl text-slate-900 mt-1">Nepal Travel Safety Index</h3>
            <p className="text-xs text-slate-500 mt-0.5">Real-time composite score based on weather, seismic alerts, and verified emergency facilities.</p>
          </div>
        </div>

        <div className="flex items-center gap-3 bg-emerald-50 border border-emerald-200 p-4 rounded-2xl self-start sm:self-auto">
          <div className="text-right">
            <span className="text-[10px] text-emerald-800 font-black uppercase tracking-wider block">Safety Score</span>
            <span className="text-3xl font-black text-emerald-700 font-mono">{displayScore}%</span>
          </div>
          <span className="px-2.5 py-1 rounded-xl bg-emerald-700 text-white font-black text-xs uppercase shadow">
            {isHigh ? "Safe Zone" : "Advisory"}
          </span>
        </div>
      </div>

      {/* Progress Indicator Bar */}
      <div className="space-y-2">
        <div className="flex justify-between items-center text-xs font-bold text-slate-600">
          <span>Overall Safety Coverage</span>
          <span className="text-emerald-700 font-black flex items-center gap-1">
            <FiCheckCircle size={14} /> Normal Condition
          </span>
        </div>
        <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden p-0.5 border border-slate-200">
          <div
            className="h-full rounded-full bg-gradient-to-r from-emerald-500 via-teal-400 to-emerald-600 transition-all duration-700 shadow"
            style={{ width: `${displayScore}%` }}
          />
        </div>
      </div>

      {/* 4 Itemized Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2">
        <Stat icon={FiCloudRain} label="Weather Radar" value={weatherStatus} tone="text-blue-700 bg-blue-100" />
        <Stat icon={FiActivity} label="Seismic Risk" value={earthquakeRisk} tone="text-amber-700 bg-amber-100" />
        <Stat icon={FiHeart} label="Hospitals Nearby" value={`${hospitalsNearby} Facilities`} tone="text-rose-700 bg-rose-100" />
        <Stat icon={FiPolice} label="Police Hotlines" value={`${policeNearby} Active Posts`} tone="text-[#102A2E] bg-emerald-100" />
      </div>
    </div>
  )
}

export default SafetyOverview
