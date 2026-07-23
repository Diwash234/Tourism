import { useState } from "react"
import { useForm } from "react-hook-form"
import { FiMap, FiTruck, FiUsers, FiCalendar, FiDollarSign, FiPlus, FiTrash2 } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import nepalDestinations from "../data/nepalDestinations"
import { TRAVEL_MODES } from "../utils/constants"
import { formatCurrency } from "../utils/helpers"

const MODE_BASE_COST = { flight: 150, bus: 20, car: 60, train: 30, bike: 15, walking: 0 }

const NOTE_CATEGORIES = ["Hotel", "Transport", "Food", "Activity", "Other"]

const TripPlanner = () => {
  const { register, handleSubmit, watch, setValue } = useForm({
    defaultValues: {
      destinationId: nepalDestinations[0].id,
      days: 5,
      budget: 500,
      travelMode: "bus",
      relatives: 0,
    },
  })
  const [plan, setPlan] = useState(null)
  const [notes, setNotes] = useState([])
  const [noteForm, setNoteForm] = useState({ category: "Hotel", label: "", amount: "" })

  const destinationId = watch("destinationId")
  const travelMode = watch("travelMode")
  const destination = nepalDestinations.find((d) => d.id === destinationId) || nepalDestinations[0]

  const onSubmit = (data) => {
    const travelers = 1 + Number(data.relatives || 0)
    const days = Number(data.days) || 1
    const dailyBase = destination.price / 3
    const transport = (MODE_BASE_COST[data.travelMode] ?? 20) * travelers
    const accommodation = Math.round(dailyBase * travelers * days * 0.5)
    const food = Math.round(dailyBase * travelers * days * 0.3)
    const activities = Math.round(dailyBase * travelers * days * 0.2)
    const estimatedTotal = accommodation + food + transport + activities

    setPlan({
      destination,
      travelers,
      days,
      travelMode: data.travelMode,
      budget: Number(data.budget) || 0,
      accommodation,
      food,
      transport,
      activities,
      estimatedTotal,
      withinBudget: estimatedTotal <= (Number(data.budget) || 0),
    })
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
    <div>
      <PageHeader
        title="Trip Planner"
        subtitle="Choose your destination, trip length, budget, travel mode, and companions to get a suggested plan."
        icon={FiMap}
        theme="cyan"
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <form onSubmit={handleSubmit(onSubmit)} className="card-base p-6 space-y-5">
          <div>
            <label className="text-xs font-medium text-gray-500 flex items-center gap-1 mb-1">
              <FiMap size={14} /> Destination of Choice
            </label>
            <select className="input-field" {...register("destinationId")}>
              {nepalDestinations.map((d) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-gray-500 flex items-center gap-1 mb-1">
                <FiCalendar size={14} /> Days of Trip
              </label>
              <input type="number" min={1} className="input-field" {...register("days")} />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500 flex items-center gap-1 mb-1">
                <FiDollarSign size={14} /> Trip Budget ($)
              </label>
              <input type="number" min={0} className="input-field" {...register("budget")} />
            </div>
          </div>

          <div>
            <label className="text-xs font-medium text-gray-500 flex items-center gap-1 mb-2">
              <FiTruck size={14} /> Way of Traveling
            </label>
            <div className="flex flex-wrap gap-2">
              {TRAVEL_MODES.map((mode) => (
                <button
                  type="button"
                  key={mode.value}
                  onClick={() => setValue("travelMode", mode.value)}
                  className={`text-sm rounded-xl px-3 py-2 border transition ${
                    travelMode === mode.value
                      ? "bg-cyan-500 text-white border-cyan-500"
                      : "border-gray-200 hover:border-cyan-300 text-gray-700"
                  }`}
                >
                  {mode.label}
                </button>
              ))}
            </div>
            <input type="hidden" {...register("travelMode")} />
          </div>

          <div>
            <label className="text-xs font-medium text-gray-500 flex items-center gap-1 mb-1">
              <FiUsers size={14} /> Relatives / Companions Traveling With You
            </label>
            <input type="number" min={0} className="input-field" {...register("relatives")} />
          </div>

          <button type="submit" className="w-full bg-cyan-500 hover:bg-cyan-600 text-white font-semibold px-5 py-2.5 rounded-xl transition">
            Generate Trip Plan
          </button>
        </form>

        <div className="space-y-6">
          {plan ? (
            <div className="card-base overflow-hidden">
              <div className="relative h-36">
                <img src={plan.destination.image} alt={plan.destination.name} className="w-full h-full object-cover" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end p-4">
                  <div className="text-white">
                    <p className="font-bold">{plan.destination.name}</p>
                    <p className="text-xs text-white/80">
                      {plan.days} days · {plan.travelers} traveler{plan.travelers > 1 ? "s" : ""} · {plan.travelMode}
                    </p>
                  </div>
                </div>
              </div>
              <div className="p-5 space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-gray-500">Accommodation</span><span>{formatCurrency(plan.accommodation)}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Food</span><span>{formatCurrency(plan.food)}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Transport</span><span>{formatCurrency(plan.transport)}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Activities</span><span>{formatCurrency(plan.activities)}</span></div>
                <div className="flex justify-between font-semibold pt-2 border-t border-gray-100">
                  <span>Estimated Total</span><span>{formatCurrency(plan.estimatedTotal)}</span>
                </div>
                <p className={`text-xs mt-2 font-medium ${plan.withinBudget ? "text-emerald-600" : "text-red-500"}`}>
                  {plan.withinBudget
                    ? `Within your ${formatCurrency(plan.budget)} budget ✓`
                    : `Over your ${formatCurrency(plan.budget)} budget by ${formatCurrency(plan.estimatedTotal - plan.budget)}`}
                </p>
              </div>
            </div>
          ) : (
            <div className="card-base p-10 text-center text-gray-400">
              Fill in the form to generate a suggested trip plan.
            </div>
          )}

          <div className="card-base p-5">
            <h3 className="font-semibold mb-3">Trip Cost Notepad</h3>
            <p className="text-xs text-gray-500 mb-4">
              Jot down hotel and destination costs you've found yourself — they're added to the total below.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 mb-4">
              <select
                className="input-field sm:col-span-1"
                value={noteForm.category}
                onChange={(e) => setNoteForm({ ...noteForm, category: e.target.value })}
              >
                {NOTE_CATEGORIES.map((c) => <option key={c}>{c}</option>)}
              </select>
              <input
                className="input-field sm:col-span-2"
                placeholder="e.g. Hotel Annapurna View"
                value={noteForm.label}
                onChange={(e) => setNoteForm({ ...noteForm, label: e.target.value })}
              />
              <div className="flex gap-2">
                <input
                  type="number"
                  className="input-field"
                  placeholder="$"
                  value={noteForm.amount}
                  onChange={(e) => setNoteForm({ ...noteForm, amount: e.target.value })}
                />
                <button onClick={addNote} className="bg-cyan-500 hover:bg-cyan-600 text-white p-2.5 rounded-xl shrink-0">
                  <FiPlus />
                </button>
              </div>
            </div>

            {notes.length > 0 && (
              <div className="space-y-2">
                {notes.map((n) => (
                  <div key={n.id} className="flex items-center justify-between text-sm border-b border-gray-50 pb-2">
                    <div>
                      <span className="text-xs text-gray-400">{n.category}</span>
                      <p>{n.label}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="font-medium">{formatCurrency(n.amount)}</span>
                      <button onClick={() => removeNote(n.id)} className="text-gray-400 hover:text-red-500">
                        <FiTrash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}
                <div className="flex justify-between font-semibold text-sm pt-2">
                  <span>Notepad Total</span><span>{formatCurrency(notesTotal)}</span>
                </div>
              </div>
            )}

            {(plan || notes.length > 0) && (
              <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-100">
                <span className="font-semibold">Grand Total</span>
                <span className="text-xl font-bold text-cyan-600">{formatCurrency(grandTotal)}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default TripPlanner