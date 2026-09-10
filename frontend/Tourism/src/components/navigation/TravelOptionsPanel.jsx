import { useEffect, useState } from "react";
import navigationApi from "../../api/navigationApi";

/*
 * Destination → Navigation screen (task-79 §15/§16).
 * "What is the best way for me to get there, how much will it cost, what
 * will I pass on the way, and what do I need to know before I arrive?"
 * Every figure comes from /navigation/travel-options/ — real routing data,
 * recorded DB facts, or the admin fare card; anything missing is shown as
 * unavailable, never invented.
 */

const UNAVAILABLE = "Information unavailable";

const costLabel = (option) => {
  if (!option.cost_npr) return UNAVAILABLE;
  const [lo, hi] = option.cost_npr;
  if (lo === 0 && hi === 0) return "Free";
  return lo === hi ? `Rs. ${lo}` : `Rs. ${lo}–${hi}`;
};

const fmtDuration = (min) => {
  if (min == null) return "—";
  if (min < 60) return `${min} min`;
  return `${Math.floor(min / 60)} hr ${min % 60} min`;
};

export default function TravelOptionsPanel({ originPayload, destinationName, destinationSlug, requestId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [note, setNote] = useState("");

  useEffect(() => {
    let cancelled = false;
    const timer = setTimeout(() => {
      if (!destinationName || !originPayload) {
        setData(null);
        setNote("");
        return;
      }
      setLoading(true);
      setNote("");
      navigationApi
        .getTravelOptions({ ...originPayload, destination_name: destinationName, destination_slug: destinationSlug })
        .then(({ data: payload }) => {
          if (cancelled) return;
          setData(payload);
        })
        .catch((err) => {
          if (!cancelled) {
            setData(null);
            setNote(err.response?.data?.detail || "Travel options unavailable right now.");
          }
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }, 0);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [requestId, destinationName, destinationSlug, originPayload]);

  if (!destinationName) return null;
  if (loading && !data) {
    return (
      <div className="p-3 rounded-2xl bg-slate-900 border border-slate-800 text-xs text-slate-400">
        Comparing ways to get there…
      </div>
    );
  }
  if (!data) {
    return note ? (
      <div className="p-3 rounded-2xl bg-slate-900 border border-slate-800 text-xs text-amber-300">{note}</div>
    ) : null;
  }

  const recommendedOption = data.options.find((option) => option.mode === data.recommended);

  return (
    <div className="space-y-3">
      {/* How do you want to go? */}
      <div className="p-3 rounded-2xl bg-slate-900 border border-slate-800">
        <h3 className="text-xs font-black uppercase tracking-wider text-emerald-400 mb-2">How do you want to go?</h3>
        <div className="space-y-1.5">
          {data.options.map((option) => (
            <div
              key={option.mode}
              className={`flex items-center gap-3 rounded-xl border px-3 py-2 ${
                option.mode === data.recommended
                  ? "border-amber-400/60 bg-amber-400/10"
                  : "border-slate-800 bg-slate-950/60"
              } ${option.available === false ? "opacity-60" : ""}`}
            >
              <span className="text-lg" aria-hidden="true">{option.icon}</span>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-bold text-white flex items-center gap-2">
                  {option.label}
                  {option.mode === data.recommended && (
                    <span className="text-[9px] font-black uppercase tracking-wider bg-amber-400 text-slate-950 rounded-md px-1.5 py-0.5">
                      ⭐ Recommended
                    </span>
                  )}
                </p>
                <p className="text-[10px] text-slate-400 truncate">
                  {fmtDuration(option.duration_min)} · {costLabel(option)}
                  {option.cost_npr && option.cost_npr[0] !== 0 ? ` · ${option.cost_note}` : ""}
                </p>
                {option.note && <p className="text-[10px] text-amber-300/80">{option.note}</p>}
              </div>
              <span className="text-[10px] text-slate-500 text-right shrink-0">{option.distance_km?.toFixed(1)} km</span>
            </div>
          ))}
        </div>
        <p className="mt-2 text-[10px] text-slate-500">
          {data.distance_label}
          {recommendedOption ? ` · Why ${recommendedOption.label.toLowerCase()}? ${data.recommendation_reasons.join(" · ")}` : ""}
        </p>
      </div>

      {/* Turn-by-turn */}
      <div className="p-3 rounded-2xl bg-slate-900 border border-slate-800">
        <h3 className="text-xs font-black uppercase tracking-wider text-emerald-400 mb-2">Route instructions</h3>
        {data.turn_by_turn?.steps?.length ? (
          <ol className="space-y-1">
            {data.turn_by_turn.steps.map((step, idx) => (
              <li key={idx} className="flex gap-2 text-[11px] text-slate-300">
                <span className="text-emerald-400 font-black shrink-0">{idx + 1}.</span>
                <span>
                  {step.instruction}
                  {step.distance_m > 0 && <span className="text-slate-500"> · {step.distance_m} m</span>}
                </span>
              </li>
            ))}
          </ol>
        ) : (
          <p className="text-[11px] text-amber-300">{data.turn_by_turn_note}</p>
        )}
      </div>

      {/* Along your route */}
      {data.along_the_way?.length > 0 && (
        <div className="p-3 rounded-2xl bg-slate-900 border border-slate-800">
          <h3 className="text-xs font-black uppercase tracking-wider text-emerald-400 mb-2">Along your route</h3>
          <ul className="space-y-1">
            {data.along_the_way.map((place) => (
              <li key={place.slug || place.name} className="flex items-center justify-between gap-2 text-[11px] text-slate-300">
                <span className="truncate">📸 {place.name} <span className="text-slate-500">· {place.category}</span></span>
                <span className="text-amber-300 font-bold whitespace-nowrap">+{place.detour_minutes} min detour</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Before you go */}
      {data.before_you_go && data.before_you_go !== UNAVAILABLE && (
        <div className="p-3 rounded-2xl bg-slate-900 border border-slate-800">
          <h3 className="text-xs font-black uppercase tracking-wider text-emerald-400 mb-2">Before you go</h3>
          <ul className="space-y-1 text-[11px] text-slate-300">
            <li>🕐 Opening hours: <b className="text-white">{data.before_you_go.opening_hours}</b></li>
            <li>🎟️ Entry fee: <b className="text-white">{data.before_you_go.entry_fee_npr != null ? `Rs. ${data.before_you_go.entry_fee_npr}` : UNAVAILABLE}</b></li>
            <li>🗓️ Best time: <b className="text-white">{data.before_you_go.best_time_to_visit}</b></li>
          </ul>
        </div>
      )}
    </div>
  );
}
