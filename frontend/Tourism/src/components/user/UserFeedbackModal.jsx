import { useState, useEffect, useRef } from "react"
import { FiStar, FiMessageSquare, FiSend, FiX, FiCheckCircle, FiUser, FiShield, FiRefreshCw } from "react-icons/fi"
import axiosClient from "../../api/axiosClient"
import useToast from "../../hooks/useToast"
import useAuth from "../../hooks/useAuth"

export default function UserFeedbackModal({ isOpen, onClose, destination = null }) {
  const { showToast } = useToast()
  const { user } = useAuth()
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
  const [selectedThread, setSelectedThread] = useState(null)
  const [replyText, setReplyText] = useState("")
  const [sendingReply, setSendingReply] = useState(false)
  const [activeTab, setActiveTab] = useState("submit") // 'submit' or 'history'
  const chatBottomRef = useRef(null)

  const loadHistory = () => {
    const url = user?.email ? `/feedback?email=${encodeURIComponent(user.email)}` : "/feedback"
    axiosClient.get(url)
      .then(({ data }) => {
        const list = Array.isArray(data) ? data : []
        setHistory(list)
        if (selectedThread) {
          const updated = list.find((t) => t.id === selectedThread.id)
          if (updated) setSelectedThread(updated)
        }
      })
      .catch(() => setHistory([]))
  }

  useEffect(() => {
    if (isOpen) loadHistory()
  }, [isOpen])

  useEffect(() => {
    if (selectedThread && chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [selectedThread?.messages])

  if (!isOpen) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!subject.trim() || !message.trim()) {
      return showToast("Please provide a subject and feedback message.", "error")
    }

    setSubmitting(true)
    try {
      const resp = await axiosClient.post("/feedback", {
        name: user?.full_name || "",
        email: user?.email || "",
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
      showToast("Support ticket created! Admin team will reply shortly.", "success")
      setSubject("")
      setMessage("")
      setActiveTab("history")
      loadHistory()
      if (resp.data?.id) {
        setTimeout(() => {
          axiosClient.get(`/feedback?id=${resp.data.id}`).then(({ data }) => {
            if (data?.[0]) setSelectedThread(data[0])
          })
        }, 300)
      }
    } catch {
      showToast("Could not submit support ticket.", "error")
    } finally {
      setSubmitting(false)
    }
  }

  const handleSendUserMessage = async (e) => {
    e.preventDefault()
    if (!replyText.trim() || !selectedThread) return

    setSendingReply(true)
    try {
      await axiosClient.post(`/feedback/${selectedThread.id}/message`, {
        email: user?.email || selectedThread.email,
        message: replyText,
      })
      setReplyText("")
      showToast("Message sent to Admin & Staff support team.", "success")
      loadHistory()
    } catch {
      showToast("Failed to send message.", "error")
    } finally {
      setSendingReply(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="bg-slate-950 border border-slate-800 rounded-3xl max-w-2xl w-full p-6 space-y-5 shadow-2xl text-white max-h-[90vh] flex flex-col">
        <div className="flex justify-between items-start border-b border-slate-800 pb-3">
          <div>
            <div className="flex gap-2 mb-1">
              <button
                type="button"
                onClick={() => { setActiveTab("submit"); setSelectedThread(null) }}
                className={`px-3 py-1 rounded-full text-xs font-bold ${activeTab === "submit" ? "bg-amber-400 text-slate-950" : "bg-slate-800 text-slate-300"}`}
              >
                + New Support Ticket
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("history")}
                className={`px-3 py-1 rounded-full text-xs font-bold ${activeTab === "history" ? "bg-amber-400 text-slate-950" : "bg-slate-800 text-slate-300"}`}
              >
                Support Chat History ({history.length})
              </button>
            </div>
            <h3 className="text-xl font-black mt-1">Traveler & Admin Support Desk</h3>
          </div>
          <button type="button" onClick={onClose} className="p-1.5 rounded-full bg-slate-800 text-slate-400 hover:text-white">
            <FiX size={18} />
          </button>
        </div>

        {activeTab === "submit" ? (
          <form onSubmit={handleSubmit} className="space-y-4 text-xs overflow-y-auto pr-1">
            {/* Category */}
            <div className="space-y-1">
              <label className="font-bold text-slate-300 block">Support Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-amber-400"
              >
                <option value="general">💬 General Traveler Support & Question</option>
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
              <label className="font-bold text-slate-300 block">Overall Experience Rating (Optional)</label>
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

            {/* Subject */}
            <div className="space-y-1">
              <label className="font-bold text-slate-300 block">Subject / Ticket Title *</label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="e.g. Help needed with Pokhara circuit itinerary"
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-amber-400"
              />
            </div>

            {/* Message */}
            <div className="space-y-1">
              <label className="font-bold text-slate-300 block">Detailed Message *</label>
              <textarea
                rows="4"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Describe your inquiry or request for the Admin and Staff team..."
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
                <FiSend size={14} /> {submitting ? "Creating Ticket..." : "Start Support Chat"}
              </button>
            </div>
          </form>
        ) : (
          <div className="flex-1 flex flex-col min-h-0 overflow-hidden text-xs">
            {selectedThread ? (
              <div className="flex-1 flex flex-col min-h-0 bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-3">
                <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                  <div>
                    <button
                      type="button"
                      onClick={() => setSelectedThread(null)}
                      className="text-amber-400 hover:underline font-bold text-[11px] block mb-1"
                    >
                      ← Back to All Threads
                    </button>
                    <b className="text-white text-sm">{selectedThread.subject}</b>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 text-[10px] font-mono font-bold uppercase">
                      {selectedThread.status}
                    </span>
                    <button type="button" onClick={loadHistory} className="p-1 rounded bg-slate-800 text-slate-300 hover:text-white" title="Refresh messages">
                      <FiRefreshCw size={12} />
                    </button>
                  </div>
                </div>

                {/* Messages Chat List */}
                <div className="flex-1 overflow-y-auto space-y-3 p-2 bg-slate-950/60 rounded-xl border border-slate-800">
                  <div className="p-3 rounded-2xl bg-amber-950/40 border border-amber-800/40 text-amber-200 text-xs">
                    <div className="font-bold flex items-center gap-1 text-amber-300 mb-1">
                      <FiUser size={12} /> {selectedThread.name || "You"} (Ticket Creator)
                    </div>
                    <p>{selectedThread.message}</p>
                    <span className="text-[10px] text-amber-400/70 mt-1 block">
                      {new Date(selectedThread.created_at).toLocaleString()}
                    </span>
                  </div>

                  {selectedThread.messages?.map((msg) => {
                    const isAdmin = msg.sender_role === "admin" || (msg.sender && msg.sender.includes("Admin"))
                    return (
                      <div
                        key={msg.id}
                        className={`p-3 rounded-2xl max-w-[85%] text-xs space-y-1 ${
                          isAdmin
                            ? "bg-purple-950/80 border border-purple-700/50 text-purple-100 self-start mr-auto"
                            : "bg-emerald-950/80 border border-emerald-700/50 text-emerald-100 self-end ml-auto"
                        }`}
                      >
                        <div className="font-bold text-[11px] flex items-center gap-1">
                          {isAdmin ? <FiShield size={12} className="text-purple-300" /> : <FiUser size={12} className="text-emerald-300" />}
                          <span className={isAdmin ? "text-purple-300" : "text-emerald-300"}>
                            {msg.sender}
                          </span>
                        </div>
                        <p className="leading-relaxed">{msg.body}</p>
                        <span className="text-[9px] opacity-60 block text-right">
                          {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                    )
                  })}
                  <div ref={chatBottomRef} />
                </div>

                {/* Chat Reply Input */}
                <form onSubmit={handleSendUserMessage} className="flex gap-2">
                  <input
                    type="text"
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                    placeholder="Write a message to Admin & Staff support..."
                    className="flex-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-amber-400 text-xs"
                  />
                  <button
                    type="submit"
                    disabled={sendingReply || !replyText.trim()}
                    className="px-4 py-2 rounded-xl bg-amber-400 hover:bg-amber-500 text-slate-950 font-black flex items-center gap-1.5 shadow disabled:opacity-50"
                  >
                    <FiSend size={14} /> Send
                  </button>
                </form>
              </div>
            ) : (
              <div className="space-y-2 overflow-y-auto max-h-[50vh]">
                {history.length === 0 ? (
                  <p className="p-8 text-center text-slate-400">No support tickets submitted yet.</p>
                ) : (
                  history.map((thread) => (
                    <button
                      key={thread.id}
                      type="button"
                      onClick={() => setSelectedThread(thread)}
                      className="w-full text-left p-4 rounded-2xl bg-slate-900 border border-slate-800 hover:border-amber-400/50 transition-all space-y-1 block"
                    >
                      <div className="flex justify-between items-center">
                        <b className="text-white text-sm">{thread.subject}</b>
                        <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 text-[10px] font-mono font-bold uppercase">
                          {thread.status}
                        </span>
                      </div>
                      <p className="text-slate-300 text-xs line-clamp-2">{thread.message}</p>
                      <div className="flex justify-between text-[10px] text-slate-400 mt-2">
                        <span>Category: {thread.category}</span>
                        <span>{thread.messages?.length || 1} message(s)</span>
                      </div>
                    </button>
                  ))
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
