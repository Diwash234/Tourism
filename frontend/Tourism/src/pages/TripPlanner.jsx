import { useState, useCallback, useMemo, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiPlus, FiTrash2, FiEdit3, FiDownload, FiShare2, FiMapPin,
  FiDollarSign, FiCalendar, FiUsers, FiClock, FiGripVertical,
  FiChevronUp, FiChevronDown, FiCopy, FiCheck, FiX, FiNavigation,
} from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import useToast from "../hooks/useToast"
import useAuth from "../hooks/useAuth"

// ─── Budget Calculator ───────────────────────────────────────────────────────
const BudgetCalculator = ({ itinerary, onUpdate }) => {
  const [budget, setBudget] = useState({
    accommodation: 5000,
    food: 3000,
    transport: 2000,
    activities: 4000,
    misc: 1000,
  })

  const total = useMemo(() => Object.values(budget).reduce((a, b) => a + b, 0), [budget])
  const days = itinerary.length || 1
  const perDay = Math.round(total / days)

  const handleChange = (key, value) => {
    const newBudget = { ...budget, [key]: Number(value) || 0 }
    setBudget(newBudget)
    onUpdate?.(newBudget)
  }

  const categories = [
    { key: "accommodation", label: "Accommodation", icon: FiMapPin, color: "#1B8A5A" },
    { key: "food", label: "Food & Dining", icon: FiDollarSign, color: "#F59E0B" },
    { key: "transport", label: "Transport", icon: FiNavigation, color: "#0B3D91" },
    { key: "activities", label: "Activities", icon: FiCalendar, color: "#DC143C" },
    { key: "misc", label: "Miscellaneous", icon: FiDollarSign, color: "#70B1AB" },
  ]

  return (
    <div className="card-base p-5">
      <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <FiDollarSign size={18} className="text-emerald-600" />
        Budget Calculator
      </h3>
      <div className="space-y-3">
        {categories.map((cat) => {
          const Icon = cat.icon
          return (
            <div key={cat.key} className="flex items-center gap-3">
              <div className="p-2 rounded-lg" style={{ backgroundColor: `${cat.color}15`, color: cat.color }}>
                <Icon size={16} />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-700">{cat.label}</p>
              </div>
              <input
                type="number"
                value={budget[cat.key]}
                onChange={(e) => handleChange(cat.key, e.target.value)}
                className="input-field w-28 text-right text-sm"
              />
            </div>
          )
        })}
      </div>
      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="flex justify-between items-center">
          <span className="font-medium text-gray-900 dark:text-gray-100">Total Budget</span>
          <span className="text-xl font-bold text-emerald-600">NPR {total.toLocaleString()}</span>
        </div>
        <div className="flex justify-between items-center mt-2 text-sm text-gray-500 dark:text-gray-400">
          <span>Per day ({days} days)</span>
          <span>NPR {perDay.toLocaleString()}</span>
        </div>
      </div>
    </div>
  )
}

// ─── Itinerary Day Card ──────────────────────────────────────────────────────
const DayCard = ({ day, index, onUpdate, onDelete, onMoveUp, onMoveDown, isFirst, isLast }) => {
  const [expanded, setExpanded] = useState(true)
  const [activities, setActivities] = useState(day.activities || [])

  const addActivity = () => {
    const newActivity = {
      id: Date.now(),
      time: "09:00",
      title: "New Activity",
      description: "",
      location: "",
      cost: 0,
    }
    const newActivities = [...activities, newActivity]
    setActivities(newActivities)
    onUpdate?.({ ...day, activities: newActivities })
  }

  const updateActivity = (id, field, value) => {
    const newActivities = activities.map((a) => (a.id === id ? { ...a, [field]: value } : a))
    setActivities(newActivities)
    onUpdate?.({ ...day, activities: newActivities })
  }

  const deleteActivity = (id) => {
    const newActivities = activities.filter((a) => a.id !== id)
    setActivities(newActivities)
    onUpdate?.({ ...day, activities: newActivities })
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="card-base overflow-hidden"
    >
      {/* Day Header */}
      <div className="flex items-center justify-between p-4 bg-gray-50 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className="flex flex-col gap-1">
            <button onClick={onMoveUp} disabled={isFirst} className="p-0.5 hover:bg-gray-200 rounded disabled:opacity-30">
              <FiChevronUp size={14} />
            </button>
            <button onClick={onMoveDown} disabled={isLast} className="p-0.5 hover:bg-gray-200 rounded disabled:opacity-30">
              <FiChevronDown size={14} />
            </button>
          </div>
          <div className="w-10 h-10 bg-emerald-600 text-white rounded-full flex items-center justify-center font-bold">
            {index + 1}
          </div>
          <div>
            <p className="font-medium text-gray-900">Day {index + 1}</p>
            <p className="text-xs text-gray-500">{day.date || "Add date"}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
          >
            {expanded ? <FiChevronUp size={16} /> : <FiChevronDown size={16} />}
          </button>
          <button
            onClick={onDelete}
            className="p-2 hover:bg-red-50 text-red-500 rounded-lg transition-colors"
          >
            <FiTrash2 size={16} />
          </button>
        </div>
      </div>

      {/* Day Content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: "auto" }}
            exit={{ height: 0 }}
            className="overflow-hidden"
          >
            <div className="p-4 space-y-3">
              {activities.map((activity) => (
                <div key={activity.id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
                  <input
                    type="time"
                    value={activity.time}
                    onChange={(e) => updateActivity(activity.id, "time", e.target.value)}
                    className="input-field text-sm py-1 w-24"
                  />
                  <div className="flex-1 space-y-2">
                    <input
                      type="text"
                      value={activity.title}
                      onChange={(e) => updateActivity(activity.id, "title", e.target.value)}
                      placeholder="Activity name"
                      className="input-field text-sm py-1"
                    />
                    <input
                      type="text"
                      value={activity.location}
                      onChange={(e) => updateActivity(activity.id, "location", e.target.value)}
                      placeholder="Location"
                      className="input-field text-sm py-1"
                    />
                  </div>
                  <button
                    onClick={() => deleteActivity(activity.id)}
                    className="p-1.5 hover:bg-red-100 text-red-500 rounded-lg transition-colors"
                  >
                    <FiX size={14} />
                  </button>
                </div>
              ))}
              <button
                onClick={addActivity}
                className="w-full p-3 border-2 border-dashed border-gray-200 rounded-xl text-sm text-gray-500 hover:border-emerald-300 hover:text-emerald-600 transition-colors flex items-center justify-center gap-2"
              >
                <FiPlus size={16} /> Add Activity
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

// ─── Collaborative Editors ───────────────────────────────────────────────────
const Collaborators = ({ collaborators, onInvite }) => {
  const [email, setEmail] = useState("")

  const handleInvite = () => {
    if (email) {
      onInvite?.(email)
      setEmail("")
    }
  }

  return (
    <div className="card-base p-5">
      <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <FiUsers size={18} className="text-emerald-600" />
        Collaborators
      </h3>
      <div className="flex gap-2 mb-4">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter email to invite"
          className="input-field flex-1 text-sm"
        />
        <button onClick={handleInvite} className="btn-primary text-sm">
          Invite
        </button>
      </div>
      <div className="space-y-2">
        {collaborators.map((collab, i) => (
          <div key={i} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center text-xs font-bold">
                {collab.email[0].toUpperCase()}
              </div>
              <span className="text-sm text-gray-700">{collab.email}</span>
            </div>
            <span className="text-xs text-gray-500">{collab.role}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Share Link Component ────────────────────────────────────────────────────
const ShareLink = ({ tripId }) => {
  const [copied, setCopied] = useState(false)
  const { showToast } = useToast()

  const shareUrl = `${window.location.origin}/plans/shared/${tripId}`

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl)
      setCopied(true)
      showToast("Link copied to clipboard!", "success")
      setTimeout(() => setCopied(false), 2000)
    } catch {
      showToast("Failed to copy link", "error")
    }
  }

  return (
    <div className="card-base p-5">
      <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <FiShare2 size={18} className="text-emerald-600" />
        Share Trip
      </h3>
      <div className="flex items-center gap-2">
        <div className="flex-1 flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg border border-gray-200">
          <span className="text-sm text-gray-600 truncate">{shareUrl}</span>
        </div>
        <button
          onClick={handleCopy}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            copied ? "bg-emerald-100 text-emerald-700" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          {copied ? <FiCheck size={16} /> : <FiCopy size={16} />}
        </button>
      </div>
    </div>
  )
}

// ─── Export PDF Button ───────────────────────────────────────────────────────
const ExportPDFButton = ({ itinerary }) => {
  const [exporting, setExporting] = useState(false)
  const { showToast } = useToast()

  const handleExport = async () => {
    setExporting(true)
    // Simulate PDF generation
    await new Promise((resolve) => setTimeout(resolve, 1500))
    setExporting(false)
    showToast("PDF exported successfully!", "success")
  }

  return (
    <button
      onClick={handleExport}
      disabled={exporting}
      className="btn-primary flex items-center gap-2"
    >
      {exporting ? (
        <>
          <Loader size="sm" /> Generating...
        </>
      ) : (
        <>
          <FiDownload size={16} /> Export PDF
        </>
      )}
    </button>
  )
}

// ─── Main Trip Planner Page ──────────────────────────────────────────────────
const TripPlanner = () => {
  const { user } = useAuth()
  const { showToast } = useToast()
  const [loading, setLoading] = useState(false)
  const [tripName, setTripName] = useState("My Nepal Adventure")
  const [itinerary, setItinerary] = useState([
    {
      id: 1,
      date: "2026-10-15",
      activities: [
        { id: 1, time: "09:00", title: "Visit Swayambhunath", location: "Kathmandu", cost: 500 },
        { id: 2, time: "14:00", title: "Explore Thamel", location: "Kathmandu", cost: 1000 },
      ],
    },
    {
      id: 2,
      date: "2026-10-16",
      activities: [
        { id: 3, time: "08:00", title: "Travel to Pokhara", location: "Prithvi Highway", cost: 2000 },
        { id: 4, time: "15:00", title: "Phewa Lake Boating", location: "Pokhara", cost: 800 },
      ],
    },
  ])
  const [collaborators, setCollaborators] = useState([
    { email: "collaborator@example.com", role: "Editor" },
  ])
  const [budget, setBudget] = useState({})

  const addDay = () => {
    const newDay = {
      id: Date.now(),
      date: "",
      activities: [],
    }
    setItinerary([...itinerary, newDay])
  }

  const updateDay = (id, updatedDay) => {
    setItinerary(itinerary.map((d) => (d.id === id ? updatedDay : d)))
  }

  const deleteDay = (id) => {
    setItinerary(itinerary.filter((d) => d.id !== id))
  }

  const moveDay = (index, direction) => {
    const newItinerary = [...itinerary]
    const [removed] = newItinerary.splice(index, 1)
    newItinerary.splice(index + direction, 0, removed)
    setItinerary(newItinerary)
  }

  const handleInvite = (email) => {
    setCollaborators([...collaborators, { email, role: "Editor" }])
    showToast(`Invitation sent to ${email}`, "success")
  }

  return (
    <div className="ny-page mx-auto w-full max-w-6xl space-y-6">
      <PageHeader
        title="Trip Planner"
        subtitle="Plan your perfect Nepal adventure with our interactive itinerary builder."
        icon={FiCalendar}
        actions={
          <div className="flex items-center gap-2">
            <ExportPDFButton itinerary={itinerary} />
          </div>
        }
      />

      {/* Trip Name */}
      <div className="card-base p-5">
        <input
          type="text"
          value={tripName}
          onChange={(e) => setTripName(e.target.value)}
          className="text-2xl font-bold text-gray-900 bg-transparent border-none outline-none w-full"
          placeholder="Name your trip..."
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Itinerary Builder */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Itinerary</h2>
            <button onClick={addDay} className="btn-secondary flex items-center gap-2 text-sm">
              <FiPlus size={16} /> Add Day
            </button>
          </div>

          {itinerary.length === 0 ? (
            <EmptyState
              title="No days added yet"
              subtitle="Start building your itinerary by adding a day."
              icon={FiCalendar}
              action={
                <button onClick={addDay} className="btn-primary mt-4">
                  <FiPlus size={16} /> Add First Day
                </button>
              }
            />
          ) : (
            <AnimatePresence>
              {itinerary.map((day, index) => (
                <DayCard
                  key={day.id}
                  day={day}
                  index={index}
                  onUpdate={(updated) => updateDay(day.id, updated)}
                  onDelete={() => deleteDay(day.id)}
                  onMoveUp={() => moveDay(index, -1)}
                  onMoveDown={() => moveDay(index, 1)}
                  isFirst={index === 0}
                  isLast={index === itinerary.length - 1}
                />
              ))}
            </AnimatePresence>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <BudgetCalculator itinerary={itinerary} onUpdate={setBudget} />
          <Collaborators collaborators={collaborators} onInvite={handleInvite} />
          <ShareLink tripId="demo-trip-123" />
        </div>
      </div>
    </div>
  )
}

export default TripPlanner
