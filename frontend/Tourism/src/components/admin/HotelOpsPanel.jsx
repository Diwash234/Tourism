import { useCallback, useEffect, useState } from "react"
import { FiRefreshCw, FiCheck, FiX, FiFlag, FiCalendar, FiUsers, FiMapPin } from "react-icons/fi"
import adminPanelApi from "../../api/adminPanelApi"
import useToast from "../../hooks/useToast"

const TABS = [
  { id: "", label: "All", key: "all" },
  { id: "pending", label: "Pending" },
  { id: "confirmed", label: "Confirmed" },
  { id: "completed", label: "Completed" },
  { id: "cancelled", label: "Cancelled" },
]

const STATUS_STYLE = {
  pending: "bg-amber-100 text-amber-800",
  confirmed: "bg-emerald-100 text-emerald-700",
  completed: "bg-sky-100 text-sky-700",
  cancelled: "bg-rose-100 text-rose-700",
}

const ACTIONS = {
  pending: [
    { id: "confirm", label: "Confirm", cls: "bg-emerald-700", icon: <FiCheck /> },
    { id: "cancel", label: "Cancel", cls: "bg-rose-700", icon: <FiX /> },
  ],
  confirmed: [
    { id: "complete", label: "Mark Completed", cls: "bg-sky-700", icon: <FiFlag /> },
    { id: "cancel", label: "Cancel", cls: "bg-rose-700", icon: <FiX /> },
  ],
}

/**
 * Hotels & bookings scope-restricted operations (Staff Ops spec §11-12).
 * Staff only ever receive hotels they are assigned to and the bookings
 * attached to them — the backend enforces the scope on every call.
 */
export default function HotelOpsPanel({ module = "hotels" }) {
  const { showToast } = useToast()
  const [hotels, setHotels] = useState([])
  const [tab, setTab] = useState("")
  const [bookings, setBookings] = useState({ counts: {}, results: [] })
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)
  const [cancelNote, setCancelNote] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [h, b] = await Promise.all([
        adminPanelApi.myHotels(),
        adminPanelApi.myBookings(tab),
      ])
      setHotels(h.data.results || h.data || [])
      setBookings(b.data)
    } catch (error) {
      showToast(error.response?.data?.detail || "Hotel desk unavailable", "error")
    } finally {
      setLoading(false)
    }
  }, [tab, showToast])

  useEffect(() => {
    const t = setTimeout(() => load(), 0)
    return () => clearTimeout(t)
  }, [load])

  const run = async (booking, action) => {
    if (action === "cancel" && cancelNote !== booking.id) {
      setCancelNote(booking.id)
      return
    }
    setBusyId(booking.id)
    try {
      await adminPanelApi.bookingAction(booking.id, action)
      showToast(`Booking ${action}ed`, "success")
      setCancelNote(null)
      load()
    } catch (error) {
      showToast(error.response?.data?.detail || "Action denied", "error")
    } finally {
      setBusyId(null)
    }
  }

  const hotelList = Array.isArray(hotels) ? hotels : []

  return (
    <div className="space-y-4">
      {module === "hotels" && (
        <section className="bg-white border rounded-2xl overflow-hidden">
          <div className="p-4 border-b flex justify-between items-center">
            <b className="text-slate-900">My Assigned Hotels</b>
            <span className="text-xs text-slate-500">{hotelList.length} properties</span>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 p-4">
            {hotelList.map((h) => (
              <div key={h.id} className="border rounded-xl p-3">
                <b className="text-sm text-slate-900">{h.name}</b>
                <p className="text-xs text-slate-500 mt-1 flex items-center gap-1"><FiMapPin /> {h.address || h.destination_name || "Nepal"}</p>
                <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5"><FiUsers /> {h.phone || "no phone"}</p>
                {h.price_per_night != null && (
                  <p className="text-xs font-bold text-[#1D5146] mt-1">{h.currency} {h.price_per_night}/night</p>
                )}
              </div>
            ))}
            {!loading && !hotelList.length && (
              <p className="col-span-full p-8 text-center text-slate-500 text-sm">No hotels assigned to you yet — an administrator can assign hotels from the admin panel.</p>
            )}
          </div>
        </section>
      )}

      <section className="bg-white border rounded-2xl overflow-hidden">
        <div className="p-4 border-b flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap gap-1.5">
            {TABS.map((t) => (
              <button
                key={t.id || "all"}
                onClick={() => setTab(t.id)}
                aria-pressed={tab === t.id}
                className={`px-3 py-1.5 rounded-full text-xs font-bold transition ${tab === t.id ? "bg-[#102A2E] text-white" : "bg-white border text-slate-600 hover:bg-slate-100"}`}
              >
                {t.label}
                <span className={`ml-1.5 ${tab === t.id ? "text-slate-300" : "text-slate-400"}`}>{bookings.counts?.[t.key ?? t.id] ?? 0}</span>
              </button>
            ))}
          </div>
          <button onClick={load} className="px-3 py-2 bg-white border rounded-xl text-xs font-bold flex items-center gap-2">
            <FiRefreshCw className={loading ? "animate-spin" : ""} /> Refresh
          </button>
        </div>

        <div className="divide-y">
          {bookings.results.map((b) => (
            <div key={b.id} className="p-4">
              <div className="flex flex-col lg:flex-row lg:items-center gap-2">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <b className="text-sm text-slate-900">{b.reference} · {b.hotel_name}</b>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${STATUS_STYLE[b.status] || "bg-slate-100"}`}>{b.status}</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {b.customer_name} ({b.customer_email}) ·
                    <FiCalendar className="inline mx-1" />{b.check_in} → {b.check_out} ·
                    <FiUsers className="inline mx-1" />{b.guests} guest{b.guests > 1 ? "s" : ""}
                    {b.total_price ? ` · ${b.currency} ${b.total_price}` : ""}
                  </p>
                  {b.special_requests && <p className="text-xs text-slate-500 mt-1 italic">“{b.special_requests}”</p>}
                </div>
                <div className="flex flex-wrap gap-2">
                  {(ACTIONS[b.status] || []).map((a) => (
                    <button
                      key={a.id}
                      onClick={() => run(b, a.id)}
                      disabled={busyId === b.id}
                      className={`px-3 py-1.5 ${a.cls} hover:opacity-90 disabled:opacity-40 text-white rounded-lg text-xs font-bold flex items-center gap-1.5`}
                    >
                      {a.icon} {a.label}
                    </button>
                  ))}
                </div>
              </div>
              {cancelNote === b.id && (
                <div className="mt-2 flex flex-col sm:flex-row gap-2">
                  <input
                    autoFocus
                    placeholder="Optional reason shared with the customer…"
                    className="flex-1 border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-rose-500"
                    onChange={(e) => (b._note = e.target.value)}
                  />
                  <button
                    onClick={async () => {
                      setBusyId(b.id)
                      try {
                        await adminPanelApi.bookingAction(b.id, "cancel", b._note || "")
                        showToast("Booking cancelled", "success")
                        setCancelNote(null)
                        load()
                      } catch (error) {
                        showToast(error.response?.data?.detail || "Action denied", "error")
                      } finally {
                        setBusyId(null)
                      }
                    }}
                    disabled={busyId === b.id}
                    className="px-3 py-1.5 bg-rose-700 text-white rounded-lg text-xs font-bold"
                  >
                    Confirm cancellation
                  </button>
                </div>
              )}
            </div>
          ))}
          {!loading && !bookings.results.length && (
            <p className="p-10 text-center text-slate-500 text-sm">No bookings in this view for your assigned hotels.</p>
          )}
        </div>
      </section>
    </div>
  )
}
