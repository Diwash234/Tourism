import { useState, useRef, useEffect } from "react"
import { FiSend } from "react-icons/fi"
import chatbotApi from "./api/chatbotApi"
import useGeolocation from "./hooks/useGeolocation"

const ChatBot = () => {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "👋 Welcome! I'm your AI Travel Assistant.\n\nAsk me anything about Nepal tourism, destinations, hotels, budgets, transportation, weather, emergency services, or travel safety.",
    },
  ])

  const [input, setInput] = useState("")
  const [sending, setSending] = useState(false)
  const [conversationId, setConversationId] = useState(null)

  const { position } = useGeolocation()
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    })
  }, [messages])

  const handleSend = async (e) => {
    if (e) e.preventDefault()

    const text = input.trim()

    if (!text || sending) return

    const userMessage = {
      role: "user",
      content: text,
    }

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
          content:
            data.reply ||
            "Sorry, I couldn't understand your request.",
        },
      ])
    } catch (error) {
      console.error(error)

      const errorMessage =
        error?.response?.data?.detail ||
        error?.response?.data?.reply ||
        "Sorry, something went wrong while contacting the server."

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: errorMessage,
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
    <div className="container-app py-10">
      <div className="max-w-5xl mx-auto">

        <h1 className="section-title text-center">
          AI Travel Assistant
        </h1>

        <p className="text-center text-gray-500 mb-8">
          Powered by OpenAI • Tourism • Budget Planner • Emergency Assistance
        </p>

        <div className="card-base h-[650px] flex flex-col">

          <div className="bg-primary-500 text-white px-6 py-4 rounded-t-xl">
            <h2 className="font-semibold text-lg">
              Nepal Tourism Assistant
            </h2>
            <p className="text-sm opacity-90">
              Ask me anything about your trip.
            </p>
          </div>

          <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-gray-50">

            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${
                  message.role === "user"
                    ? "justify-end"
                    : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 whitespace-pre-wrap shadow ${
                    message.role === "user"
                      ? "bg-primary-500 text-white"
                      : "bg-white text-gray-800"
                  }`}
                >
                  {message.content}
                </div>
              </div>
            ))}

            {sending && (
              <div className="text-sm text-gray-400">
                AI is typing...
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          <form
            onSubmit={handleSend}
            className="border-t p-4 flex gap-3 bg-white"
          >
            <textarea
              rows={2}
              value={input}
              disabled={sending}
              placeholder="Ask about Nepal..."
              className="input-field flex-1 resize-none"
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />

            <button
              type="submit"
              disabled={sending}
              className="btn-primary px-6"
            >
              <FiSend size={18} />
            </button>
          </form>

        </div>
      </div>
    </div>
  )
}

export default ChatBot
