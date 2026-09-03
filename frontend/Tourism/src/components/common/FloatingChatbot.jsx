import { useState, useRef, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { FiMessageSquare, FiX, FiSend, FiMinimize2, FiMaximize2 } from "react-icons/fi"
import chatbotApi from "../../api/chatbotApi"
import useGeolocation from "../../hooks/useGeolocation"
import useToast from "../../hooks/useToast"
import HimalPackageCards from "../chat/HimalPackageCards"

const FloatingChatbot = () => {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Namaste! 🙏 I am Himal AI, your Nepal Travel Assistant. Ask me about destinations, treks, budgets, routes, hotels, or emergency services!",
    },
  ])
  const [input, setInput] = useState("")
  const [sending, setSending] = useState(false)
  const [conversationId, setConversationId] = useState(null)

  const { position } = useGeolocation()
  const { showToast } = useToast()
  const chatScrollRef = useRef(null)

  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight
    }
  }, [messages, isOpen])

  const handleSend = async (e) => {
    if (e) e.preventDefault()
    const text = input.trim()
    if (!text || sending) return

    const userMessage = { role: "user", content: text }
    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setSending(true)

    try {
      const { data } = await chatbotApi.sendMessage(
        text,
        position?.lat,
        position?.lng,
        conversationId
      )

      if (data.conversation_id) {
        setConversationId(data.conversation_id)
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.reply || "I am here to help you explore Nepal!",
          package_cards: data.package_cards || [],
          emergency_cards: data.emergency_cards || [],
        },
      ])
    } catch (error) {
      console.error("Chat error:", error)
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            error?.response?.data?.detail ||
            "I can assist you with Nepal destinations, budgets, hotels, and emergency info. What would you like to know?",
        },
      ])
    } finally {
      setSending(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="fixed bottom-6 right-6 z-50" data-testid="himal-float">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 30, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 30, scale: 0.9 }}
            data-testid="himal-float-panel"
            className="card-base w-[360px] sm:w-[400px] h-[520px] shadow-2xl flex flex-col overflow-hidden border border-[#E5E0D5] mb-3 bg-white"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-800 via-purple-700 to-rose-700 text-white px-4 py-3 flex items-center justify-between shadow-md">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-sm font-bold">
                  🏔️
                </div>
                <div>
                  <h3 className="font-semibold text-sm">Himal AI Assistant</h3>
                  <span className="text-[11px] text-green-300 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
                    Online & Ready
                  </span>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 hover:bg-white/20 rounded-lg transition-colors text-white"
              >
                <FiX size={18} />
              </button>
            </div>

            {/* Message List */}
            <div
              ref={chatScrollRef}
              className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50 text-sm"
            >
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 whitespace-pre-wrap shadow-sm text-xs sm:text-sm ${
                      m.role === "user"
                        ? "bg-[#102A2E] text-white rounded-br-none"
                        : "bg-white text-gray-800 border border-gray-100 rounded-bl-none"
                    }`}
                  >
                    {m.content}
                    <HimalPackageCards
                      offers={m.package_cards}
                      onAdd={() => showToast("Added to trip basket", "success")}
                    />
                  </div>
                </div>
              ))}
              {sending && (
                <div className="text-xs text-emerald-700 font-medium italic flex items-center gap-1.5">
                  <span className="inline-block w-2 h-2 rounded-full bg-emerald-600 animate-bounce"></span>
                  Himal AI is thinking...
                </div>
              )}
            </div>

            {/* Input Bar */}
            <form onSubmit={handleSend} className="p-2.5 bg-white border-t border-gray-100 flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about Nepal places, budgets..."
                data-testid="himal-float-input"
                className="input-field py-2 text-xs flex-1"
                disabled={sending}
              />
              <button
                type="submit"
                disabled={sending || !input.trim()}
                data-testid="himal-float-send"
                className="bg-[#102A2E] hover:bg-[#1D5146] text-white px-3.5 rounded-xl flex items-center justify-center transition-colors disabled:opacity-50"
              >
                <FiSend size={15} />
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating Launcher Button */}
      <motion.button
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(!isOpen)}
        className="w-14 h-14 rounded-full bg-gradient-to-r from-purple-700 to-rose-600 text-white shadow-xl flex items-center justify-center hover:shadow-2xl transition-shadow relative"
      >
        <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-amber-400 border-2 border-white flex items-center justify-center text-[9px] font-bold text-gray-900">
          !
        </span>
        {isOpen ? <FiX size={22} /> : <FiMessageSquare size={22} />}
      </motion.button>
    </div>
  )
}

export default FloatingChatbot
