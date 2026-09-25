import { useState, useRef, useEffect } from "react"
import PageHeader from "./components/common/PageHeader"
import CMSPageIntro from "./components/cms/CMSPageIntro"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiSend, FiCompass, FiShield, FiDollarSign, FiPhoneCall, FiSun,
  FiMapPin, FiImage, FiNavigation, FiArrowRight, FiGlobe, FiKey,
  FiCalendar, FiClock, FiCheck, FiTruck, FiExternalLink, FiMaximize2,
  FiMessageCircle,
} from "react-icons/fi"
import { Link } from "react-router-dom"
import chatbotApi from "./api/chatbotApi"
import destinationApi from "./api/destinationApi"
import useGeolocation from "./hooks/useGeolocation"
import useChatSocket from "./hooks/useChatSocket"
import useToast from "./hooks/useToast"
import HimalPackageCards from "./components/chat/HimalPackageCards"
import { NOT_RECORDED, recordedCity } from "./utils/placeUtils"
import PlaceholderImage from "./components/common/PlaceholderImage"

const QUICK_COMMANDS = [
  { label: "Recorded destinations", prompt: "Show recorded destinations in Nepal" },
  { label: "Emergency directory", prompt: "Help me find recorded emergency services near a destination" },
  { label: "Travel packages", prompt: "What travel packages can I add to a trip?" },
  { label: "Plan a five-day trip", prompt: "Help me plan a five-day trip to Nepal" },
]

export default function ChatBot() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Namaste! I am Himal AI, your Nepal travel companion.\n\n" +
        "I can help you discover recorded destinations, published packages and practical trip information. Missing fields stay unavailable.",
      destination_cards: [],
      image_cards: [],
      itinerary_cards: null,
      distance_cards: null,
      emergency_cards: [],
    },
  ])

  const { showToast } = useToast()
  const [input, setInput] = useState("")
  const [sending, setSending] = useState(false)
  const [conversationId, setConversationId] = useState(null)

  // Live sync across tabs/devices over WebSocket (master spec §30); the
  // REST POST stays canonical and socket events dedupe by message id.
  const seenChatIds = useRef(new Set())
  useChatSocket(conversationId, (event) => {
    if (event.message_id == null || seenChatIds.current.has(event.message_id)) return
    seenChatIds.current.add(event.message_id)
    if (event.type === "bot_reply") {
      setMessages((prev) => [...prev, {
        role: "assistant",
        content: event.reply || "",
        destination_cards: event.destination_cards || [],
        image_cards: event.image_cards || [],
        itinerary_cards: event.itinerary_cards || null,
        distance_cards: event.distance_cards || null,
        emergency_cards: event.emergency_cards || [],
        package_cards: event.package_cards || [],
      }])
    } else if (event.type === "user_message") {
      setMessages((prev) => {
        const last = prev[prev.length - 1]
        if (last?.role === "user" && last.content === event.content) return prev
        return [...prev, { role: "user", content: event.content }]
      })
    }
  })

  const { position, locating, retry: requestLocation } = useGeolocation({ auto: false })
  const chatBoxRef = useRef(null)

  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight
    }
  }, [messages, sending])

  useEffect(() => {
    destinationApi.getDestinations({ featured: true, page_size: 4, limit: 4 })
      .then(({ data }) => {
        const dests = data.results || data || []
        const cards = (Array.isArray(dests) ? dests : []).filter((row) => row?.name).slice(0, 2).map((dest) => ({
          name: dest.name,
          city: recordedCity(dest) || dest.district || NOT_RECORDED,
          image: dest.cover_image_url || "",
          slug: dest.slug,
          rating: dest.average_rating != null ? dest.average_rating : NOT_RECORDED,
          budget: dest.entry_fee ? `NPR ${dest.entry_fee}` : NOT_RECORDED,
          altitude: dest.altitude || NOT_RECORDED,
          category: dest.category_name || dest.type || "Destination",
        }))
        if (!cards.length) return
        setMessages((prev) => {
          if (!prev.length || prev[0].role !== "assistant") return prev
          return [{ ...prev[0], destination_cards: cards }, ...prev.slice(1)]
        })
      })
      .catch(() => {})
  }, [])

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
      if (data.message_id != null) seenChatIds.current.add(data.message_id)

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
          package_cards: data.package_cards || [],
        },
      ])
    } catch (error) {
      console.error(error)
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "I couldn't reach the travel service just now. Please try again, or browse the destination catalogue while the service is unavailable.",
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
    <div className="ny-page container-app space-y-6 py-6 sm:py-8" data-testid="himal-page">
      <CMSPageIntro pageKey="chatbot" />
      <div className="mx-auto w-full max-w-6xl space-y-5">
        <div className="text-center">
          <span className="ny-kicker !border !border-[var(--ny-border)] !bg-[var(--ny-soft-green)] !text-[var(--ny-green)]">
            AI Travel Companion
          </span>
          <PageHeader title="Himal AI Assistant & Visual Guide" subtitle="Ask about destinations, safety, permits and more." icon={FiMessageCircle} />
          <p className="text-gray-500 text-sm mt-1">
            Recorded destinations, published packages and practical trip information
          </p>
          <div className="mt-3 flex flex-wrap items-center justify-center gap-2 bg-slate-100 border border-slate-200 text-slate-700 text-xs font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-500 opacity-70" />
            <span>Recorded data first: I use available catalogue records and clearly mark missing details.</span><button type="button" onClick={requestLocation} disabled={locating} className="ny-btn ny-btn-secondary min-h-11 text-xs"><FiMapPin size={14} aria-hidden="true" />{position ? "Location shared" : locating ? "Finding location…" : "Use my location"}</button>
          </div>
        </div>

        {/* Quick prompt grid — one card per suggestion, prompt preview included */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full max-w-3xl mx-auto">
          {QUICK_COMMANDS.map((qp, idx) => (
            <button
              key={idx}
              type="button"
              data-testid={qp.prompt.includes("five-day") ? "himal-quick-budget" : `himal-quick-${idx}`}
              onClick={() => handleSend(qp.prompt)}
              disabled={sending}
              className="ny-card min-h-11 px-4 py-3 text-left"
            >
              <span className="block text-xs font-bold text-primary-900">{qp.label}</span>
              <span className="block text-[11px] text-gray-500 mt-0.5 line-clamp-1">{qp.prompt}</span>
            </button>
          ))}
        </div>

        <div className="card-base flex min-h-[320px] flex-col overflow-hidden rounded-[var(--ny-radius-lg)] border border-[var(--ny-border)] bg-white shadow-[var(--ny-shadow-elevated)]" style={{ height: "min(680px, calc(100dvh - 8rem))" }}>
          <div className="flex items-center justify-between bg-[var(--ny-green-dark)] px-5 py-4 text-white shadow-sm sm:px-6">
            <div>
              <h2 className="font-extrabold text-base flex items-center gap-2">
                Himal AI travel assistant
              </h2>
              <p className="text-xs text-primary-100">
                Available catalogue and route tools
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
                        <span className="text-primary-200">Fare index:</span>
                        <p className="font-black text-emerald-300 text-xs mt-0.5">{message.distance_cards.fare_bus_npr != null ? `NPR ${message.distance_cards.fare_bus_npr.toLocaleString()}` : "Unavailable"}</p>
                      </div>
                      <div className="bg-primary-900/40 p-2 rounded-xl border border-primary-800">
                        <span className="text-primary-200">4WD fare index:</span>
                        <p className="font-black text-cyan-300 text-xs mt-0.5">{message.distance_cards.fare_jeep_npr != null ? `NPR ${message.distance_cards.fare_jeep_npr.toLocaleString()}` : "Unavailable"}</p>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-1 text-[10px] text-primary-100">
                      <span>{message.distance_cards.fare_note ? <b>{message.distance_cards.fare_note}</b> : "Fare unavailable unless a recorded route value is supplied."}</span>
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
                          Planning estimate: <b>{message.itinerary_cards.total_estimated_npr != null ? `NPR ${message.itinerary_cards.total_estimated_npr.toLocaleString()}` : "Information unavailable"}</b>
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
                            <span className="text-primary-700 font-mono">{item.daily_budget_npr != null ? `NPR ${item.daily_budget_npr.toLocaleString()} (estimate)` : "Budget unavailable"}</span>
                          </div>
                          <p className="text-[10px] text-gray-600 mt-0.5">{item.highlights}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 3. Recorded photo gallery cards */}
                {message.image_cards && message.image_cards.length > 0 && (
                  <div className="max-w-[85%] mt-3 w-full space-y-1.5">
                    <p className="text-[11px] font-bold text-primary-900 flex items-center gap-1">
                      <FiImage /> Recorded photos & attribution:
                    </p>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                      {message.image_cards.map((img, i) => (
                        <div key={i} className="rounded-xl overflow-hidden border border-primary-100 bg-white shadow-sm flex flex-col justify-between">
                          <div className="h-24 w-full relative bg-slate-900 overflow-hidden">
                            <PlaceholderImage src={img.url} title={img.caption} alt={img.caption} className="h-full w-full transition-transform hover:scale-105" />
                            <span className="absolute bottom-1 left-1 px-1.5 py-0.5 rounded bg-black/70 text-amber-300 text-[9px] font-bold">
                              {img.category}
                            </span>
                          </div>
                          <div className="p-1.5 text-[9px] text-gray-500">
                            <p className="font-bold text-gray-800 truncate">{img.caption}</p>
                            <p className="text-[11px] text-emerald-600 truncate">{[img.photographer, img.license].filter(Boolean).join(" · ") || "Attribution unavailable"}</p>
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
                          <PlaceholderImage src={card.image} title={card.name} alt={card.name} className="h-full w-full" />
                          <span className="absolute top-2 left-2 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur text-amber-300 text-[10px] font-bold">
                            {card.category}
                          </span>
                        </div>
                        <div className="p-3 space-y-1.5">
                          <div className="flex justify-between items-start">
                            <h4 className="font-bold text-xs text-gray-900 leading-tight">{card.name}</h4>
                            <span className="text-xs text-amber-600 font-bold">{card.rating != null && card.rating !== "" ? `★ ${card.rating}` : "Rating unavailable"}</span>
                          </div>
                          <p className="text-[10px] text-gray-500">{card.city || "Location unavailable"} · <b>{card.budget != null && card.budget !== "" ? card.budget : "Budget unavailable"}</b></p>
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

                <HimalPackageCards
                  offers={message.package_cards}
                  onAdd={() => showToast("Added to trip basket", "success")}
                />

                {/* 5. Emergency Helplines Cards */}
                {message.emergency_cards && message.emergency_cards.length > 0 && (
                  <div className="max-w-[85%] mt-3 w-full bg-rose-50 border border-rose-200 p-3.5 rounded-2xl space-y-2">
                    <p className="text-xs font-bold text-rose-800 flex items-center gap-1.5">
                      <FiShield /> Emergency directory contacts
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {message.emergency_cards.map((em, i) => (
                        <div key={i} className="p-2 bg-white rounded-xl border border-rose-100 flex justify-between items-center text-xs">
                          <div>
                            <p className="font-bold text-gray-900 truncate">{em.name}</p>
                            <span className="text-[10px] text-gray-500">{em.type} ({em.district})</span>
                          </div>
                          <a
                            href={em.phone && !em.phone_is_national_fallback ? `tel:${em.phone}` : "#"}
                             onClick={(event) => { if (!em.phone || em.phone_is_national_fallback) event.preventDefault() }}
                             aria-disabled={!em.phone || Boolean(em.phone_is_national_fallback)}
                            className="px-2.5 py-1 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-bold text-[11px] flex items-center gap-1 shadow"
                          >
                            <FiPhoneCall size={10} /> {em.phone && !em.phone_is_national_fallback ? `Call ${em.phone}` : "No local phone recorded"}
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
                Himal AI is looking through available records…
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
              data-testid="himal-send"
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
