import { useEffect, useRef, useState } from "react"
import VerificationBadge from "../components/common/VerificationBadge"
import PageHeader from "../components/common/PageHeader"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import { useNavigate, useSearchParams } from "react-router-dom"
import { reportError } from "../utils/errorLogger"
import { motion } from "framer-motion"

import {
  FiCalendar,
  FiUsers,
  FiDollarSign,
  FiMapPin,
  FiCheckCircle,
  FiAlertCircle,
  FiNavigation,
  FiLoader,
  FiSliders,
  FiPlus,
  FiTrash2,
  FiActivity,
  FiCheckSquare,
} from "react-icons/fi"

import itineraryApi from "../api/itineraryApi"
import SharePlanButton from "../components/itinerary/SharePlanButton"
import axiosClient from "../api/axiosClient"
import { formatDistance, formatDuration } from "../utils/formatDistance"
import useToast from "../hooks/useToast"
import TripReadinessPanel from "../components/itinerary/TripReadinessPanel"
import CuratedItineraryShowcase from "../components/itinerary/CuratedItineraryShowcase"
import AltitudeSafetyModal from "../components/itinerary/AltitudeSafetyModal"
import CostBreakdownModal from "../components/itinerary/CostBreakdownModal"
import PackingChecklistModal from "../components/itinerary/PackingChecklistModal"
import LocalTrailSecrets from "../components/itinerary/LocalTrailSecrets"
import PrintableTravelBrief from "../components/itinerary/PrintableTravelBrief"
import TippingAndCurrencyGuide from "../components/itinerary/TippingAndCurrencyGuide"
import { NATIONALITY_OPTIONS } from "../utils/currency"
import { useI18n } from "../i18n"


const NOTE_CATEGORIES = [
  { key: "itin.note_hotel", fallback: "Hotel" },
  { key: "itin.note_transport", fallback: "Transport" },
  { key: "itin.note_food", fallback: "Food" },
  { key: "itin.note_activity", fallback: "Activity" },
  { key: "itin.note_other", fallback: "Other" },
]

const AI_MODIFICATIONS = [
  ["cheaper", "itin.mod_cheaper", "Budget-Friendly (कम खर्च)"],
  ["luxurious", "itin.mod_luxurious", "Extra Comfort & Boutique (आरामदायी)"],
  ["more_culture", "itin.mod_culture", "Deep Cultural Heritage (संस्कृति)"],
  ["more_nature", "itin.mod_nature", "Scenic Viewpoints (प्रकृति दृश्य)"],
  ["slower_pace", "itin.mod_slower", "Gentle Acclimatization (सुस्त गति)"],
  ["replan", "itin.mod_replan", "Trail & Weather Adapt (मौसम अनुकूल)"],
]


const BUDGET_LEVELS = [
  { id: "budget", key: "itin.budget_budget", fallback: "Budget" },
  { id: "mid", key: "itin.budget_mid", fallback: "Mid-range" },
  { id: "standard", key: "itin.budget_standard", fallback: "Standard" },
  { id: "luxury", key: "itin.budget_luxury", fallback: "Luxury" },
]


const TRAVEL_STYLES = [
  { id: "leisure", key: "itin.style_leisure", fallback: "Leisure" },
  { id: "culture", key: "itin.style_culture", fallback: "Culture" },
  { id: "nature", key: "itin.style_nature", fallback: "Nature" },
  { id: "adventure", key: "itin.style_adventure", fallback: "Adventure" },
  { id: "city", key: "itin.style_city", fallback: "City" },
]


const TRAVEL_TYPES = [
  { id: "solo", key: "itin.type_solo", fallback: "Solo" },
  { id: "couple", key: "itin.type_couple", fallback: "Couple" },
  { id: "family", key: "itin.type_family", fallback: "Family" },
  { id: "group", key: "itin.type_group", fallback: "Group" },
]


const INTERESTS = [
  "culture",
  "heritage",
  "nature",
  "adventure",
  "spiritual",
  "city",
  "wildlife",
  "trekking",
]


const DEFAULT_FORM = {
  days: 3,
  travelers: 1,
  budget_npr: "",
  budget_level: "mid",
  travel_style: "culture",
  travel_type: "solo",
  interests: ["culture"],
  start_city: "",
  nationality: "foreign",
  travel_month: "",
}

const MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

// Only the fields the planner uses -- compared to show "inputs changed".
const planKey = (f) => JSON.stringify([f.days, f.travelers, f.budget_npr, f.budget_level, f.travel_style, f.travel_type, [...(f.interests || [])].sort(), (f.start_city || "").trim(), f.nationality, f.travel_month])

function toPayload(f) {
  const { travel_month: month, ...rest } = f
  return { ...rest, start_city: (f.start_city || "").trim(), ...(month ? { travel_month: Number(month) } : {}) }
}


function formatCleanPhone(phone) {
  if (!phone) return null
  const value = String(phone).replace(/\.0$/, "").trim()
  return ["nan", "null", "None", ""].includes(value) ? null : value
}

function enrichPlanBudget(rawPlan, form) {
  if (!rawPlan) return null
  const travelers = Math.max(1, Number(rawPlan.travelers || form?.travelers || 1))
  const days = Math.max(1, Number(rawPlan.days || form?.days || 3))
  const totalNpr = rawPlan.total_estimated_npr ?? rawPlan.total_budget_npr ?? null
  const perPersonNpr = totalNpr != null ? Math.round(Number(totalNpr) / travelers) : null
  const totalUsd = rawPlan.total_estimated_usd ?? null
  const perPersonUsd = totalUsd != null ? Math.round(Number(totalUsd) / travelers) : null
  const rawItinerary = Array.isArray(rawPlan.itinerary) ? rawPlan.itinerary : (Array.isArray(rawPlan.days_schedule) ? rawPlan.days_schedule : [])
  const enrichedDays = rawItinerary.map((day) => {
    const rawServices = day.nearby_services || {}
    const hotels = (rawServices.hotels || []).filter((hotel) => {
      const name = (hotel.name || hotel.title || "").toLowerCase()
      return !name.includes("hospital") && !name.includes("clinic") && !name.includes("dental") && !name.includes("medical")
    }).map((hotel) => ({ ...hotel, phone: formatCleanPhone(hotel.phone || hotel.phone_number) }))
    return { ...day, daily_budget_npr: day.daily_budget_npr ?? null, nearby_services: { ...rawServices, hotels, hospitals: (rawServices.hospitals || []).map((item) => ({ ...item, phone: formatCleanPhone(item.phone || item.phone_number) })), police: (rawServices.police || []).map((item) => ({ ...item, phone: formatCleanPhone(item.phone || item.phone_number) })) } }
  })
  return { ...rawPlan, travelers, days, total_estimated_npr: totalNpr, per_person_npr: perPersonNpr, total_estimated_usd: totalUsd, per_person_usd: perPersonUsd, itinerary: enrichedDays }
}

const Itinerary = () => {
  const { t } = useI18n()
  const tx = (key, fallback) => (t(key) !== key ? t(key) : fallback)

  // /itinerary?city=Dolakha (linked from the 77-district pages) prefills the
  // start city so every district can jump straight to its own itinerary.
  const [searchParams] = useSearchParams()
  const cityParam = (searchParams.get("city") || "").trim()
  const linkedPlace = cityParam || (searchParams.get("dest") || "").replace(/[-_]/g, " ").trim()
  const [form, setForm] = useState(
    () => (linkedPlace ? { ...DEFAULT_FORM, start_city: linkedPlace } : DEFAULT_FORM)
  )
  const [generatedKey, setGeneratedKey] = useState(null)
  const [prevLinkedPlace, setPrevLinkedPlace] = useState(linkedPlace)
  if (linkedPlace !== prevLinkedPlace) {
    setPrevLinkedPlace(linkedPlace)
    if (linkedPlace) setForm((old) => ({ ...old, start_city: linkedPlace }))
  }

  const [plan, setPlan] = useState(null)

  const [loading, setLoading] = useState(false)

  const [error, setError] = useState("")


  // FIX:
  // Do not use state because request id is not UI data.
  const lastRequestId = useRef(0)
  const planAbortRef = useRef(null)
  useEffect(() => () => planAbortRef.current?.abort(), [])




  const { showToast } = useToast()
  const navigate = useNavigate()

  // Merged from the old TripPlanner: optional ?dest= focus, AI refinement, and a
  // custom-cost notepad. The rich dataset engine remains the source of truth.
  const focusDestination = (searchParams.get("dest") || "").replace(/[-_]/g, " ").trim()

  const [modifying, setModifying] = useState(false)
  const [showSafetyModal, setShowSafetyModal] = useState(false)
  const [showCostModal, setShowCostModal] = useState(false)
  const [showPackingModal, setShowPackingModal] = useState(false)
  const [showSecretsModal, setShowSecretsModal] = useState(false)
  const [showPrintModal, setShowPrintModal] = useState(false)
  const [showTippingModal, setShowTippingModal] = useState(false)
  const [notes, setNotes] = useState([])
  const [noteForm, setNoteForm] = useState({ category: "Hotel", label: "", amount: "" })

  const notesTotal = notes.reduce((sum, n) => sum + (Number(n.amount) || 0), 0)
  const grandTotalNpr = Math.round((plan?.total_estimated_npr || 0) + notesTotal)

  const handleApplyAIModification = async (action) => {
    if (!plan) return
    setModifying(true)
    try {
      const { data } = await axiosClient.post("/ml/itinerary/modify/", { action, itinerary_data: plan })
      setPlan((prev) => ({ ...prev, itinerary: data.itinerary || prev.itinerary, total_estimated_npr: null, total_estimated_usd: null, per_person_npr: null, per_person_usd: null, fits_budget: null, modificationNote: data.modification_note }))
      showToast(data.modification_note || "Route customized successfully", "success")
    } catch {
      showToast("Could not modify itinerary.", "error")
    } finally {
      setModifying(false)
    }
  }

  const addNote = () => {
    const amount = Number(noteForm.amount)
    if (!noteForm.label?.trim() || !Number.isFinite(amount) || amount < 0) return
    setNotes((prev) => [...prev, { id: Date.now(), category: noteForm.category, label: noteForm.label.trim(), amount }])
    setNoteForm({ category: "Hotel", label: "", amount: "" })
  }
  const removeNote = (id) => setNotes((prev) => prev.filter((n) => n.id !== id))


  const update = (patch) => {

    setForm((old)=>({
      ...old,
      ...patch
    }))

  }

  const handleSelectCuratedPlan = (curatedPlan) => {
    const updatedForm = {
      ...form,
      days: curatedPlan.days || form.days,
      travelers: curatedPlan.travelers || form.travelers,
      nationality: curatedPlan.nationality || form.nationality,
      start_city: curatedPlan.itinerary?.[0]?.city || curatedPlan.itinerary?.[0]?.destinations?.[0]?.city || form.start_city,
      budget_npr: curatedPlan.total_estimated_npr || form.budget_npr,
    }
    setForm(updatedForm)
    setPlan(enrichPlanBudget(curatedPlan, updatedForm))
    setGeneratedKey(planKey(updatedForm))
    setError("")
  }

  const [savedPlan, setSavedPlan] = useState(null)
  const savePlan = async () => {
    try {
      // generation_source must be one of the model's choices ("manual" | "ml");
      // the planner's own `source` tag (e.g. "internal_db_engine") is kept
      // inside itinerary_data.
      const { data: saved } = await itineraryApi.savePlan({ title: `${form.start_city} ${form.days}-day itinerary`, travelers: form.travelers,
        budget_npr: plan?.total_estimated_npr || form.budget_npr || null, interests: form.interests,
        itinerary_data: plan, generation_source: "ml", notes: `${form.travel_style} · ${form.travel_type}${notes.length ? ` · Cost notes: ${notes.map((note) => `${note.label} (NPR ${note.amount})`).join("; ")}` : ""}` })
      setSavedPlan({ id: saved?.id, key: generatedKey, share_token: saved?.share_token || null })
      showToast("Travel plan saved to your account", "success")
    } catch (saveError) {
      showToast(saveError.response?.status === 401 ? "Sign in to save this travel plan" : "Could not save travel plan", "error")
    }
  }







  async function fetchPlan(payload) {


    const requestId = ++lastRequestId.current
    // Cancel the previous in-flight plan: the requestId guard only ignored its
    // answer, the stale request still occupied the server and the network.
    planAbortRef.current?.abort()
    const controller = new AbortController()
    planAbortRef.current = controller
    setLoading(true)

    setError("")



    try{


      const {data}=await itineraryApi.build(toPayload(payload), { signal: controller.signal })



      if(requestId===lastRequestId.current){

        setPlan(enrichPlanBudget(data, payload))
        setGeneratedKey(planKey(payload))

      }



    }catch(err){

      if (err?.code === "ERR_CANCELED" || err?.name === "CanceledError" || err?.name === "AbortError") return

      if(requestId===lastRequestId.current){


        // Technical detail goes to the console/telemetry, never to the traveller.
        const status = err?.response?.status
        const timedOut = err?.code === "ECONNABORTED" || /timeout/i.test(String(err?.message || ""))
        console.error(
          "[itinerary] generation failed",
          status || "",
          err?.response?.data?.detail || err?.message
        )
        try { reportError(err, { feature: "itinerary", action: "generate" }) } catch { /* telemetry optional */ }
        if (status) {
          setError(`The itinerary service returned an error (HTTP ${status}). Please try again.`)
        } else if (timedOut || err?.apiUnreachable) {
          setError(err.message || "The itinerary service is unreachable. Check your connection and try again.")
        } else {
          setError("We couldn't generate your itinerary right now. Please try again in a moment.")
        }


        setPlan(null)

      }


    }finally{


      if(requestId===lastRequestId.current){

        setLoading(false)

      }


    }


  }

  // Plans are generated only on an explicit request (the Generate button),
  // never on every keystroke. The one exception is arriving from a link that
  // names a place (?city= / ?dest=) -- that is itself an explicit request.
  useEffect(() => {
    if (!linkedPlace) return undefined
    const timer = setTimeout(() => fetchPlan(form), 0)
    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const generate = () => {
    if (!form.start_city?.trim()) { setError("Enter a start city or district first."); return }
    fetchPlan(form)
  }
  const cancelGenerate = () => { planAbortRef.current?.abort(); lastRequestId.current += 1; setLoading(false) }
  const inputsChanged = Boolean(plan && generatedKey && generatedKey !== planKey(form))







  const toggleInterest=(interest)=>{


    const current=form.interests.includes(interest)

      ? form.interests.filter(
          (i)=>i!==interest
        )

      : [
          ...form.interests,
          interest
        ]



    update({

      interests:
        current.length
          ? current
          : ["culture"]

    })


  }





  const totalLegs=(plan?.itinerary || []).reduce(

    (sum,day)=>
      sum+(day.legs || []).length,

    0

  )



  const totalTravelKm=(plan?.itinerary || []).reduce(

    (sum,day)=>

      sum+

      (day.legs || []).reduce(

        (s,l)=>
          s+(l.distance_km || 0),

        0

      ),

    0

  )

  // Collect ordered, coordinate-bearing stops across all days for
  // real road-routing navigation (cap 12, dedupe by name).
  const collectNavStops = () => {
    const pts = []
    const seen = new Set()
    for (const day of plan?.itinerary || []) {
      const cands = [...(day.destinations || []),
        ...(day.legs || []).map((l) => l.to || l.destination).filter(Boolean)]
      for (const d of cands) {
        const lat = Number(d?.latitude ?? d?.lat)
        const lng = Number(d?.longitude ?? d?.lng ?? d?.lon)
        const name = d?.name || "Stop"
        if (!Number.isFinite(lat) || !Number.isFinite(lng) || seen.has(name)) continue
        seen.add(name)
        pts.push({ name, latitude: lat, longitude: lng })
        if (pts.length >= 12) break
      }
      if (pts.length >= 12) break
    }
    return pts
  }

  const navigateItinerary = () => {
    const pts = collectNavStops()
    if (pts.length < 2) {
      showToast("This itinerary has fewer than 2 navigable stops with coordinates.", "error")
      return
    }
    sessionStorage.setItem("nav_itinerary_stops", JSON.stringify(pts))
    navigate(`/navigation?dest=${encodeURIComponent(pts[0].name)}&itinerary=1`)
  }

    return (
    <div className="ny-page container-app space-y-6 py-6 sm:py-8">
      {plan?.itinerary?.length > 0 && (
        <div className="mb-4 flex justify-end">
          <button onClick={navigateItinerary}
            className="ny-btn ny-btn-primary min-h-11">
            Navigate this itinerary (real road routing)
          </button>
        </div>
      )}
      <CMSPageIntro pageKey="itinerary" />

      <PageHeader title={t("itin.title")} subtitle={t("itin.subtitle")} icon={ FiCalendar } />

      {/* Curated Signature Master Itineraries Showcase */}
      <CuratedItineraryShowcase onSelectPlan={handleSelectCuratedPlan} currentNationality={form.nationality} />

      {/* Controls */}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 md:grid-cols-3 lg:grid-cols-5 mb-6">


        {/* Days */}

        <div>

          <label htmlFor="itin-days" className="block text-xs font-semibold text-gray-600 mb-1">
            {t("itin.days")}
          </label>


          <div className="relative">

            <FiCalendar
              className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
            />


            <input id="itin-days"

              type="number"

              min={1}

              max={30}

              value={form.days}


              onChange={(e)=>

                update({

                  days:Math.max(

                    1,

                    Math.min(

                      30,

                      Number(e.target.value)||1

                    )

                  )

                })

              }


              className="input-field pl-11"

            />

          </div>

        </div>





        {/* Travelers */}

        <div>

          <label htmlFor="itin-travelers" className="block text-xs font-semibold text-gray-600 mb-1">
            Travelers
          </label>


          <div className="relative">


            <FiUsers
              className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
            />


            <input id="itin-travelers"

              type="number"

              min={1}

              max={50}

              value={form.travelers}


              onChange={(e)=>

                update({

                  travelers:

                    Math.max(

                      1,

                      Number(e.target.value)||1

                    )

                })

              }


              className="input-field pl-11"

            />


          </div>


        </div>





        {/* Budget */}

        <div>


          <label htmlFor="itin-budget" className="block text-xs font-semibold text-gray-600 mb-1">
            Budget (NPR, optional)
          </label>


          <div className="relative">


            <FiDollarSign
              className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
            />


            <input id="itin-budget"

              type="number"

              min={0}

              placeholder={t("itin.budget_ph")}


              value={form.budget_npr}


              onChange={(e)=>

                update({

                  budget_npr:e.target.value

                })

              }


              className="input-field pl-11"

            />


          </div>


        </div>





        {/* Start city */}

        <div>


          <label htmlFor="itin-start" className="block text-xs font-semibold text-gray-600 mb-1">
            {t("itin.start_city")}
          </label>


          <div className="relative">


            <FiMapPin
              className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
            />


            <input id="itin-start"

              value={form.start_city}


              onChange={(e)=>

                update({

                  start_city:e.target.value

                })

              }


              required
               placeholder={t("itin.start_city_ph")}


              className="input-field pl-11"

            />


          </div>


        </div>





        {/* Budget level */}

        <div>


          <label htmlFor="itin-1" className="block text-xs font-semibold text-gray-600 mb-1">
            {t("itin.budget_level")}
          </label>


          <select id="itin-1"

            value={form.budget_level}


            onChange={(e)=>

              update({

                budget_level:e.target.value

              })

            }


            className="input-field"

          >


            {
              BUDGET_LEVELS.map((item)=>(

                <option

                  key={item.id}

                  value={item.id}

                >

                  {tx(item.key, item.fallback)}

                </option>

              ))
            }


          </select>


        </div>


      </div>





      {/* Travel style */}


      <div className="flex flex-wrap items-center gap-3 mb-4">


        <span className="text-xs font-semibold text-gray-600">
          Style:
        </span>



        {
          TRAVEL_STYLES.map((style)=>(


            <button

              key={style.id}

              type="button"


              onClick={()=>update({

                travel_style:style.id

              })}


              className={

                `px-3.5 py-1.5 rounded-xl text-sm font-medium transition-colors

                ${
                  form.travel_style===style.id

                  ?

                  "bg-himalaya-500 text-white"

                  :

                  "bg-white border border-gray-200 text-gray-600"

                }`

              }


            >

              {tx(style.key, style.fallback)}


            </button>


          ))
        }





        <span className="text-xs font-semibold text-gray-600 ml-4">

          Travel type:

        </span>




        {
          TRAVEL_TYPES.map((type)=>(


            <button

              key={type.id}

              type="button"


              onClick={()=>update({

                travel_type:type.id

              })}


              className={

                `px-3.5 py-1.5 rounded-xl text-sm font-medium

                ${
                  form.travel_type===type.id

                  ?

                  "bg-amber-500 text-white"

                  :

                  "bg-white border border-gray-200 text-gray-600"

                }`

              }


            >

              {tx(type.key, type.fallback)}


            </button>


          ))
        }


      </div>





      {/* Interests */}

      <div className="flex flex-wrap items-center gap-3 mb-8">


        <span className="text-xs font-semibold text-gray-600">
          Interests:
        </span>



        {
          INTERESTS.map((interest)=>(


            <button

              key={interest}

              type="button"


              onClick={()=>toggleInterest(interest)}


              className={

                `px-3.5 py-1.5 rounded-xl text-sm font-medium

                ${
                  form.interests.includes(interest)

                  ?

                  "bg-emerald-500 text-white"

                  :

                  "bg-white border border-gray-200 text-gray-600"

                }`

              }


            >

              {interest}


            </button>


          ))
        }


      </div>





      <div className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_auto] lg:items-end" data-testid="itinerary-generate-row">
        <div>
          <label htmlFor="itin-nationality" className="block text-xs font-semibold text-gray-600 mb-1">{t("itin.nationality")}</label>
          <select id="itin-nationality" className="input-field" value={form.nationality} onChange={(e) => setForm({ ...form, nationality: e.target.value })}>
            {NATIONALITY_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="itin-month" className="block text-xs font-semibold text-gray-600 mb-1">{t("itin.travel_month")}</label>
          <select id="itin-month" className="input-field" value={form.travel_month} onChange={(e) => setForm({ ...form, travel_month: e.target.value })}>
            <option value="">{t("itin.not_decided")}</option>
            {MONTH_NAMES.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
          </select>
        </div>
        <button type="button" onClick={generate} disabled={loading || !form.start_city?.trim()} className="ny-btn ny-btn-primary min-h-11 sm:col-span-2 lg:col-span-1" data-testid="itinerary-generate">
          {loading ? t("itin.generating") : plan ? t("itin.regenerate") : t("itin.generate")}
        </button>
        {inputsChanged && !loading && (
          <p role="status" className="text-xs font-medium text-amber-800 sm:col-span-2 lg:col-span-3">{t("itin.inputs_changed")}</p>
        )}
      </div>

      {/* Dual Persona Guidance Banner */}
      <div className="mb-6 rounded-2xl border border-slate-200/80 bg-slate-50/50 p-4 shadow-2xs">
        {form.nationality === "nepali" ? (
          <div className="flex items-start gap-3">
            <span className="text-2xl" aria-hidden="true">🇳🇵</span>
            <div>
              <p className="font-bold text-emerald-950 text-sm">
                नेपाली आन्तरिक पर्यटक योजना (Nepalese Domestic Explorer Mode)
              </p>
              <p className="mt-1 text-xs text-slate-700 leading-relaxed">
                नेपाली नागरिकका लागि कुनै TIMS कार्ड वा विदेशी निकुञ्ज परमिट चाहिँदैन। केवल सामान्य मन्दिर, पालिका तथा स्थानीय शुल्क (रु. २५ - रु. १५०) मात्र लाग्नेछ। स्थानीय डिलक्स बस, स्कोर्पियो जीप तथा रैथाने खानाका सिफारिसहरू उपलब्ध छन्।
              </p>
            </div>
          </div>
        ) : form.nationality === "saarc" ? (
          <div className="flex items-start gap-3">
            <span className="text-2xl" aria-hidden="true">🏛️</span>
            <div>
              <p className="font-bold text-blue-950 text-sm">
                SAARC National Explorer (सार्क देशहरूका नागरिकहरू)
              </p>
              <p className="mt-1 text-xs text-slate-700 leading-relaxed">
                Concessional entry rates (50% to 70% discount) apply across UNESCO World Heritage sites, National Parks, and Conservation Areas. Please ensure you carry your valid SAARC passport or government photo ID.
              </p>
            </div>
          </div>
        ) : (
          <div className="flex items-start gap-3">
            <span className="text-2xl" aria-hidden="true">🌍</span>
            <div>
              <p className="font-bold text-slate-900 text-sm">
                International Visitor Planning Mode (विदेशी पर्यटक)
              </p>
              <p className="mt-1 text-xs text-slate-700 leading-relaxed">
                Official TIMS Cards (NPR 2,000 / $20) and Conservation Area / National Park permits (Sagarmatha, ACAP, Langtang) are automatically calculated. Certified licensed trekking guides are required on declared mountain routes under NTB regulations.
              </p>
            </div>
          </div>
        )}
      </div>

      <div id="itinerary-plan-results" className="scroll-mt-6">
      {
        loading && (

          <div className="flex items-center gap-2 text-sm text-himalaya-600 mb-4">

            <FiLoader className="animate-spin"/>

            {t("itin.generating_plan")}
            <button type="button" onClick={cancelGenerate} className="ny-btn ny-btn-secondary min-h-9 px-3 text-xs">{t("common.cancel")}</button>

          </div>

        )
      }



      {
        error && (

          <div role="alert" className="mb-4 flex flex-col gap-3 rounded-[var(--ny-radius-md)] border border-[#E9B9B9] bg-[var(--ny-soft-red)] px-4 py-3 text-sm text-[var(--ny-danger)] sm:flex-row sm:items-center sm:justify-between">
            <span>{error}</span>
            <button type="button" onClick={generate} className="ny-btn ny-btn-secondary min-h-11 shrink-0 text-xs">{t("common.try_again")}</button>
          </div>

        )
      }
      {plan && !error && <TripReadinessPanel plan={plan} />}

      {plan && !error && (plan.cost_breakdown || plan.altitude_safety || plan.packing_checklist_detailed) && (
        <div className="flex flex-wrap gap-2.5 my-4">
          {plan.cost_breakdown && (
            <button
              type="button"
              onClick={() => setShowCostModal(true)}
              className="ny-btn ny-btn-secondary text-xs flex items-center gap-1.5 py-2 px-3.5 rounded-xl border-emerald-300 bg-emerald-50 text-emerald-900 hover:bg-emerald-100 font-bold shadow-2xs"
            >
              <FiDollarSign size={14} className="text-emerald-700" />
              <span>Itemized Cost Schedule (NPR {plan.cost_breakdown.total_npr?.toLocaleString()})</span>
            </button>
          )}
          {plan.altitude_safety && (
            <button
              type="button"
              onClick={() => setShowSafetyModal(true)}
              className="ny-btn ny-btn-secondary text-xs flex items-center gap-1.5 py-2 px-3.5 rounded-xl border-rose-300 bg-rose-50 text-rose-900 hover:bg-rose-100 font-bold shadow-2xs"
            >
              <FiActivity size={14} className="text-rose-700" />
              <span>AMS & High-Altitude Safety Guide ({plan.altitude_safety.max_elevation_m}m)</span>
            </button>
          )}
          {plan.packing_checklist_detailed && (
            <button
              type="button"
              onClick={() => setShowPackingModal(true)}
              className="ny-btn ny-btn-secondary text-xs flex items-center gap-1.5 py-2 px-3.5 rounded-xl border-blue-300 bg-blue-50 text-blue-900 hover:bg-blue-100 font-bold shadow-2xs"
            >
              <FiCheckSquare size={14} className="text-blue-700" />
              <span>Gear Checklist ({plan.packing_checklist_detailed.total_items} items)</span>
            </button>
          )}

          <button
            type="button"
            onClick={() => setShowSecretsModal(true)}
            className="ny-btn ny-btn-secondary text-xs flex items-center gap-1.5 py-2 px-3.5 rounded-xl border-amber-300 bg-amber-50 text-amber-950 hover:bg-amber-100 font-bold shadow-2xs"
          >
            <span>🏔️</span>
            <span>Trail Secrets & Etiquette (स्थानीय संस्कार)</span>
          </button>

          <button
            type="button"
            onClick={() => setShowTippingModal(true)}
            className="ny-btn ny-btn-secondary text-xs flex items-center gap-1.5 py-2 px-3.5 rounded-xl border-teal-300 bg-teal-50 text-teal-950 hover:bg-teal-100 font-bold shadow-2xs"
          >
            <span>💵</span>
            <span>Tipping & Mountain Cash (टिपिङ र नगद)</span>
          </button>

          <button
            type="button"
            onClick={() => setShowPrintModal(true)}
            className="ny-btn ny-btn-secondary text-xs flex items-center gap-1.5 py-2 px-3.5 rounded-xl border-slate-300 bg-slate-100 text-slate-900 hover:bg-slate-200 font-bold shadow-2xs"
          >
            <span>🖨️</span>
            <span>Printable Field Dossier (अफलाइन गाइड)</span>
          </button>
        </div>
      )}

      {/* Route Adaptation & Journey Customizer + Trip Cost Notepad */}
      {
        plan && !error && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-8">
            <div className="card-base p-5 space-y-3">
              <div className="flex justify-between items-center text-xs font-bold text-gray-800">
                <span className="flex items-center gap-1.5">
                  <FiSliders className="text-amber-500" /> Route Adaptation & Journey Customizer (यात्रा अनुकूलन)
                </span>
                {modifying && <span className="text-emerald-600 animate-pulse">Adapting journey schedule…</span>}
              </div>
              <p className="text-[11px] text-slate-500">
                {t("itin.tailor_hint")}
              </p>
              <div className="flex flex-wrap gap-1.5 text-xs">
                {AI_MODIFICATIONS.map(([act, key, fallback]) => (
                  <button
                    key={act}
                    disabled={modifying}
                    onClick={() => handleApplyAIModification(act)}
                    className="min-h-10 rounded-xl border border-[var(--ny-border)] bg-white px-3 py-1.5 text-gray-800 font-bold transition hover:border-[var(--ny-green)] hover:bg-[var(--ny-soft-green)]"
                  >
                    {tx(key, fallback)}
                  </button>
                ))}
              </div>
              {plan.modificationNote && (
                <p className="text-[11px] text-emerald-700 font-bold bg-emerald-50 p-2.5 rounded-xl border border-emerald-200">✓ {plan.modificationNote}</p>
              )}
              {focusDestination && (
                <p className="text-[11px] text-himalaya-600 font-bold bg-himalaya-50 p-2.5 rounded-xl border border-himalaya-100">🎯 {t("itin.planning_focus")}: {focusDestination}</p>
              )}
            </div>

            <div className="card-base p-5 space-y-3">
              <div>
                <h3 className="font-bold text-sm text-gray-900">{t("itin.notepad_title")}</h3>
                <p className="text-xs text-gray-500">{t("itin.notepad_sub")}</p>
              </div>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
                <select aria-label={t("itin.cost_category")} className="input-field bg-white text-xs" value={noteForm.category} onChange={(e) => setNoteForm({ ...noteForm, category: e.target.value })}>
                  {NOTE_CATEGORIES.map((c) => <option key={c.key} value={c.fallback}>{tx(c.key, c.fallback)}</option>)}
                </select>
                <input aria-label={t("itin.item_label")} className="input-field bg-white text-xs sm:col-span-1 lg:col-span-2" placeholder={t("itin.item_ph")} value={noteForm.label} onChange={(e) => setNoteForm({ ...noteForm, label: e.target.value })} />
                <div className="flex gap-2">
                  <input aria-label={t("itin.amount_label")} type="number" min="0" step="1" className="input-field bg-white text-xs" placeholder="रू" value={noteForm.amount} onChange={(e) => setNoteForm({ ...noteForm, amount: e.target.value })} />
                  <button onClick={addNote} className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-himalaya-600 text-white hover:bg-himalaya-700" aria-label={t("itin.add_note")}><FiPlus /></button>
                </div>
              </div>
              {notes.length > 0 && (
                <div className="space-y-2 text-xs">
                  {notes.map((n) => (
                    <div key={n.id} className="flex items-center justify-between border-b border-gray-100 pb-2">
                      <div className="min-w-0">
                        <span className="text-[10px] text-gray-400 font-bold uppercase">{n.category}</span>
                        <p className="font-bold text-gray-800 truncate">{n.label}</p>
                      </div>
                      <div className="flex items-center gap-3 shrink-0">
                        <span className="font-bold text-gray-900">रू {n.amount.toLocaleString()}</span>
                        <button onClick={() => removeNote(n.id)} className="grid h-11 w-11 place-items-center rounded-[var(--ny-radius-sm)] text-gray-400 hover:bg-rose-50 hover:text-rose-600" aria-label="Remove note"><FiTrash2 size={14} /></button>
                      </div>
                    </div>
                  ))}
                  <div className="flex justify-between font-bold pt-2"><span>{t("itin.notepad_total")}</span><span>रू {notesTotal.toLocaleString()}</span></div>
                </div>
              )}
              <div className="flex justify-between items-center pt-3 border-t border-gray-200">
                <span className="font-bold text-sm text-gray-900">{t("itin.grand_total")}</span>
                <span className="text-xl font-black text-himalaya-600">{plan?.total_estimated_npr != null ? `रू ${grandTotalNpr.toLocaleString()}` : `${t("itin.notes_label")}: रू ${notesTotal.toLocaleString()}`}</span>
              </div>
            </div>
          </div>
        )
      }

            {/* Summary */}

      {
        plan && !error && (

          <motion.div

            initial={{
              opacity:0,
              y:8
            }}

            animate={{
              opacity:1,
              y:0
            }}

            className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-4 mb-8"

          >
            {savedPlan?.id && savedPlan.key === generatedKey ? (
              <div className="card-base p-4 text-left border-2 border-emerald-300">
                <FiCheckCircle className="text-emerald-600 mb-1"/><b className="text-emerald-800">{t("itin.saved_to_account")}</b>
                <p className="mb-2 text-xs text-gray-500">{t("itin.share_readonly")}</p>
                <SharePlanButton planId={savedPlan.id} initialToken={savedPlan.share_token} compact />
              </div>
            ) : (
              <button onClick={savePlan} className="card-base p-4 text-left border-2 border-emerald-300 hover:bg-emerald-50">
                <FiCheckCircle className="text-emerald-600 mb-1"/><b className="text-emerald-800">{t("itin.save_plan")}</b><p className="text-xs text-gray-500">{t("itin.save_plan_sub")}</p>
              </button>
            )}

            <div className="card-base p-4">

              <p className="text-xs text-gray-500">
                {t("itin.total_estimate")}
              </p>


              <p className="text-2xl font-bold text-himalaya-600">

                रू {plan.total_estimated_npr?.toLocaleString() ?? "—"}

              </p>


              <p className="text-xs text-gray-400">

                {plan.total_estimated_usd != null ? `≈ $${Number(plan.total_estimated_usd).toLocaleString()} USD` : t("itin.usd_unavailable")}

              </p>


            </div>





            <div className="card-base p-4">

              <p className="text-xs text-gray-500">
                Per person
              </p>


              <p className="text-2xl font-bold text-himalaya-600">

                रू {plan.per_person_npr?.toLocaleString() ?? "—"}

              </p>


              <p className="text-xs text-gray-400">

                {plan.travelers} traveler(s)

              </p>


            </div>





            <div className="card-base p-4">

              <p className="text-xs text-gray-500">
                Total travel
              </p>


              <p className="text-2xl font-bold text-himalaya-600">

                {formatDistance(totalTravelKm)}

              </p>


              <p className="text-xs text-gray-400">

                {totalLegs} route leg(s)

              </p>


            </div>





            <div className="card-base p-4">


              <p className="text-xs text-gray-500">
                Fits your budget?
              </p>



              {
                plan.fits_budget === null ||

                plan.fits_budget === undefined ? (


                  <p className="text-2xl font-bold text-gray-400">
                    —
                  </p>


                ) : plan.fits_budget ? (


                  <p className="text-xl font-bold text-emerald-600 flex items-center gap-1">

                    <FiCheckCircle />

                    Yes

                  </p>


                ) : (


                  <p className="text-xl font-bold text-nepalred-500 flex items-center gap-1">

                    <FiAlertCircle />

                    No

                  </p>


                )

              }



              <p className="text-xs text-gray-400">

                {
                  plan.budget_npr

                  ?

                  `Budget: रू ${Number(plan.budget_npr).toLocaleString()}`

                  :

                  "No budget set"

                }

              </p>


            </div>



          </motion.div>

        )

      }







      {/* Day cards */}


      {
        plan && !error && (

          <div className="space-y-6">


            {
              plan.itinerary.map((day)=>(


                <motion.div


                  key={day.day}


                  initial={{
                    opacity:0,
                    y:10
                  }}


                  animate={{
                    opacity:1,
                    y:0
                  }}


                  className="card-base p-6"


                >



                  <div className="flex flex-wrap items-center justify-between gap-2 mb-4">


                    <div className="flex items-center gap-3">


                      <span className="w-10 h-10 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 text-white font-bold flex items-center justify-center">

                        {day.day}

                      </span>



                      <div>

                        <h3 className="font-bold">

                          Day {day.day} — {day.city}

                        </h3>


                        <p className="text-xs text-gray-500">

                          {day.theme}

                        </p>


                      </div>


                    </div>




                    <div className="text-sm">


                      <span className="text-xs text-gray-500">

                        Day budget:

                      </span>


                      <b className="text-himalaya-600">

                        {" "}रू {day.daily_budget_npr?.toLocaleString()}

                      </b>


                    </div>



                  </div>





                  {
                    day.legs?.map((leg,index)=>(


                      <div


                        key={index}


                        className="flex items-center gap-2 text-xs text-gray-600 bg-gray-50 rounded-xl px-3 py-2 mb-3"


                      >


                        <FiNavigation className="text-himalaya-500 shrink-0"/>



                        <span className="truncate">

                          {leg.from} → {leg.to}

                        </span>



                        <span className="ml-auto font-semibold">

                          {formatDistance(leg.distance_km)}

                        </span>



                        <span className="text-gray-400">

                          {formatDuration(leg.duration_min)}

                        </span>



                      </div>


                    ))
                  }






                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">


                    {
                      day.destinations?.map((dest,index)=>(


                        <div


                          key={`${dest.name}-${index}`}


                          className="border border-gray-100 rounded-xl p-3 hover:border-himalaya-200 transition-colors"


                        >


                          <span className="text-[10px] uppercase tracking-wide text-gray-400">

                            {dest.category}

                          </span>



                          <p className="font-medium text-sm mt-0.5">

                            {dest.name}

                          </p>




                          {
                            dest.latitude && dest.longitude && (

                              <p className="text-[11px] text-gray-400 mt-1">

                                {dest.latitude.toFixed(4)},
                                {" "}
                                {dest.longitude.toFixed(4)}

                              </p>

                            )
                          }


                        </div>


                      ))
                    }


                  </div>

                  {day.nearby_services && (
                    <div className="mt-5 pt-4 border-t">
                      <h4 className="text-xs font-black uppercase tracking-wide text-gray-500 mb-3">Nearby planning & emergency services</h4>
                      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
                        {[
                          ["Stay", day.nearby_services.hotels],
                          ["Hospital", day.nearby_services.hospitals],
                          ["Police", day.nearby_services.police],
                          ["🏦 Essentials", day.nearby_services.essentials],
                        ].map(([label, services]) => (
                          <div key={label} className="rounded-xl bg-gray-50 p-3">
                            <b className="text-xs">{label}</b>
                            {(services || []).length ? services.map((service) => (
                              <div key={`${label}-${service.id}`} className="mt-2 text-[11px] text-gray-600">
                                <span className="font-semibold block truncate">{service.name}</span>
                                <span>{service.distance_km} km straight-line{service.phone ? ` · ${service.phone}` : ""}</span>
                                <VerificationBadge record={service} compact className="mt-1" />
                                {(service.source_url || service.website) && (
                                  <a
                                    href={service.source_url || service.website}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="mt-1 inline-flex min-h-8 items-center text-[11px] font-semibold text-emerald-800 underline"
                                  >
                                    {service.source_url ? "Verify source" : "Visit website"}
                                  </a>
                                )}
                              </div>
                            )) : <p className="text-[11px] text-gray-500 mt-2">No verified record within 250 km in our database</p>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                </motion.div>


              ))
            }



          </div>


        )

      }







      {
        !plan && !error && !loading && (

          <p className="text-sm text-gray-400 text-center py-10">

            Enter a start city or district and press “Generate itinerary” — your day-by-day plan will appear here.

          </p>

        )
      }

      </div>

      {/* Altitude Safety & Lake Louise Modal */}
      <AltitudeSafetyModal
        isOpen={showSafetyModal}
        onClose={() => setShowSafetyModal(false)}
        safetyData={plan?.altitude_safety}
        title={plan?.title}
      />

      {/* Itemized Cost Breakdown Modal */}
      <CostBreakdownModal
        isOpen={showCostModal}
        onClose={() => setShowCostModal(false)}
        costData={plan?.cost_breakdown}
        title={plan?.title}
        currentParams={{
          nationality: plan?.nationality || form.nationality,
          style: "standard",
          travelers: plan?.travelers || form.travelers,
        }}
      />

      {/* Gear & Packing Checklist Modal */}
      <PackingChecklistModal
        isOpen={showPackingModal}
        onClose={() => setShowPackingModal(false)}
        packingData={plan?.packing_checklist_detailed}
        title={plan?.title}
        slug={plan?.slug || plan?.title?.toLowerCase()?.replace(/\s+/g, "-")}
      />

      {/* Local Trail Secrets & Mountain Wisdom Modal */}
      <LocalTrailSecrets
        isOpen={showSecretsModal}
        onClose={() => setShowSecretsModal(false)}
      />

      {/* Guide & Porter Tipping and Currency Guide Modal */}
      <TippingAndCurrencyGuide
        isOpen={showTippingModal}
        onClose={() => setShowTippingModal(false)}
        defaultDays={plan?.days || form.days}
        defaultTravelers={plan?.travelers || form.travelers}
      />

      {/* Printable Travel Brief & SOS Medical Card */}
      <PrintableTravelBrief
        isOpen={showPrintModal}
        onClose={() => setShowPrintModal(false)}
        plan={plan}
      />
    </div>

  )

}



export default Itinerary