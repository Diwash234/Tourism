import { useState, useRef, useEffect } from "react"
import { useLocation } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import { FiMessageSquare, FiX, FiSend } from "react-icons/fi"
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
        "Namaste! I am Himal AI, your Nepal travel assistant. I can help you discover recorded places, compare published packages and plan a route. Missing details stay unavailable.",
    },
  ])
  const [input, setInput] = useState("")
  const [sending, setSending] = useState(false)
  const [conversationId, setConversationId] = useState(null)

  const { position } = useGeolocation({ auto: false })
  const { showToast } = useToast()
  const location = useLocation()
  const chatScrollRef = useRef(null)

  useEffect(() => {
    if (typeof window === "undefined") return undefined
    window.dispatchEvent(new CustomEvent("ny-chat-toggle", { detail: { open: isOpen } }))
    return () => window.dispatchEvent(new CustomEvent("ny-chat-toggle", { detail: { open: false } }))
  }, [isOpen])

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
            "I couldn't reach the travel service just now. Please try again or browse the destination catalogue.",
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

  // The full-page assistant already owns the conversation on /chatbot.
  if (location.pathname === "/chatbot") return null

  return (
    <div className="ny-floating-chat fixed" data-testid="himal-float">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 30, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 30, scale: 0.9 }}
            id="himal-float-panel"
            data-testid="himal-float-panel"
            role="dialog"
            aria-label="Nepal Yatra travel assistant"
            className="ny-card mb-3 flex max-h-[min(520px,calc(100dvh-8rem))] w-[min(360px,calc(100vw-1.5rem))] flex-col overflow-hidden bg-white shadow-[var(--ny-shadow-elevated)] sm:w-[400px]"
          >
            {/* Header */}
            <div className="flex items-center justify-between bg-[var(--ny-green-dark)] px-4 py-3 text-white shadow-sm">
              <div className="flex items-center gap-2">
                <div className="grid h-8 w-8 place-items-center rounded-full bg-white/15">
                  <FiMessageSquare size={16} aria-hidden="true" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm">Nepal Yatra assistant</h3>
                  <span className="text-[11px] text-[#BDEBD9]">Travel questions, clearly answered</span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="grid h-11 w-11 place-items-center rounded-[var(--ny-radius-sm)] text-white transition-colors hover:bg-white/15"
                aria-label="Close travel assistant"
              >
                <FiX size={18} />
              </button>
            </div>

            {/* Message List */}
            <div
              ref={chatScrollRef}
              className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50 text-sm"
              aria-live="polite"
              aria-relevant="additions text"
            >
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 whitespace-pre-wrap shadow-sm text-xs sm:text-sm ${
                      m.role === "user"
                        ? "bg-[var(--ny-green-dark)] text-white rounded-br-none"
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
                  The assistant is working…
                </div>
              )}
            </div>

            {/* Input Bar */}
            <form onSubmit={handleSend} className="p-2.5 bg-white border-t border-gray-100 flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                aria-label="Ask the Nepal Yatra assistant"
                placeholder="Ask about Nepal places, budgets..."
                data-testid="himal-float-input"
                className="input-field py-2 text-xs flex-1"
                disabled={sending}
              />
              <button
                type="submit"
                disabled={sending || !input.trim()}
                data-testid="himal-float-send"
                aria-label="Send message to the travel assistant"
                className="ny-btn ny-btn-primary min-h-11 min-w-11 px-3"
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
        type="button"
        aria-label={isOpen ? "Close Nepal Yatra assistant" : "Open Nepal Yatra assistant"}
        aria-expanded={isOpen}
        aria-controls="himal-float-panel"
        onClick={() => setIsOpen(!isOpen)}
        className="relative grid h-14 w-14 place-items-center rounded-full bg-[var(--ny-green)] text-white shadow-[var(--ny-shadow-elevated)] transition hover:bg-[var(--ny-green-dark)]"
      >
        <span className="absolute -right-1 -top-1 grid h-5 w-5 place-items-center rounded-full border-2 border-white bg-[var(--ny-gold)] text-xs font-bold text-[var(--ny-green-deepest)]" aria-hidden="true">
          !
        </span>
        {isOpen ? <FiX size={22} /> : <FiMessageSquare size={22} />}
      </motion.button>
    </div>
  )
}

export default FloatingChatbot
