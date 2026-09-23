import { FiArrowUp, FiArrowLeft, FiArrowRight, FiRotateCcw } from "react-icons/fi"

const TURN_ICONS = {
  start: FiArrowUp,
  straight: FiArrowUp,
  left: FiArrowLeft,
  right: FiArrowRight,
}

export default function TurnByTurnNav({ steps = [], currentIdx = 0, onSelectStep }) {
  return (
    <div className="card-base p-5 shadow-lg border border-[#E5E0D5] rounded-3xl space-y-4">
      <div className="flex items-center justify-between border-b pb-3">
        <h3 className="font-bold text-base text-gray-900">Turn-by-Turn Route Guidance</h3>
        <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-100 text-[#1D5146] font-bold">
          {steps.length} Turns
        </span>
      </div>

      <ol className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
        {steps.map((step, idx) => {
          const Icon = TURN_ICONS[step.turn] || FiArrowUp
          const isCurrent = idx === currentIdx
          return (
            <li
              key={idx}
              onClick={() => onSelectStep?.(idx)}
              className={`p-3 rounded-xl cursor-pointer transition-all flex items-start gap-3 border ${
                isCurrent ? "bg-[#F7F8F5] border-purple-400 shadow-sm" : "hover:bg-gray-50 border-gray-100"
              }`}
            >
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold shrink-0 ${
                isCurrent ? "bg-amber-400 text-gray-950" : "bg-gray-100 text-gray-600"
              }`}>
                <Icon size={16} />
              </div>
              <div>
                <p className="text-xs font-bold text-gray-800 leading-snug">{step.instruction}</p>
                <p className="text-[11px] text-gray-400 mt-0.5">{step.distance_km} km</p>
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
