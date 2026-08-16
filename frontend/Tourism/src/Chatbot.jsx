import { useState, useRef, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiSend, FiCompass, FiShield, FiDollarSign, FiPhoneCall, FiSun,
  FiMapPin, FiImage, FiNavigation, FiArrowRight, FiGlobe, FiKey,
  FiCalendar, FiClock, FiCheck, FiTruck, FiExternalLink, FiMaximize2
} from "react-icons/fi"
import { Link } from "react-router-dom"
import chatbotApi from "./api/chatbotApi"
import useGeolocation from "./hooks/useGeolocation"

const QUICK_COMMANDS = [
  { label: "🏔️ Top Places & Photos", prompt: "Show top places to visit in Nepal with pictures" },
  { label: "📏 KTM to Pokhara Distance", prompt: "How far is Pokhara from Kathmandu and what are the bus and drive times?" },
  { label: "🗓️ 7-Day Mustang Trip", prompt: "Plan an 7-day itinerary for Mustang with budget NPR 60,000" },
  { label: "💰 5-Day Annapurna Cost", prompt: "Estimate budget for 5 days in Annapurna and Pokhara" },
  { label: "🖼️ View Everest Photos", prompt: "Show me beautiful photos of Everest Base Camp" },
  { label: "🚨 24/7 Emergency Helplines", prompt: "What are the nearest hospitals and tourist police 1144 numbers?" },
]

export default function ChatBot() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Namaste! 🙏 I am **Himal AI**, your personal Nepal Travel Companion & Intelligent Visual Guide.\n\n" +
        "I can calculate real highway distances, design day-by-day itineraries, estimate travel costs in NPR/USD, and show verified photos from all 77 districts.",
      destination_cards: [
        {
          name: "Pokhara & Phewa Lake",
          city: "Kaski, Gandaki",
          image: "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&auto=format&fit=crop&q=80",
          slug: "phewa-lake-tal-barahi",
          rating: "4.9",
          budget: "NPR 4,500/day",
          altitude: "822m",
          category: "Lakes & Adventure",
        },
        {
          name: "Everest Base Camp (5,364m)",
          city: "Solukhumbu, Koshi",
          image: "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=800&auto=format&fit=crop&q=80",
          slug: "everest-base-camp-ebc",
          rating: "5.0",
          budget: "NPR 7,000/day",
          altitude: "5,364m",
          category: "High Mountain Trek",
        }
      ],
      image_cards: [],
      itinerary_cards: null,
      distance_cards: null,
      emergency_cards: [],
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
  }, [messages, sending])

  const handleSend = async (textToSend = null) => {
    const query = typeof textToSend === "string" ? textToSend : input.trim()
    if (!query || sending) return

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
          content: data.reply || "I'm here to assist with Nepal travel destinations, itineraries, and emergency support!",
          destination_cards: data.destination_cards || [],
          image_cards: data.image_cards || [],
          itinerary_cards: data.itinerary_cards || null,
          distance_cards: data.distance_cards || null,
          emergency_cards: data.emergency_cards || [],
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
          destination_cards: [],
          image_cards: [],
          itinerary_cards: null,
          distance_cards: null,
          emergency_cards: [],
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
          <span className="px-3.5 py-1 rounded-full bg-primary-50 text-primary-800 text-xs font-black uppercase tracking-wider">
            AI Travel Companion
          </span>
          <h1 className="text-3xl font-extrabold text-gray-900 mt-2 flex items-center justify-center gap-2">
            🏔️ Himal AI Assistant & Visual Guide
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Grok & Gemini Intelligence • 77 Districts • Photo Galleries • Highway Distances & Itineraries
          </p>
        </div>

        {/* Quick prompt badges */}
        <div className="flex flex-wrap items-center justify-center gap-2">
          {QUICK_COMMANDS.map((qp, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(qp.prompt)}
              disabled={sending}
              className="text-xs font-bold bg-white text-primary-900 hover:bg-primary-50 border border-primary-200/80 rounded-xl px-3.5 py-2 flex items-center gap-1.5 transition-all shadow-sm hover:border-primary-400"
            >
              {qp.label}
            </button>
          ))}
        </div>

        <div className="card-base h-[680px] flex flex-col overflow-hidden border border-primary-100 shadow-2xl rounded-3xl bg-white">
          <div className="bg-gradient-to-r from-primary-800 via-primary-700 to-secondary-700 text-white px-6 py-4 flex items-center justify-between shadow-md">
            <div>
              <h2 className="font-extrabold text-base flex items-center gap-2">
                Himal AI Travel Sentinel 🙏
              </h2>
              <p className="text-xs text-primary-100">
                Connected to Knowledge Engine, Road Corridors & Visual Media Database
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
                      ? "bg-primary-600 text-white rounded-br-none"
                      : "bg-white text-gray-800 border border-gray-100 rounded-bl-none shadow"
                  }`}
                >
                  {message.content}
                </div>

                {/* 1. Distance & Transit Route Card */}
                {message.distance_cards && (
                  <div className="max-w-[85%] mt-3 w-full bg-gradient-to-br from-primary-900 via-stone-900 to-stone-950 text-white p-4 rounded-2xl border border-primary-700 shadow-lg space-y-3">
                    <div className="flex justify-between items-center border-b border-primary-700/60 pb-2">
                      <h4 className="font-extrabold text-xs text-amber-300 flex items-center gap-1.5">
                        <FiTruck /> {message.distance_cards.origin} ➔ {message.distance_cards.destination}
                      </h4>
                      <span className="px-2 py-0.5 rounded bg-amber-400 text-gray-950 text-[10px] font-black">
                        Road Transit Route
                      </span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
                      <div className="bg-primary-900/40 p-2 rounded-xl border border-primary-800">
                        <span className="text-primary-200">Road Distance:</span>
                        <p className="font-black text-white text-xs mt-0.5">{message.distance_cards.road_distance_km} km</p>
                      </div>
                      <div className="bg-primary-900/40 p-2 rounded-xl border border-primary-800">
                        <span className="text-primary-200">Driving Time:</span>
                        <p className="font-black text-amber-300 text-xs mt-0.5">{message.distance_cards.estimated_drive_time}</p>
                      </div>
                      <div className="bg-primary-900/40 p-2 rounded-xl border border-primary-800">
                        <span className="text-primary-200">Public Bus:</span>
                        <p className="font-black text-emerald-300 text-xs mt-0.5">~NPR {message.distance_cards.fare_bus_npr?.toLocaleString()}</p>
                      </div>
                      <div className="bg-primary-900/40 p-2 rounded-xl border border-primary-800">
                        <span className="text-primary-200">Private Jeep:</span>
                        <p className="font-black text-cyan-300 text-xs mt-0.5">~NPR {message.distance_cards.fare_jeep_npr?.toLocaleString()}</p>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-1 text-[10px] text-primary-100">
                      <span>Corridor: <b>{message.distance_cards.highway_corridor}</b></span>
                      <Link
                        to={`/navigation?origin=${encodeURIComponent(message.distance_cards.origin)}&dest=${encodeURIComponent(message.distance_cards.destination)}`}
                        className="px-3 py-1 rounded-lg bg-amber-400 hover:bg-amber-500 text-gray-950 font-black flex items-center gap-1 shadow"
                      >
                        Open Navigation HUD ➔
                      </Link>
                    </div>
                  </div>
                )}

                {/* 2. Structured Itinerary Card */}
                {message.itinerary_cards && message.itinerary_cards.schedule && (
                  <div className="max-w-[85%] mt-3 w-full bg-white p-4 rounded-2xl border border-primary-100 shadow-lg space-y-3">
                    <div className="flex justify-between items-center border-b border-gray-100 pb-2">
                      <div>
                        <h4 className="font-bold text-xs text-primary-900 flex items-center gap-1.5">
                          <FiCalendar /> {message.itinerary_cards.days_count}-Day Plan: {message.itinerary_cards.destination}
                        </h4>
                        <p className="text-[10px] text-gray-500">
                          Total Budget: <b>NPR {message.itinerary_cards.total_estimated_npr?.toLocaleString()}</b> (~${message.itinerary_cards.total_estimated_usd} USD)
                        </p>
                      </div>
                      <Link
                        to="/itinerary"
                        className="px-3 py-1 rounded-lg bg-primary-600 hover:bg-primary-700 text-white text-[10px] font-bold"
                      >
                        Customize Itinerary ➔
                      </Link>
                    </div>

                    <div className="space-y-1.5">
                      {message.itinerary_cards.schedule.map((item, idx) => (
                        <div key={idx} className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 text-[11px]">
                          <div className="flex justify-between font-bold text-gray-900">
                            <span>{item.title}</span>
                            <span className="text-primary-700 font-mono">NPR {item.daily_budget_npr?.toLocaleString()}</span>
                          </div>
                          <p className="text-[10px] text-gray-600 mt-0.5">{item.highlights}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 3. Verified Photo Gallery Cards */}
                {message.image_cards && message.image_cards.length > 0 && (
                  <div className="max-w-[85%] mt-3 w-full space-y-1.5">
                    <p className="text-[11px] font-bold text-primary-900 flex items-center gap-1">
                      <FiImage /> Verified Photos & Attribution Credits:
                    </p>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                      {message.image_cards.map((img, i) => (
                        <div key={i} className="rounded-xl overflow-hidden border border-primary-100 bg-white shadow-sm flex flex-col justify-between">
                          <div className="h-24 w-full relative bg-slate-900 overflow-hidden">
                            <img src={img.url} alt={img.caption} className="w-full h-full object-cover hover:scale-105 transition-transform" />
                            <span className="absolute bottom-1 left-1 px-1.5 py-0.5 rounded bg-black/70 text-amber-300 text-[9px] font-bold">
                              {img.category}
                            </span>
                          </div>
                          <div className="p-1.5 text-[9px] text-gray-500">
                            <p className="font-bold text-gray-800 truncate">{img.caption}</p>
                            <p className="text-[8px] text-emerald-600 truncate">✓ {img.license} ({img.photographer})</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 4. Destination Cards */}
                {message.destination_cards && message.destination_cards.length > 0 && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-[85%] mt-3">
                    {message.destination_cards.map((card, i) => (
                      <div
                        key={i}
                        className="bg-white rounded-2xl overflow-hidden border border-primary-100 shadow-md flex flex-col justify-between hover:shadow-lg transition-shadow"
                      >
                        <div className="h-32 w-full relative overflow-hidden bg-black">
                          <img src={card.image} alt={card.name} className="w-full h-full object-cover" />
                          <span className="absolute top-2 left-2 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur text-amber-300 text-[10px] font-bold">
                            {card.category}
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
                              className="flex-1 py-1.5 rounded-lg bg-primary-600 hover:bg-primary-700 text-white text-center text-[10px] font-bold transition-colors"
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

                {/* 5. Emergency Helplines Cards */}
                {message.emergency_cards && message.emergency_cards.length > 0 && (
                  <div className="max-w-[85%] mt-3 w-full bg-rose-50 border border-rose-200 p-3.5 rounded-2xl space-y-2">
                    <p className="text-xs font-bold text-rose-800 flex items-center gap-1.5">
                      <FiShield /> 24/7 Verified Emergency Contacts (1-Click Call):
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {message.emergency_cards.map((em, i) => (
                        <div key={i} className="p-2 bg-white rounded-xl border border-rose-100 flex justify-between items-center text-xs">
                          <div>
                            <p className="font-bold text-gray-900 truncate">{em.name}</p>
                            <span className="text-[10px] text-gray-500">{em.type} ({em.district})</span>
                          </div>
                          <a
                            href={`tel:${em.phone}`}
                            className="px-2.5 py-1 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-bold text-[11px] flex items-center gap-1 shadow"
                          >
                            <FiPhoneCall size={10} /> Call {em.phone}
                          </a>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}

            {sending && (
              <div className="flex items-center gap-2 text-xs text-primary-700 font-bold italic">
                <span className="w-2 h-2 rounded-full bg-primary-600 animate-bounce"></span>
                Himal AI is researching knowledge engine, routes, and verified images...
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
              placeholder="Ask about Nepal destinations, distance between cities, 5-day itineraries, or say 'show photos'..."
              className="input-field flex-1 resize-none text-sm"
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />

            <button
              type="submit"
              disabled={sending || !input.trim()}
              className="btn-primary px-6 flex items-center justify-center bg-primary-600 hover:bg-primary-700 transition-colors disabled:opacity-50"
            >
              <FiSend size={18} />
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
