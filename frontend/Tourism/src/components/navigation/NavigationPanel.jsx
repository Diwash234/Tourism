import { FiCompass, FiShield, FiTrendingUp, FiZap } from "react-icons/fi"

export default function NavigationPanel({ speedKmh = 58, bearing = "285° WNW", altitude = 1400, missionName = "Pokhara" }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div className="p-3.5 rounded-2xl bg-black/40 border border-purple-800/60 text-center text-white">
        <p className="text-[10px] text-purple-300 uppercase font-bold">Speed</p>
        <p className="text-xl font-black text-emerald-400 mt-0.5">{speedKmh} <span className="text-xs text-white">KM/H</span></p>
      </div>

      <div className="p-3.5 rounded-2xl bg-black/40 border border-purple-800/60 text-center text-white">
        <p className="text-[10px] text-purple-300 uppercase font-bold">Bearing</p>
        <p className="text-xl font-black text-amber-300 mt-0.5">{bearing}</p>
      </div>

      <div className="p-3.5 rounded-2xl bg-black/40 border border-purple-800/60 text-center text-white">
        <p className="text-[10px] text-purple-300 uppercase font-bold">Altitude</p>
        <p className="text-xl font-black text-cyan-300 mt-0.5">{altitude} <span className="text-xs text-white">M</span></p>
      </div>

      <div className="p-3.5 rounded-2xl bg-black/40 border border-purple-800/60 text-center text-white">
        <p className="text-[10px] text-purple-300 uppercase font-bold">Zone Status</p>
        <p className="text-base font-black text-emerald-300 mt-1 flex items-center justify-center gap-1">
          <FiShield size={14} /> SAFE ZONE
        </p>
      </div>
    </div>
  )
}
