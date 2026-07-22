import { useState, useRef, useEffect } from "react"
import { FiMessageCircle, FiX, FiSend } from "react-icons/fi"
import chatbotApi from "../api/chatbotApi"

/**
 * Floating chat widget — drop <ChatBot /> once near the bottom of
 * MainLayout.jsx (or DashboardLayout.jsx) so it's available on every page.
 */
const ChatBot = () => {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi! Ask me anything about destinations, budgets, or safety in Nepal." },
  ])
  const [input, setInput] = useState("")
  const [sending, setSending] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, open])

  const handleSend = async (e) => {
    e.preventDefault()
    const text = input.trim()
    if (!text || sending) return

    setMessages((prev) => [...prev, { role: "user", content: text }])
    setInput("")
    setSending(true)

    try {
      const { data } = await chatbotApi.sendMessage(text, conversationId)
      setConversationId(data.conversation_id)
      setMessages((prev) => [...prev, { role: "assistant", content: data.reply }])
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, something went wrong. Please try again." }])
    } finally {
      setSending(false)
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 bg-primary-500 text-white rounded-full p-4 shadow-hover hover:bg-primary-600 z-50"
        aria-label="Open chat assistant"
      >
        <FiMessageCircle size={22} />
      </button>
    )
  }

  return (
    <div className="fixed bottom-6 right-6 w-80 sm:w-96 h-[28rem] card-base flex flex-col shadow-hover z-50">
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <h3 className="font-semibold text-sm">Travel Assistant</h3>
        <button onClick={() => setOpen(false)} aria-label="Close chat">
          <FiX />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`rounded-xl px-3 py-2 text-sm max-w-[80%] ${
                m.role === "user" ? "bg-primary-500 text-white" : "bg-gray-100 text-gray-800"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {sending && <div className="text-xs text-gray-400">Typing...</div>}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} className="flex items-center gap-2 p-3 border-t">
        <input
          className="input-field flex-1"
          placeholder="Ask something..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={sending}
        />
        <button type="submit" className="btn-primary p-2" disabled={sending} aria-label="Send">
          <FiSend size={16} />
        </button>
      </form>
    </div>
  )
}

export default ChatBot