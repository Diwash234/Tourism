import { useState, useRef, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiSend, FiCompass, FiShield, FiDollarSign, FiPhoneCall, FiSun,
  FiMapPin, FiImage, FiNavigation, FiArrowRight, FiGlobe, FiKey
} from "react-icons/fi"
import { Link } from "react-router-dom"
import chatbotApi from "./api/chatbotApi"
import useGeolocation from "./hooks/useGeolocation"

const QUICK_COMMANDS = [
  { label: "🏔️ Top Places", prompt: "Show top places to visit in Nepal with pictures" },
  { label: "💰 7-Day Budget", prompt: "Estimate budget for 7 days in Pokhara and Kathmandu" },
  { label: "🖼️ View Photos", prompt: "Show me beautiful pictures of Everest and Annapurna" },
  { label: "🚗 Route Guide", prompt: "How do I travel from Kathmandu to Pokhara?" },
  { label: "🚨 Emergency Hub", prompt: "What are the 24/7 tourist police and hospital numbers?" },
  { label: "🌤️ Best Season", prompt: "When is the best time of year to visit Nepal?" },
]

const PLACE_CARD_DB = {
  "pokhara": {
    name: "Pokhara & Phewa Lake",
    city: "Pokhara, Gandaki",
    image: "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&auto=format&fit=crop&q=80",
    slug: "phewa-lake-tal-barahi",
    rating: "4.9",
    budget: "$40/day",
    tag: "Lakes & Adventure"
  },
  "everest": {
    name: "Everest Base Camp (5,364m)",
    city: "Solukhumbu, Koshi",
    image: "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=800&auto=format&fit=crop&q=80",
    slug: "everest-base-camp-ebc",
    rating: "5.0",
    budget: "$55/day",
    tag: "High Mountain Trek"
  },
  "annapurna": {
    name: "Annapurna Sanctuary (ABC)",
    city: "Kaski, Gandaki",
    image: "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800&auto=format&fit=crop&q=80",
    slug: "annapurna-base-camp-abc-sanctuary",
    rating: "4.9",
    budget: "$45/day",
    tag: "Mountain Amphitheater"
  },
  "kathmandu": {
    name: "Pashupatinath & Boudhanath",
    city: "Kathmandu Valley",
    image: "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=800&auto=format&fit=crop&q=80",
    slug: "pashupatinath-temple",
    rating: "4.8",
    budget: "$35/day",
    tag: "UNESCO World Heritage"
  },
  "chitwan": {
    name: "Chitwan Jungle Safari",
    city: "Sauraha, Chitwan",
    image: "https://images.unsplash.com/photo-1575550959106-5a7defe28b56?w=800&auto=format&fit=crop&q=80",
    slug: "chitwan-national-park-safari",
    rating: "4.8",
    budget: "$50/day",
    tag: "Rhinos & Wildlife"
  },
  "lumbini": {
    name: "Lumbini Sacred Garden",
    city: "Rupandehi, Lumbini",
    image: "https://images.unsplash.com/photo-1565008447742-97f6f38c985c?w=800&auto=format&fit=crop&q=80",
    slug: "lumbini-sacred-garden-maya-devi-temple",
    rating: "4.9",
    budget: "$30/day",
    tag: "Birthplace of Buddha"
  },
  "mustang": {
    name: "Upper Mustang & Lo Manthang",
    city: "Mustang, Gandaki",
    image: "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=800&auto=format&fit=crop&q=80",
    slug: "upper-mustang-lo-manthang",
    rating: "4.9",
    budget: "$90/day",
    tag: "Walled Kingdom"
  }
}

export default function ChatBot() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Namaste! 🙏 Welcome to Himal AI.\n\nI'm your intelligent Nepal Travel Companion with live image search and itinerary generation. Ask me about destinations, budgets, routes, permits, weather, or emergency helplines.",
      cards: [PLACE_CARD_DB.pokhara, PLACE_CARD_DB.everest]
    },
  ])

  const [input, setInput] = useState("")
  const [sending, setSending] = useState(false)
  const [conversationId, setConversationId] = useState(null)

  const { position } = useGeolocation()
  const chatBoxRef = useRef(null)

  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight
    }
  }, [messages])

  const detectRelevantCards = (text) => {
    const q = text.toLowerCase()
    const found = []
    Object.keys(PLACE_CARD_DB).forEach((key) => {
      if (q.includes(key)) {
        found.push(PLACE_CARD_DB[key])
      }
    })
    if (found.length === 0 && (q.includes("place") || q.includes("photo") || q.includes("destination") || q.includes("visit") || q.includes("top"))) {
      return [PLACE_CARD_DB.pokhara, PLACE_CARD_DB.everest, PLACE_CARD_DB.chitwan]
    }
    return found
  }

  const handleSend = async (textToSend = null) => {
    const query = typeof textToSend === "string" ? textToSend : input.trim()
    if (!query || sending) return

    const matchedCards = detectRelevantCards(query)

    const userMessage = {
      role: "user",
      content: query,
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setSending(true)

    try {
      const { data } = await chatbotApi.sendMessage(
        query,
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
            "I'm here to assist with Nepal travel destinations, itineraries, and emergency support!",
          cards: matchedCards,
        },
      ])
    } catch (error) {
      console.error(error)
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "I can help you plan your journey across Nepal, find hotels, calculate budgets, and navigate mountain routes. Ask me anything!",
          cards: matchedCards,
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
    <div className="container-app py-8 animate-fadeIn">
      <div className="max-w-4xl mx-auto space-y-5">
        <div className="text-center">
          <span className="px-3.5 py-1 rounded-full bg-purple-100 text-purple-800 text-xs font-black uppercase tracking-wider">
            AI Travel Companion
          </span>
          <h1 className="text-3xl font-extrabold text-gray-900 mt-2 flex items-center justify-center gap-2">
            🏔️ Himal AI Assistant & Visual Guide
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Grok & Gemini Intelligence • 77 Districts • Photo Galleries • Budget & Road Navigation
          </p>
        </div>

        {/* Quick prompt badges */}
        <div className="flex flex-wrap items-center justify-center gap-2">
          {QUICK_COMMANDS.map((qp, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(qp.prompt)}
              disabled={sending}
              className="text-xs font-bold bg-white text-purple-900 hover:bg-purple-50 border border-purple-200/80 rounded-xl px-3.5 py-2 flex items-center gap-1.5 transition-all shadow-sm hover:border-purple-400"
            >
              {qp.label}
            </button>
          ))}
        </div>

        <div className="card-base h-[640px] flex flex-col overflow-hidden border border-purple-100 shadow-2xl rounded-3xl bg-white">
          <div className="bg-gradient-to-r from-purple-900 via-purple-800 to-rose-700 text-white px-6 py-4 flex items-center justify-between shadow-md">
            <div>
              <h2 className="font-extrabold text-base flex items-center gap-2">
                Himal AI Travel Sentinel 🙏
              </h2>
              <p className="text-xs text-purple-200">
                Connected to Knowledge Engine & Visual Destination Database
              </p>
            </div>
            {position && (
              <span className="text-xs bg-white/20 px-3 py-1 rounded-full flex items-center gap-1 font-semibold">
                <FiMapPin size={12} /> GPS Active
              </span>
            )}
          </div>

          <div
            ref={chatBoxRef}
            className="flex-1 overflow-y-auto p-5 space-y-4 bg-slate-50/70"
          >
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex flex-col ${
                  message.role === "user" ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-5 py-3.5 whitespace-pre-wrap text-sm leading-relaxed shadow-sm ${
                    message.role === "user"
                      ? "bg-purple-700 text-white rounded-br-none"
                      : "bg-white text-gray-800 border border-gray-100 rounded-bl-none shadow"
                  }`}
                >
                  {message.content}
                </div>

                {/* Inline Image & Destination Cards generated in Chat */}
                {message.cards && message.cards.length > 0 && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-[85%] mt-3">
                    {message.cards.map((card, i) => (
                      <div
                        key={i}
                        className="bg-white rounded-2xl overflow-hidden border border-purple-100 shadow-md flex flex-col justify-between hover:shadow-lg transition-shadow"
                      >
                        <div className="h-32 w-full relative overflow-hidden bg-black">
                          <img src={card.image} alt={card.name} className="w-full h-full object-cover" />
                          <span className="absolute top-2 left-2 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur text-amber-300 text-[10px] font-bold">
                            {card.tag}
                          </span>
                        </div>
                        <div className="p-3 space-y-1.5">
                          <div className="flex justify-between items-start">
                            <h4 className="font-bold text-xs text-gray-900 leading-tight">{card.name}</h4>
                            <span className="text-xs text-amber-500 font-bold">★ {card.rating}</span>
                          </div>
                          <p className="text-[10px] text-gray-500">{card.city} · <b>{card.budget}</b></p>
                          <div className="flex gap-1.5 pt-1">
                            <Link
                              to={`/destinations/${card.slug}`}
                              className="flex-1 py-1.5 rounded-lg bg-purple-700 hover:bg-purple-800 text-white text-center text-[10px] font-bold transition-colors"
                            >
                              View Details
                            </Link>
                            <Link
                              to={`/navigation?dest=${encodeURIComponent(card.name)}`}
                              className="px-2.5 py-1.5 rounded-lg bg-amber-400 hover:bg-amber-500 text-gray-950 text-center text-[10px] font-black transition-colors"
                            >
                              Route ➔
                            </Link>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {sending && (
              <div className="flex items-center gap-2 text-xs text-purple-700 font-bold italic">
                <span className="w-2 h-2 rounded-full bg-purple-600 animate-bounce"></span>
                Himal AI is researching and fetching images...
              </div>
            )}
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleSend()
            }}
            className="border-t p-4 flex gap-3 bg-white"
          >
            <textarea
              rows={2}
              value={input}
              disabled={sending}
              placeholder="Ask about Nepal destinations, budgets, trekking routes or say 'show pictures'..."
              className="input-field flex-1 resize-none text-sm"
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />

            <button
              type="submit"
              disabled={sending || !input.trim()}
              className="btn-primary px-6 flex items-center justify-center bg-purple-700 hover:bg-purple-800 transition-colors disabled:opacity-50"
            >
              <FiSend size={18} />
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
