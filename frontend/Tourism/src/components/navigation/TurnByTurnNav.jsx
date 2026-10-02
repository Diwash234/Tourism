import { TurnIcon } from "../../utils/uiIcons"

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
          const isCurrent = idx === currentIdx
          return (
            <li
              key={idx}
              onClick={() => onSelectStep?.(idx)}
              className={`p-3 rounded-xl cursor-pointer transition-all flex items-start gap-3 border ${
                isCurrent ? "bg-[#F7F8F5] border-purple-400 shadow-sm" : "hover:bg-gray-50 border-gray-100"
              }`}
            >
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${
                isCurrent ? "bg-amber-100" : "bg-gray-50"
              }`}>
                <TurnIcon step={step} size={26} />
              </div>
              <div>
                <p className="text-xs font-bold text-gray-800 leading-snug">{step.instruction}</p>
                <p className="text-[11px] text-gray-400 mt-0.5">
                  {step.distance_km != null
                    ? `${step.distance_km} km`
                    : step.distance_m != null
                      ? step.distance_m >= 1000
                        ? `${(step.distance_m / 1000).toFixed(1)} km`
                        : `${Math.round(step.distance_m)} m`
                      : ""}
                </p>
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
