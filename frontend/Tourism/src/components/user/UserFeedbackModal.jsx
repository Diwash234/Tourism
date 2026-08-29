import { useState, useEffect } from "react"
import { FiStar, FiMessageSquare, FiSend, FiX, FiCheckCircle } from "react-icons/fi"
import axiosClient from "../../api/axiosClient"
import useToast from "../../hooks/useToast"

export default function UserFeedbackModal({ isOpen, onClose, destination = null }) {
  const { showToast } = useToast()
  const [subject, setSubject] = useState("")
  const [message, setMessage] = useState("")
  const [category, setCategory] = useState("recommendation_quality")
  const [rating, setRating] = useState(5)
  const [recRating, setRecRating] = useState(5)
  const [itinRating, setItinRating] = useState(5)
  const [budgetRating, setBudgetRating] = useState(5)
  const [routeRating, setRouteRating] = useState(5)

  const [submitting, setSubmitting] = useState(false)
  const [history, setHistory] = useState([])
  const [activeTab, setActiveTab] = useState("submit") // 'submit' or 'history'

  const loadHistory = () => {
    axiosClient.get("/admin/feedback")
      .then(({ data }) => setHistory(data || []))
      .catch(() => setHistory([]))
  }

  useEffect(() => {
    if (isOpen) loadHistory()
  }, [isOpen])

  if (!isOpen) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!subject.trim() || !message.trim()) {
      return showToast("Please provide a subject and feedback message.", "error")
    }

    setSubmitting(true)
    try {
      await axiosClient.post("/feedback", {
        subject,
        message,
        category,
        rating,
        recommendation_quality_rating: recRating,
        itinerary_quality_rating: itinRating,
        budget_accuracy_rating: budgetRating,
        route_quality_rating: routeRating,
        destination_id: destination?.id || null,
      })
      showToast("Thank you! Your feedback has been sent to the Admin Team.", "success")
      setSubject("")
      setMessage("")
      setActiveTab("history")
      loadHistory()
    } catch {
      showToast("Could not submit feedback.", "error")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="bg-slate-950 border border-slate-800 rounded-3xl max-w-xl w-full p-6 space-y-5 shadow-2xl text-white max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-start border-b border-slate-800 pb-3">
          <div>
            <div className="flex gap-2 mb-1">
              <button
                type="button"
                onClick={() => setActiveTab("submit")}
                className={`px-3 py-1 rounded-full text-xs font-bold ${activeTab === "submit" ? "bg-amber-400 text-slate-950" : "bg-slate-800 text-slate-300"}`}
              >
                Submit Feedback
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("history")}
                className={`px-3 py-1 rounded-full text-xs font-bold ${activeTab === "history" ? "bg-amber-400 text-slate-950" : "bg-slate-800 text-slate-300"}`}
              >
                My Feedback History ({history.length})
              </button>
            </div>
            <h3 className="text-xl font-black mt-1">Traveler Feedback & Quality Desk</h3>
          </div>
          <button type="button" onClick={onClose} className="p-1.5 rounded-full bg-slate-800 text-slate-400 hover:text-white">
            <FiX size={18} />
          </button>
        </div>

        {activeTab === "submit" ? (
          <form onSubmit={handleSubmit} className="space-y-4 text-xs">
            {/* Category */}
            <div className="space-y-1">
              <label className="font-bold text-slate-300 block">Feedback Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-amber-400"
              >
                <option value="recommendation_quality">🎯 Recommendation Quality & Relevance</option>
                <option value="itinerary_quality">🗺️ Itinerary Structure & Schedule</option>
                <option value="budget_accuracy">💵 Budget Accuracy & Prices</option>
                <option value="route_quality">🚗 Route Navigation & Transport</option>
                <option value="bug_report">🐞 Bug Report / Technical Issue</option>
                <option value="suggestion">💡 General Suggestion</option>
              </select>
            </div>

            {/* Overall Rating */}
            <div className="space-y-1">
              <label className="font-bold text-slate-300 block">Overall Experience Rating</label>
              <div className="flex gap-2 items-center">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setRating(star)}
                    className="p-1 text-amber-400 hover:scale-110 transition-transform"
                  >
                    <FiStar size={22} className={rating >= star ? "fill-amber-400" : "text-slate-600"} />
                  </button>
                ))}
                <span className="text-amber-300 font-bold ml-2">{rating} / 5 Stars</span>
              </div>
            </div>

            {/* Detailed Component Ratings */}
            <div className="grid grid-cols-2 gap-3 p-3 rounded-2xl bg-slate-900 border border-slate-800 text-[11px]">
              <div>
                <span className="text-slate-400 block font-bold">Recommendation Quality</span>
                <select value={recRating} onChange={(e) => setRecRating(Number(e.target.value))} className="w-full mt-1 bg-slate-800 p-1.5 rounded-lg text-white">
                  {[5, 4, 3, 2, 1].map((r) => <option key={r} value={r}>{r} Stars</option>)}
                </select>
              </div>
              <div>
                <span className="text-slate-400 block font-bold">Itinerary Quality</span>
                <select value={itinRating} onChange={(e) => setItinRating(Number(e.target.value))} className="w-full mt-1 bg-slate-800 p-1.5 rounded-lg text-white">
                  {[5, 4, 3, 2, 1].map((r) => <option key={r} value={r}>{r} Stars</option>)}
                </select>
              </div>
              <div>
                <span className="text-slate-400 block font-bold">Budget Accuracy</span>
                <select value={budgetRating} onChange={(e) => setBudgetRating(Number(e.target.value))} className="w-full mt-1 bg-slate-800 p-1.5 rounded-lg text-white">
                  {[5, 4, 3, 2, 1].map((r) => <option key={r} value={r}>{r} Stars</option>)}
                </select>
              </div>
              <div>
                <span className="text-slate-400 block font-bold">Route & Navigation</span>
                <select value={routeRating} onChange={(e) => setRouteRating(Number(e.target.value))} className="w-full mt-1 bg-slate-800 p-1.5 rounded-lg text-white">
                  {[5, 4, 3, 2, 1].map((r) => <option key={r} value={r}>{r} Stars</option>)}
                </select>
              </div>
            </div>

            {/* Subject */}
            <div className="space-y-1">
              <label className="font-bold text-slate-300 block">Feedback Subject *</label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="e.g. Great recommendations for Pokhara trekking!"
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-amber-400"
              />
            </div>

            {/* Message */}
            <div className="space-y-1">
              <label className="font-bold text-slate-300 block">Detailed Comments *</label>
              <textarea
                rows="3"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Share your thoughts to help us personalize recommendations..."
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-amber-400"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-5 py-2 rounded-xl bg-amber-400 hover:bg-amber-500 text-slate-950 font-black flex items-center gap-1.5 shadow"
              >
                <FiSend size={14} /> {submitting ? "Sending..." : "Send Feedback"}
              </button>
            </div>
          </form>
        ) : (
          <div className="space-y-3 text-xs">
            {history.length === 0 ? (
              <p className="p-8 text-center text-slate-400">No feedback threads submitted yet.</p>
            ) : (
              <div className="space-y-2 max-h-[50vh] overflow-y-auto">
                {history.map((thread) => (
                  <div key={thread.id} className="p-3.5 rounded-2xl bg-slate-900 border border-slate-800 space-y-1.5">
                    <div className="flex justify-between items-center">
                      <b className="text-white text-sm">{thread.subject}</b>
                      <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 text-[10px] font-mono font-bold uppercase">
                        {thread.status}
                      </span>
                    </div>
                    <p className="text-slate-300">{thread.message}</p>
                    {thread.messages?.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-slate-800 space-y-1">
                        {thread.messages.map((msg) => (
                          <div key={msg.id} className="p-2 rounded-xl bg-slate-800 text-[11px] text-amber-200">
                            <b>Admin Reply:</b> {msg.body}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
