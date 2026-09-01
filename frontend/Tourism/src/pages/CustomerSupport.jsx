import { useState, useEffect, useRef } from "react"
import {
  FiHeadphones, FiMessageSquare, FiSend, FiCheckCircle, FiPhoneCall,
  FiMail, FiHelpCircle, FiShield, FiUser, FiPlus, FiRefreshCw, FiClock, FiCheck, FiAlertCircle
} from "react-icons/fi"
import Breadcrumbs from "../components/common/Breadcrumbs"
import { ResponsiveContainer } from "../components/common/ResponsiveSystem"
import UserFeedbackModal from "../components/user/UserFeedbackModal"
import axiosClient from "../api/axiosClient"
import useToast from "../hooks/useToast"
import useAuth from "../hooks/useAuth"

export default function CustomerSupport() {
  const { showToast } = useToast()
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState("chat") // 'chat', 'himal', 'emergency'
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)

  // Live Chat state
  const [threads, setThreads] = useState([])
  const [selectedThread, setSelectedThread] = useState(null)
  const [loadingThreads, setLoadingThreads] = useState(false)
  const [replyText, setReplyText] = useState("")
  const [sendingReply, setSendingReply] = useState(false)

  // New ticket state inside chat panel
  const [showNewTicketForm, setShowNewTicketForm] = useState(false)
  const [newSubject, setNewSubject] = useState("")
  const [newMessage, setNewMessage] = useState("")
  const [newCategory, setNewCategory] = useState("general")
  const [creatingTicket, setCreatingTicket] = useState(false)

  const chatBottomRef = useRef(null)

  const loadThreads = () => {
    setLoadingThreads(true)
    const url = user?.email ? `/feedback?email=${encodeURIComponent(user.email)}` : "/feedback"
    axiosClient.get(url)
      .then(({ data }) => {
        const list = Array.isArray(data) ? data : []
        setThreads(list)
        if (selectedThread) {
          const updated = list.find((t) => t.id === selectedThread.id)
          if (updated) setSelectedThread(updated)
        } else if (list.length > 0 && !showNewTicketForm) {
          setSelectedThread(list[0])
        }
      })
      .catch(() => setThreads([]))
      .finally(() => setLoadingThreads(false))
  }

  useEffect(() => {
    loadThreads()
  }, [user?.email])

  useEffect(() => {
    if (selectedThread && chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [selectedThread?.messages])

  const handleCreateTicket = async (e) => {
    e.preventDefault()
    if (!newSubject.trim() || !newMessage.trim()) {
      return showToast("Please provide both a subject and a message.", "error")
    }

    setCreatingTicket(true)
    try {
      const resp = await axiosClient.post("/feedback", {
        name: user?.full_name || "",
        email: user?.email || "",
        subject: newSubject,
        message: newMessage,
        category: newCategory,
      })
      showToast("Support ticket created! Admin team will reply shortly.", "success")
      setNewSubject("")
      setNewMessage("")
      setShowNewTicketForm(false)
      loadThreads()
      if (resp.data?.id) {
        setTimeout(() => {
          axiosClient.get(`/feedback?id=${resp.data.id}`).then(({ data }) => {
            if (data?.[0]) setSelectedThread(data[0])
          })
        }, 300)
      }
    } catch {
      showToast("Could not create support ticket.", "error")
    } finally {
      setCreatingTicket(false)
    }
  }

  const handleSendReply = async (e) => {
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
      loadThreads()
    } catch {
      showToast("Failed to send message.", "error")
    } finally {
      setSendingReply(false)
    }
  }

  return (
    <ResponsiveContainer className="py-8 space-y-8 animate-fadeIn">
      <Breadcrumbs items={[
        { label: "Home", to: "/" },
        { label: "Customer Support & Admin Help Desk", to: "/support" }
      ]} />

      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-purple-950 to-slate-900 text-white p-8 sm:p-12 shadow-2xl border border-purple-800/30">
        <div className="relative z-10 max-w-3xl space-y-4">
          <span className="px-3.5 py-1 rounded-full bg-amber-400/20 text-amber-300 text-xs font-bold uppercase tracking-wider border border-amber-400/30">
            24/7 Traveler Help Desk & Admin Support
          </span>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">
            Customer Support & Admin Chat Center
          </h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Direct real-time communication channel with Nepal Yatra Admin and Field Support Staff. Ask questions, report trip issues, or request itinerary assistance.
          </p>
        </div>
      </div>

      {/* Primary Navigation Tabs */}
      <div className="flex border-b border-slate-200">
        <button
          type="button"
          onClick={() => setActiveTab("chat")}
          className={`pb-3 px-5 font-bold text-sm sm:text-base flex items-center gap-2 border-b-2 transition-all ${
            activeTab === "chat" ? "border-purple-600 text-purple-700" : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <FiMessageSquare size={18} /> Support Chat with Admin & Staff
          {threads.length > 0 && (
            <span className="px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 text-xs font-black">
              {threads.length}
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("himal")}
          className={`pb-3 px-5 font-bold text-sm sm:text-base flex items-center gap-2 border-b-2 transition-all ${
            activeTab === "himal" ? "border-purple-600 text-purple-700" : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <FiHeadphones size={18} /> Himal AI Assistant
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("emergency")}
          className={`pb-3 px-5 font-bold text-sm sm:text-base flex items-center gap-2 border-b-2 transition-all ${
            activeTab === "emergency" ? "border-purple-600 text-purple-700" : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <FiPhoneCall size={18} /> Emergency Helplines
        </button>
      </div>

      {/* Tab 1: Live Support Chat (User <-> Admin & Staff) */}
      {activeTab === "chat" && (
        <div className="grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-6 bg-slate-950 border border-slate-800 rounded-3xl p-4 sm:p-6 shadow-2xl text-white min-h-[560px]">
          
          {/* Left Sidebar: Threads List & New Ticket Button */}
          <div className="flex flex-col space-y-3 border-b lg:border-b-0 lg:border-r border-slate-800 pb-4 lg:pb-0 lg:pr-4">
            <div className="flex justify-between items-center">
              <h3 className="font-black text-sm uppercase tracking-wider text-slate-300">Your Support Tickets</h3>
              <button
                type="button"
                onClick={loadThreads}
                className="p-1.5 rounded-lg bg-slate-900 text-slate-400 hover:text-white"
                title="Refresh threads"
              >
                <FiRefreshCw size={14} className={loadingThreads ? "animate-spin" : ""} />
              </button>
            </div>

            <button
              type="button"
              onClick={() => { setShowNewTicketForm(true); setSelectedThread(null); }}
              className="w-full py-2.5 px-4 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs flex items-center justify-center gap-2 shadow transition-all"
            >
              <FiPlus size={16} /> Open New Support Ticket
            </button>

            <div className="flex-1 overflow-y-auto space-y-2 max-h-[460px] pr-1">
              {threads.length === 0 ? (
                <div className="p-6 text-center text-slate-500 text-xs space-y-2">
                  <FiMessageSquare size={24} className="mx-auto text-slate-600" />
                  <p>No support tickets created yet.</p>
                  <p className="text-[11px] text-slate-400">Click "Open New Support Ticket" to chat with Admin & Staff.</p>
                </div>
              ) : (
                threads.map((thread) => {
                  const isSelected = selectedThread?.id === thread.id && !showNewTicketForm
                  return (
                    <button
                      key={thread.id}
                      type="button"
                      onClick={() => { setSelectedThread(thread); setShowNewTicketForm(false); }}
                      className={`w-full text-left p-3.5 rounded-2xl border transition-all text-xs space-y-1 block ${
                        isSelected
                          ? "bg-purple-950/80 border-purple-500/80 text-white shadow-lg"
                          : "bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex justify-between items-center">
                        <b className="text-white text-xs truncate max-w-[190px]">{thread.subject}</b>
                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold uppercase ${
                          thread.status === "replied" ? "bg-emerald-950 text-emerald-300 border border-emerald-800" :
                          thread.status === "in_progress" ? "bg-amber-950 text-amber-300 border border-amber-800" :
                          "bg-slate-800 text-slate-300"
                        }`}>
                          {thread.status}
                        </span>
                      </div>
                      <p className="text-slate-400 text-[11px] line-clamp-1">{thread.message}</p>
                      <div className="flex justify-between text-[10px] text-slate-500 pt-1">
                        <span>{thread.category}</span>
                        <span>{thread.messages?.length || 1} msg(s)</span>
                      </div>
                    </button>
                  )
                })
              )}
            </div>
          </div>

          {/* Right Main Panel: Chat View or New Ticket Form */}
          <div className="flex flex-col min-h-0">
            {showNewTicketForm ? (
              <form onSubmit={handleCreateTicket} className="space-y-4 text-xs max-w-xl">
                <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                  <h3 className="text-lg font-black text-white">Create New Support Ticket</h3>
                  <button
                    type="button"
                    onClick={() => setShowNewTicketForm(false)}
                    className="text-slate-400 hover:text-white font-bold"
                  >
                    Cancel
                  </button>
                </div>

                <div className="space-y-1">
                  <label className="font-bold text-slate-300 block">Support Category</label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-purple-400"
                  >
                    <option value="general">💬 General Traveler Support & Inquiries</option>
                    <option value="trip_planner">🗺️ AI Trip Planner & Itinerary Help</option>
                    <option value="booking">🏨 Hotel & Booking Support</option>
                    <option value="budget">💵 Budget & Expenditure Questions</option>
                    <option value="risk">⚠️ Safety & Transport Alerts</option>
                    <option value="bug_report">🐞 Bug Report / Technical Issue</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="font-bold text-slate-300 block">Subject / Ticket Title *</label>
                  <input
                    type="text"
                    value={newSubject}
                    onChange={(e) => setNewSubject(e.target.value)}
                    placeholder="e.g. Need assistance with Annapurna circuit transport options"
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-purple-400"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-bold text-slate-300 block">Message Details *</label>
                  <textarea
                    rows="6"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Describe your inquiry or request for the Admin and Staff team..."
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-purple-400"
                  />
                </div>

                <div className="flex gap-3 pt-2">
                  <button
                    type="submit"
                    disabled={creatingTicket}
                    className="px-6 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-black flex items-center gap-2 shadow"
                  >
                    <FiSend size={14} /> {creatingTicket ? "Submitting..." : "Send Ticket to Admin & Staff"}
                  </button>
                </div>
              </form>
            ) : selectedThread ? (
              <div className="flex-1 flex flex-col min-h-0 space-y-3">
                {/* Thread Header */}
                <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                  <div>
                    <span className="text-[10px] uppercase font-bold text-purple-400 tracking-wider">
                      Ticket #{selectedThread.id} · {selectedThread.category}
                    </span>
                    <h2 className="text-lg font-black text-white">{selectedThread.subject}</h2>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-1 rounded-full bg-purple-950 text-purple-300 border border-purple-800 text-xs font-mono font-bold uppercase">
                      {selectedThread.status}
                    </span>
                  </div>
                </div>

                {/* Messages Feed */}
                <div className="flex-1 overflow-y-auto space-y-3 p-4 bg-slate-900/60 rounded-2xl border border-slate-800 min-h-[340px] max-h-[440px]">
                  {/* Initial Ticket Creator Post */}
                  <div className="p-4 rounded-2xl bg-amber-950/40 border border-amber-800/40 text-amber-100 text-xs space-y-1">
                    <div className="font-bold flex items-center gap-1.5 text-amber-300 mb-1">
                      <FiUser size={14} /> {selectedThread.name || selectedThread.email || "You"} (Ticket Opener)
                    </div>
                    <p className="leading-relaxed">{selectedThread.message}</p>
                    <span className="text-[10px] text-amber-400/60 block text-right mt-1">
                      {new Date(selectedThread.created_at).toLocaleString()}
                    </span>
                  </div>

                  {/* Thread Replies */}
                  {selectedThread.messages?.map((msg) => {
                    const isAdmin = msg.sender_role === "admin" || (msg.sender && (msg.sender.includes("Admin") || msg.sender.includes("Staff")))
                    return (
                      <div
                        key={msg.id}
                        className={`p-3.5 rounded-2xl max-w-[85%] text-xs space-y-1 shadow-sm ${
                          isAdmin
                            ? "bg-purple-950/90 border border-purple-700/60 text-purple-100 self-start mr-auto"
                            : "bg-emerald-950/90 border border-emerald-700/60 text-emerald-100 self-end ml-auto"
                        }`}
                      >
                        <div className="font-bold text-[11px] flex items-center gap-1.5">
                          {isAdmin ? <FiShield size={14} className="text-purple-300" /> : <FiUser size={14} className="text-emerald-300" />}
                          <span className={isAdmin ? "text-purple-300" : "text-emerald-300"}>
                            {msg.sender}
                          </span>
                        </div>
                        <p className="leading-relaxed text-slate-100">{msg.body}</p>
                        <span className="text-[9px] opacity-60 block text-right">
                          {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                    )
                  })}
                  <div ref={chatBottomRef} />
                </div>

                {/* Input Area */}
                <form onSubmit={handleSendReply} className="flex gap-2 pt-1">
                  <input
                    type="text"
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                    placeholder="Write a message to Admin & Staff support team..."
                    className="flex-1 px-4 py-3 rounded-2xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-purple-400 text-xs"
                  />
                  <button
                    type="submit"
                    disabled={sendingReply || !replyText.trim()}
                    className="px-5 py-3 rounded-2xl bg-purple-600 hover:bg-purple-700 text-white font-black flex items-center gap-2 shadow disabled:opacity-50 text-xs"
                  >
                    <FiSend size={14} /> Send
                  </button>
                </form>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-500 space-y-3">
                <FiMessageSquare size={48} className="text-slate-700" />
                <h3 className="text-lg font-bold text-slate-300">Select a support ticket or create a new one</h3>
                <p className="text-xs text-slate-400 max-w-sm">
                  Our admin team and field staff respond to all traveler inquiries directly in this chat interface.
                </p>
                <button
                  type="button"
                  onClick={() => setShowNewTicketForm(true)}
                  className="py-2.5 px-5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs shadow"
                >
                  Start New Support Conversation
                </button>
              </div>
            )}
          </div>

        </div>
      )}

      {/* Tab 2: Himal AI Assistant */}
      {activeTab === "himal" && (
        <div className="p-8 rounded-3xl bg-white border border-slate-200/80 shadow-sm space-y-6">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-emerald-100 text-emerald-700">
              <FiHeadphones size={28} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">Himal AI 24/7 Virtual Tourism Guide</h2>
              <p className="text-xs text-slate-600">Grounded in 8,522 verified Nepal destinations, hotel datasets, and real-time weather.</p>
            </div>
          </div>
          <div className="p-6 rounded-2xl bg-slate-950 text-white space-y-4">
            <p className="text-sm text-slate-300 leading-relaxed">
              Himal AI can assist you with instant answers about trekking permits, seasonal weather recommendations, regional transport fare estimates, and emergency contacts across all 77 districts.
            </p>
            <a
              href="/chatbot"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-sm shadow"
            >
              <FiSend size={16} /> Open Himal AI Chat Room ➔
            </a>
          </div>
        </div>
      )}

      {/* Tab 3: Emergency Helplines */}
      {activeTab === "emergency" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-3xl bg-amber-50 border border-amber-200 shadow-sm space-y-3">
            <div className="p-3 rounded-2xl bg-amber-200 text-amber-800 w-fit">
              <FiPhoneCall size={24} />
            </div>
            <h3 className="text-lg font-bold text-amber-950">Tourist Police Nepal</h3>
            <p className="text-xs text-amber-800">24/7 Dedicated tourist assistance and security hotline.</p>
            <a href="tel:1144" className="block text-center py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-black text-sm shadow">
              📞 Call 1144
            </a>
          </div>

          <div className="p-6 rounded-3xl bg-rose-50 border border-rose-200 shadow-sm space-y-3">
            <div className="p-3 rounded-2xl bg-rose-200 text-rose-800 w-fit">
              <FiShield size={24} />
            </div>
            <h3 className="text-lg font-bold text-rose-950">Nepal National Police</h3>
            <p className="text-xs text-rose-800">Emergency response for all immediate safety incidents.</p>
            <a href="tel:100" className="block text-center py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-black text-sm shadow">
              📞 Call 100
            </a>
          </div>

          <div className="p-6 rounded-3xl bg-emerald-50 border border-emerald-200 shadow-sm space-y-3">
            <div className="p-3 rounded-2xl bg-emerald-200 text-emerald-800 w-fit">
              <FiCheckCircle size={24} />
            </div>
            <h3 className="text-lg font-bold text-emerald-950">Ambulance & Medical</h3>
            <p className="text-xs text-emerald-800">Medical emergency dispatch service across all provinces.</p>
            <a href="tel:102" className="block text-center py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-black text-sm shadow">
              📞 Call 102
            </a>
          </div>
        </div>
      )}

      <UserFeedbackModal
        isOpen={showFeedbackModal}
        onClose={() => setShowFeedbackModal(false)}
      />
    </ResponsiveContainer>
  )
}
