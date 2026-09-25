import { useState } from "react"
import { FiDollarSign, FiInfo } from "react-icons/fi"

/**
 * Budget input shell. It intentionally does not calculate a price locally;
 * the parent must submit the values to a real estimate endpoint.
 */
export default function CostPrediction({ onCalculate }) {
  const [days, setDays] = useState(7)
  const [travelers, setTravelers] = useState(2)
  const [style, setStyle] = useState("mid")
  const [destination, setDestination] = useState("")

  return (
    <section className="ny-card space-y-5 p-5" aria-labelledby="cost-input-title">
      <div className="flex items-start gap-3 border-b border-[var(--ny-border)] pb-3"><FiDollarSign className="mt-0.5 text-[var(--ny-green)]" aria-hidden="true" /><div><h2 id="cost-input-title" className="text-base font-bold">Trip budget input</h2><p className="text-xs text-[var(--ny-text-secondary)]">Send these details to a recorded estimate service. No price is calculated in this component.</p></div></div>
      <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
        <label>Days<input type="number" min={1} max={60} className="input-field mt-1" value={days} onChange={(event) => setDays(event.target.value)} /></label>
        <label>Travellers<input type="number" min={1} max={20} className="input-field mt-1" value={travelers} onChange={(event) => setTravelers(event.target.value)} /></label>
        <label>Travel style<select className="input-field mt-1" value={style} onChange={(event) => setStyle(event.target.value)}><option value="budget">Budget</option><option value="mid">Mid-range</option><option value="standard">Standard</option><option value="luxury">Luxury</option></select></label>
        <label>Destination<input className="input-field mt-1" value={destination} onChange={(event) => setDestination(event.target.value)} placeholder="Enter a destination" /></label>
      </div>
      <button type="button" disabled={!destination.trim() || !onCalculate} onClick={() => onCalculate?.({ days: Number(days) || null, travelers: Number(travelers) || null, style, destination })} className="ny-btn ny-btn-primary disabled:cursor-not-allowed disabled:opacity-50">Request an estimate</button>
      <p className="flex items-start gap-2 text-xs leading-5 text-[var(--ny-text-secondary)]"><FiInfo size={15} className="mt-0.5 shrink-0 text-[var(--ny-info)]" aria-hidden="true" />If no estimate service is available, the result stays unavailable rather than substituting a sample budget.</p>
    </section>
  )
}
