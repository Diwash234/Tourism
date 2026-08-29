import { useState } from "react"
import { useForm } from "react-hook-form"
import {
  FiMap, FiTruck, FiUsers, FiCalendar, FiDollarSign, FiPlus, FiTrash2,
  FiCompass, FiSliders, FiSun, FiCoffee, FiZap, FiShield, FiCheckCircle,
  FiAperture, FiDroplet, FiWind, FiCamera, FiLayers, FiRefreshCw
} from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import nepalDestinations from "../data/nepalDestinations"
import { TRAVEL_MODES } from "../utils/constants"
import { formatCurrency } from "../utils/helpers"
import axiosClient from "../api/axiosClient"
import useToast from "../hooks/useToast"

const MODE_BASE_COST = { flight: 150, bus: 20, car: 60, train: 30, bike: 15, walking: 0 }
const NOTE_CATEGORIES = ["Hotel", "Transport", "Food", "Activity", "Other"]

const INTEREST_CHIPS = [
  { id: "mountains", label: "🏔️ Mountains" },
  { id: "trekking", label: "🥾 Trekking" },
  { id: "adventure", label: "⚡ Adventure" },
  { id: "culture", label: "🏛️ Culture & Heritage" },
  { id: "nature", label: "🌿 Nature" },
  { id: "wildlife", label: "🦏 Wildlife" },
  { id: "spiritual", label: "🧘 Spiritual" },
  { id: "food", label: "🍲 Local Cuisine" },
  { id: "photography", label: "📷 Photography" },
  { id: "relaxation", label: "☕ Relaxation" },
]

export default function TripPlanner() {
  const { showToast } = useToast()
  const { register, handleSubmit, watch, setValue } = useForm({
    defaultValues: {
      destinationId: nepalDestinations[0].id,
      origin: "Kathmandu",
      days: 5,
      budget: 500,
      travelMode: "bus",
      groupType: "solo",
      travelers: 1,
      travelStyle: "comfortable",
      pace: "balanced",
    },
  })

  const [selectedInterests, setSelectedInterests] = useState(["culture", "mountains"])
  const [plan, setPlan] = useState(null)
  const [modifying, setModifying] = useState(false)

  const [notes, setNotes] = useState([])
  const [noteForm, setNoteForm] = useState({ category: "Hotel", label: "", amount: "" })

  const destinationId = watch("destinationId")
  const travelMode = watch("travelMode")
  const groupType = watch("groupType")
  const travelStyle = watch("travelStyle")
  const pace = watch("pace")

  const destination = nepalDestinations.find((d) => d.id === destinationId) || nepalDestinations[0]

  const toggleInterest = (id) => {
    setSelectedInterests((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    )
  }

  const onSubmit = async (data) => {
    const travelers = Math.max(1, Number(data.travelers || 1))
    const days = Number(data.days) || 1
    const dailyBase = destination.price / 3

    const styleMultiplier = { backpacker: 0.6, budget: 0.8, comfortable: 1.0, premium: 1.5, luxury: 2.2 }[data.travelStyle] || 1.0
    const transport = Math.round((MODE_BASE_COST[data.travelMode] ?? 20) * travelers)
    const accommodation = Math.round(dailyBase * travelers * days * 0.5 * styleMultiplier)
    const food = Math.round(dailyBase * travelers * days * 0.3 * styleMultiplier)
    const activities = Math.round(dailyBase * travelers * days * 0.2 * styleMultiplier)
    const estimatedTotal = accommodation + food + transport + activities

    const dayItinerary = Array.from({ length: days }).map((_, i) => ({
      day: i + 1,
      theme: i === 0 ? "Arrival & Local Sightseeing" : i === days - 1 ? "Cultural Farewell & Souvenirs" : `Day ${i + 1} Scenic & Heritage Exploration`,
      daily_budget_npr: Math.round((estimatedTotal / days) * 132),
      destinations: [{ name: destination.name, city: destination.name }],
    }))

    setPlan({
      destination,
      origin: data.origin || "Kathmandu",
      travelers,
      days,
      travelMode: data.travelMode,
      groupType: data.groupType,
      travelStyle: data.travelStyle,
      pace: data.pace,
      budget: Number(data.budget) || 0,
      accommodation,
      food,
      transport,
      activities,
      estimatedTotal,
      withinBudget: estimatedTotal <= (Number(data.budget) || 0),
      itinerary: dayItinerary,
      interests: selectedInterests,
    })
  }

  const handleApplyAIModification = async (action) => {
    if (!plan) return
    setModifying(true)
    try {
      const { data } = await axiosClient.post("/ml/itinerary/modify/", {
        action,
        itinerary_data: plan,
      })
      setPlan((prev) => ({
        ...prev,
        itinerary: data.itinerary || prev.itinerary,
        modificationNote: data.modification_note,
      }))
      showToast(data.modification_note || `AI modification applied: ${action}`, "success")
    } catch {
      showToast("Could not modify itinerary.", "error")
    } finally {
      setModifying(false)
    }
  }

  const addNote = () => {
    if (!noteForm.label || !noteForm.amount) return
    setNotes((prev) => [...prev, { id: Date.now(), ...noteForm, amount: Number(noteForm.amount) }])
    setNoteForm({ category: "Hotel", label: "", amount: "" })
  }

  const removeNote = (id) => setNotes((prev) => prev.filter((n) => n.id !== id))
  const notesTotal = notes.reduce((sum, n) => sum + n.amount, 0)
  const grandTotal = (plan?.estimatedTotal || 0) + notesTotal

  return (
    <div className="container-app py-8 space-y-8 animate-fadeIn">
      <PageHeader
        title="Intelligent Trip Planner"
        subtitle="Configure your origin, trip duration, budget, travel style, and interests to generate a structured itinerary."
        icon={FiMap}
        theme="cyan"
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        {/* Planner Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="card-base p-6 space-y-6 bg-white border border-slate-200">
          {/* 1. Destination & Origin */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-bold text-slate-700 flex items-center gap-1 mb-1">
                <FiMap size={14} className="text-emerald-600" /> Target Destination
              </label>
              <select className="input-field bg-white" {...register("destinationId")}>
                {nepalDestinations.map((d) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 flex items-center gap-1 mb-1">
                <FiCompass size={14} className="text-emerald-600" /> Starting Origin
              </label>
              <input
                type="text"
                placeholder="e.g. Pokhara, Kathmandu, Airport"
                className="input-field bg-white"
                {...register("origin")}
              />
            </div>
          </div>

          {/* 2. Duration, Budget & Travelers */}
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-xs font-bold text-slate-700 flex items-center gap-1 mb-1">
                <FiCalendar size={14} /> Days
              </label>
              <input type="number" min={1} max={30} className="input-field bg-white" {...register("days")} />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 flex items-center gap-1 mb-1">
                <FiDollarSign size={14} /> Budget ($)
              </label>
              <input type="number" min={0} className="input-field bg-white" {...register("budget")} />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 flex items-center gap-1 mb-1">
                <FiUsers size={14} /> Travelers
              </label>
              <input type="number" min={1} max={20} className="input-field bg-white" {...register("travelers")} />
            </div>
          </div>

          {/* 3. Group Type, Travel Style & Pace */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Group Type</label>
              <select className="input-field bg-white text-xs" {...register("groupType")}>
                <option value="solo">Solo Traveler</option>
                <option value="couple">Couple</option>
                <option value="family">Family</option>
                <option value="friends">Friends</option>
                <option value="group">Group</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Travel Style</label>
              <select className="input-field bg-white text-xs" {...register("travelStyle")}>
                <option value="backpacker">Backpacker</option>
                <option value="budget">Budget</option>
                <option value="comfortable">Comfortable</option>
                <option value="premium">Premium</option>
                <option value="luxury">Luxury</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Trip Pace</label>
              <select className="input-field bg-white text-xs" {...register("pace")}>
                <option value="relaxed">Relaxed & Unhurried</option>
                <option value="balanced">Balanced Sightseeing</option>
                <option value="fast">Fast-Paced Explorer</option>
              </select>
            </div>
          </div>

          {/* Places Visited & Places to Avoid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div>
              <label className="font-bold text-slate-700 block mb-1">Places Already Visited (Optional)</label>
              <input
                type="text"
                placeholder="e.g., Kathmandu Durbar, Nagarkot"
                className="input-field bg-white"
                {...register("visitedPlaces")}
              />
            </div>

            <div>
              <label className="font-bold text-slate-700 block mb-1">Places / Cities to Avoid (Optional)</label>
              <input
                type="text"
                placeholder="e.g., Crowded city centers, high altitude > 4000m"
                className="input-field bg-white"
                {...register("avoidPlaces")}
              />
            </div>
          </div>

          {/* 4. Travel Mode */}
          <div>
            <label className="text-xs font-bold text-slate-700 flex items-center gap-1 mb-2">
              <FiTruck size={14} /> Transport Preference
            </label>
            <div className="flex flex-wrap gap-2">
              {TRAVEL_MODES.map((mode) => (
                <button
                  type="button"
                  key={mode.value}
                  onClick={() => setValue("travelMode", mode.value)}
                  className={`text-xs font-bold rounded-xl px-3 py-2 border transition ${
                    travelMode === mode.value
                      ? "bg-slate-900 text-white border-slate-900"
                      : "bg-slate-50 border-slate-200 hover:border-slate-300 text-slate-700"
                  }`}
                >
                  {mode.label}
                </button>
              ))}
            </div>
          </div>

          {/* 5. Travel Interests Chips */}
          <div>
            <label className="text-xs font-bold text-slate-700 block mb-2">Travel Interests & Experiences</label>
            <div className="flex flex-wrap gap-1.5">
              {INTEREST_CHIPS.map((chip) => {
                const isSel = selectedInterests.includes(chip.id)
                return (
                  <button
                    type="button"
                    key={chip.id}
                    onClick={() => toggleInterest(chip.id)}
                    className={`px-3 py-1.5 rounded-full text-xs font-bold border transition-all ${
                      isSel ? "bg-amber-400 text-slate-950 border-amber-400 shadow-sm" : "bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100"
                    }`}
                  >
                    {chip.label}
                  </button>
                )
              })}
            </div>
          </div>

          <button
            type="submit"
            className="w-full py-3.5 rounded-2xl bg-gradient-to-r from-amber-400 via-amber-300 to-amber-500 text-slate-950 font-black text-sm shadow-xl shadow-amber-400/20 hover:scale-[1.01] transition-all"
          >
            Generate Trip Plan
          </button>
        </form>

        {/* Results & AI Refinement Column */}
        <div className="space-y-6">
          {plan ? (
            <div className="card-base overflow-hidden bg-white border border-slate-200 shadow-lg space-y-4">
              <div className="relative h-40">
                <img src={plan.destination.image} alt={plan.destination.name} className="w-full h-full object-cover" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent flex items-end p-4">
                  <div className="text-white space-y-0.5">
                    <span className="px-2.5 py-0.5 rounded-full bg-emerald-500 text-slate-950 text-[10px] font-black uppercase">
                      From {plan.origin}
                    </span>
                    <p className="font-black text-xl">{plan.destination.name}</p>
                    <p className="text-xs text-slate-200">
                      {plan.days} days · {plan.travelers} traveler{plan.travelers > 1 ? "s" : ""} · {plan.travelStyle} ({plan.groupType})
                    </p>
                  </div>
                </div>
              </div>

              {/* AI Modification Actions Bar */}
              <div className="p-4 bg-slate-50 border-y border-slate-100 space-y-2">
                <div className="flex justify-between items-center text-xs font-bold text-slate-800">
                  <span className="flex items-center gap-1.5"><FiSliders className="text-amber-500" /> AI Itinerary Refinement</span>
                  {modifying && <span className="text-emerald-600 animate-pulse">Modifying plan...</span>}
                </div>
                <div className="flex flex-wrap gap-1.5 text-xs">
                  <button
                    disabled={modifying}
                    onClick={() => handleApplyAIModification("cheaper")}
                    className="px-2.5 py-1 rounded-xl bg-white border border-slate-200 hover:border-emerald-500 text-slate-800 font-bold"
                  >
                    💵 Make it cheaper
                  </button>
                  <button
                    disabled={modifying}
                    onClick={() => handleApplyAIModification("luxurious")}
                    className="px-2.5 py-1 rounded-xl bg-white border border-slate-200 hover:border-purple-500 text-slate-800 font-bold"
                  >
                    💎 Make it luxurious
                  </button>
                  <button
                    disabled={modifying}
                    onClick={() => handleApplyAIModification("more_culture")}
                    className="px-2.5 py-1 rounded-xl bg-white border border-slate-200 hover:border-amber-500 text-slate-800 font-bold"
                  >
                    🏛️ Add more culture
                  </button>
                  <button
                    disabled={modifying}
                    onClick={() => handleApplyAIModification("more_nature")}
                    className="px-2.5 py-1 rounded-xl bg-white border border-slate-200 hover:border-teal-500 text-slate-800 font-bold"
                  >
                    🌿 Add hidden nature
                  </button>
                  <button
                    disabled={modifying}
                    onClick={() => handleApplyAIModification("slower_pace")}
                    className="px-2.5 py-1 rounded-xl bg-white border border-slate-200 hover:border-blue-500 text-slate-800 font-bold"
                  >
                    ☕ Slow down pace
                  </button>
                  <button
                    disabled={modifying}
                    onClick={() => handleApplyAIModification("replan")}
                    className="px-2.5 py-1 rounded-xl bg-amber-100 hover:bg-amber-200 border border-amber-300 text-amber-900 font-bold"
                  >
                    🌦️ Weather / Impact Replan
                  </button>
                </div>
                {plan.modificationNote && (
                  <p className="text-[11px] text-emerald-700 font-bold bg-emerald-50 p-2 rounded-xl border border-emerald-200 mt-1">
                    ✓ {plan.modificationNote}
                  </p>
                )}
              </div>

              {/* Expense Breakdown */}
              <div className="p-5 space-y-2 text-xs text-slate-700">
                <div className="flex justify-between"><span className="text-slate-500">Accommodation</span><span className="font-bold">{formatCurrency(plan.accommodation)}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Food & Dining</span><span className="font-bold">{formatCurrency(plan.food)}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Transit ({plan.travelMode})</span><span className="font-bold">{formatCurrency(plan.transport)}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Activities & Permits</span><span className="font-bold">{formatCurrency(plan.activities)}</span></div>
                <div className="flex justify-between font-black text-sm pt-2 border-t border-slate-100 text-slate-900">
                  <span>Estimated Total</span><span>{formatCurrency(plan.estimatedTotal)}</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="card-base p-10 text-center text-slate-400 bg-white border border-slate-200">
              Configure your preferences and click "Generate Trip Plan" to view your customized Nepal itinerary.
            </div>
          )}

          {/* Trip Cost Notepad */}
          <div className="card-base p-5 bg-white border border-slate-200 space-y-4">
            <div>
              <h3 className="font-bold text-sm text-slate-900">Trip Cost Notepad</h3>
              <p className="text-xs text-slate-500">Add custom lodge rates or local flight quotes to your trip budget total.</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-2">
              <select
                className="input-field bg-white text-xs sm:col-span-1"
                value={noteForm.category}
                onChange={(e) => setNoteForm({ ...noteForm, category: e.target.value })}
              >
                {NOTE_CATEGORIES.map((c) => <option key={c}>{c}</option>)}
              </select>
              <input
                className="input-field bg-white text-xs sm:col-span-2"
                placeholder="e.g. Annapurna View Hotel"
                value={noteForm.label}
                onChange={(e) => setNoteForm({ ...noteForm, label: e.target.value })}
              />
              <div className="flex gap-2">
                <input
                  type="number"
                  className="input-field bg-white text-xs"
                  placeholder="$"
                  value={noteForm.amount}
                  onChange={(e) => setNoteForm({ ...noteForm, amount: e.target.value })}
                />
                <button onClick={addNote} className="bg-purple-700 hover:bg-purple-800 text-white p-2.5 rounded-xl shrink-0">
                  <FiPlus />
                </button>
              </div>
            </div>

            {notes.length > 0 && (
              <div className="space-y-2 text-xs">
                {notes.map((n) => (
                  <div key={n.id} className="flex items-center justify-between border-b border-slate-100 pb-2">
                    <div>
                      <span className="text-[10px] text-slate-400 font-bold uppercase">{n.category}</span>
                      <p className="font-bold text-slate-800">{n.label}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-slate-900">{formatCurrency(n.amount)}</span>
                      <button onClick={() => removeNote(n.id)} className="text-slate-400 hover:text-rose-600">
                        <FiTrash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}
                <div className="flex justify-between font-bold text-xs pt-2">
                  <span>Notepad Total</span><span>{formatCurrency(notesTotal)}</span>
                </div>
              </div>
            )}

            {(plan || notes.length > 0) && (
              <div className="flex justify-between items-center mt-4 pt-3 border-t border-slate-200">
                <span className="font-bold text-sm text-slate-900">Grand Total</span>
                <span className="text-xl font-black text-purple-700">{formatCurrency(grandTotal)}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
