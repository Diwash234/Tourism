import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiMapPin, FiUploadCloud, FiClock, FiDollarSign, FiShield,
  FiCompass, FiInfo, FiCheckCircle, FiCrosshair, FiHome, FiPhoneCall,
  FiLayers, FiImage, FiX, FiEdit3
} from "react-icons/fi"
import { getCurrentPosition } from "../services/api.js"
import destinationApi from "../api/destinationApi"
import useToast from "../hooks/useToast"
import Breadcrumbs from "../components/common/Breadcrumbs"
import {
  NEPAL_ALL_PROVINCES, NEPAL_ALL_DISTRICTS,
  DISTRICT_DEFAULTS, geocodeNepalPlace, resolveFuzzyPlaceLocation
} from "../utils/nepalGeocoder"

export default function SubmitPlacePage() {
  const { showToast } = useToast()
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState(null)
  const [autoGeocodeMatch, setAutoGeocodeMatch] = useState(null)

  // Administrative selection
  const [selectedProvince, setSelectedProvince] = useState("Gandaki")
  const [selectedDistrict, setSelectedDistrict] = useState("Kaski")
  const [selectedMunicipality, setSelectedMunicipality] = useState("Pokhara Metropolitan City")
  const [manualMuniMode, setManualMuniMode] = useState(false)
  const [manualMuniText, setManualMuniText] = useState("")
  const [selectedWard, setSelectedWard] = useState(6)
  const [villageTole, setVillageTole] = useState("")

  const [form, setForm] = useState({
    name: "",
    category: "",
    district: "Kaski",
    municipality: "Pokhara Metropolitan City",
    ward_number: 6,
    province: "Gandaki",
    city: "Pokhara",
    latitude: "28.209600",
    longitude: "83.985600",
    altitude: "822m",
    entry_fee: "0",
    opening_hours: "6:00 AM - 6:00 PM",
    best_time_to_visit: "October to April",
    short_description: "",
    description: "",
    history: "",
    nearest_hospital_info: "",
    nearest_hotel_info: "",
    nearest_police_info: "",
  })

  const [coverImage, setCoverImage] = useState(null)
  const [coverImagePreview, setCoverImagePreview] = useState(null)
  const [galleryImages, setGalleryImages] = useState([])
  const [galleryPreviews, setGalleryPreviews] = useState([])

  useEffect(() => {
    destinationApi
      .getCategories()
      .then(({ data }) => {
        const list = data.results || data || []
        setCategories(list)
        if (list.length > 0) {
          setForm((prev) => ({ ...prev, category: list[0].id }))
        }
      })
      .catch(() => setCategories([]))
  }, [])

  // Auto-calculate coordinates when Administrative hierarchy changes
  useEffect(() => {
    const muniNameToUse = manualMuniMode ? manualMuniText : selectedMunicipality
    const geo = geocodeNepalPlace(selectedProvince, selectedDistrict, muniNameToUse, selectedWard)
    setForm((prev) => ({
      ...prev,
      province: selectedProvince,
      district: selectedDistrict,
      municipality: muniNameToUse || selectedDistrict,
      ward_number: selectedWard,
      city: selectedDistrict,
      latitude: geo.lat.toFixed(6),
      longitude: geo.lng.toFixed(6),
      altitude: geo.alt,
    }))
  }, [selectedProvince, selectedDistrict, selectedMunicipality, selectedWard, manualMuniMode, manualMuniText])

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleNameChange = (val) => {
    update("name", val)
    if (val.trim().length >= 2) {
      const match = resolveFuzzyPlaceLocation(val.trim())
      if (match && match.district) {
        setAutoGeocodeMatch(match)
        if (match.province) setSelectedProvince(match.province)
        setSelectedDistrict(match.district)
        if (match.municipality) setSelectedMunicipality(match.municipality)
        update("latitude", match.latitude.toFixed(6))
        update("longitude", match.longitude.toFixed(6))
        update("altitude", match.altitude || "1,200m")
      } else {
        setAutoGeocodeMatch(null)
      }
    } else {
      setAutoGeocodeMatch(null)
    }
  }

  const handleDetectGPS = async () => {
    setStatus("Acquiring device GPS sensor coordinates...")
    const coords = await getCurrentPosition()
    if (coords && coords.latitude && coords.longitude) {
      update("latitude", coords.latitude.toFixed(6))
      update("longitude", coords.longitude.toFixed(6))
      setStatus("GPS location locked successfully!")
      showToast("GPS position acquired! 📍", "success")
    } else {
      setStatus("Could not acquire device GPS. Geocoded coordinates used.")
    }
  }

  const handleCoverImageChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setCoverImage(file)
      setCoverImagePreview(URL.createObjectURL(file))
    }
  }

  const handleGalleryImagesChange = (e) => {
    const files = Array.from(e.target.files)
    if (files.length > 0) {
      setGalleryImages(files)
      setGalleryPreviews(files.map((f) => URL.createObjectURL(f)))
    }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.name.trim()) return showToast("Place name is required", "error")

    setStatus("Validating details and uploading place...")
    setLoading(true)

    // Sanitize numbers to prevent nan-08 errors
    const latNum = parseFloat(form.latitude) || 28.2096
    const lonNum = parseFloat(form.longitude) || 83.9856
    const feeNum = parseFloat(form.entry_fee) || 0.0
    const muniFinal = manualMuniMode ? (manualMuniText.trim() || selectedDistrict) : selectedMunicipality

    const formData = new FormData()
    formData.append("name", form.name.trim())
    formData.append("category", form.category)
    formData.append("province", selectedProvince)
    formData.append("district", selectedDistrict)
    formData.append("municipality", muniFinal)
    formData.append("ward_number", selectedWard)
    formData.append("city", villageTole.trim() ? `${villageTole.trim()}, ${selectedDistrict}` : selectedDistrict)
    formData.append("latitude", latNum.toFixed(6))
    formData.append("longitude", lonNum.toFixed(6))
    formData.append("altitude", form.altitude.trim())
    formData.append("entry_fee", feeNum.toFixed(2))
    formData.append("opening_hours", form.opening_hours.trim())
    formData.append("best_time_to_visit", form.best_time_to_visit.trim())
    formData.append("short_description", form.short_description.trim())
    formData.append("description", form.description.trim())
    formData.append("history", form.history.trim())
    formData.append("nearest_hospital_info", form.nearest_hospital_info.trim())
    formData.append("nearest_hotel_info", form.nearest_hotel_info.trim())
    formData.append("nearest_police_info", form.nearest_police_info.trim())

    if (coverImage) {
      formData.append("cover_image", coverImage)
    }

    try {
      await destinationApi.submit(formData)
      showToast("Place submitted successfully! Queued for Admin Verification. 🏔️", "success")
      setStatus("Submission sent! An administrator will review your place, pictures, and coordinates in the Admin Dashboard.")
      setForm({
        name: "",
        category: categories[0]?.id || "",
        district: selectedDistrict,
        municipality: selectedMunicipality,
        ward_number: selectedWard,
        province: selectedProvince,
        city: selectedDistrict,
        latitude: "28.209600",
        longitude: "83.985600",
        altitude: "822m",
        entry_fee: "0",
        opening_hours: "",
        best_time_to_visit: "",
        short_description: "",
        description: "",
        history: "",
        nearest_hospital_info: "",
        nearest_hotel_info: "",
        nearest_police_info: "",
      })
      setCoverImage(null)
      setCoverImagePreview(null)
      setGalleryImages([])
      setGalleryPreviews([])
      setVillageTole("")
    } catch (err) {
      console.error("Submission failed:", err.response?.data || err)
      const errorMsg =
        err.response?.data?.detail ||
        JSON.stringify(err.response?.data) ||
        "Submission failed. Please check required fields."
      showToast(errorMsg, "error")
      setStatus(`Error: ${errorMsg}`)
    } finally {
      setLoading(false)
    }
  }

  const currentDistricts = NEPAL_ALL_DISTRICTS[selectedProvince] || []
  const distInfo = DISTRICT_DEFAULTS[selectedDistrict]
  const currentMunicipalities = distInfo?.munis || [`${selectedDistrict} Municipality`, `${selectedDistrict} Rural Municipality`]

  return (
    <div className="container-app py-8 max-w-4xl animate-fadeIn space-y-6">
      <Breadcrumbs items={[{ label: "Submit a Place", to: "/destinations/submit" }]} />

      <div className="text-center mb-8">
        <span className="px-3.5 py-1 rounded-full bg-purple-100 text-purple-800 text-xs font-black uppercase tracking-wider">
          All 77 Districts & 753 Local Bodies
        </span>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 mt-2 flex items-center justify-center gap-2">
          <FiMapPin className="text-purple-700" /> Submit a New Nepal Destination
        </h1>
        <p className="text-gray-500 text-sm max-w-2xl mx-auto mt-1">
          Select or manually enter any district, municipality, village, or ward across Nepal to auto-calculate coordinates, attach photos, and submit for Admin Verification.
        </p>
      </div>

      <motion.form
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        onSubmit={handleSubmit}
        className="card-base p-6 sm:p-8 space-y-6 shadow-2xl border border-purple-100 rounded-3xl bg-white"
      >
        {/* Section 1: Basic Details */}
        <div>
          <h3 className="font-bold text-base text-gray-900 border-b pb-2 flex items-center gap-2">
            <FiCompass className="text-purple-600" /> 1. Destination Identification
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4 text-xs">
            <div>
              <label className="font-semibold text-gray-700">Place / Landmark Name *</label>
              <input
                className="input-field mt-1 text-sm font-medium"
                placeholder="e.g. Bihadi Parbat / Waling Valley / Galeshwor / Swargadwari..."
                value={form.name}
                onChange={(e) => handleNameChange(e.target.value)}
                required
              />
              {autoGeocodeMatch && (
                <div className="mt-2 p-2.5 rounded-xl bg-purple-50 border border-purple-200 text-xs text-purple-900 flex items-center justify-between">
                  <div>
                    <span className="font-bold">⚡ Auto-Geocoded:</span> {autoGeocodeMatch.district}, {autoGeocodeMatch.province}
                    <span className="text-[11px] text-purple-700 ml-2 font-mono">
                      (GPS: {autoGeocodeMatch.latitude?.toFixed(4)}° N, {autoGeocodeMatch.longitude?.toFixed(4)}° E · Alt: {autoGeocodeMatch.altitude})
                    </span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[10px] font-black uppercase">
                    {autoGeocodeMatch.confidence}% Match
                  </span>
                </div>
              )}
            </div>

            <div>
              <label className="font-semibold text-gray-700">Tourism Category *</label>
              <select
                className="input-field mt-1 text-sm font-medium"
                value={form.category}
                onChange={(e) => update("category", e.target.value)}
                required
              >
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Section 2: Administrative Geocoding & Ward / Gaunpalika */}
        <div>
          <div className="flex items-center justify-between border-b pb-2">
            <div>
              <h3 className="font-bold text-base text-gray-900 flex items-center gap-2">
                <FiLayers className="text-purple-600" /> 2. Administrative Location (77 Districts & Municipalities)
              </h3>
              <p className="text-[11px] text-gray-400">
                Coordinates & altitude are auto-calculated. You can also toggle manual entry to type any custom Gaunpalika / Village.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setManualMuniMode(!manualMuniMode)}
                className={`text-xs font-bold px-3 py-1.5 rounded-xl border flex items-center gap-1 transition-all ${
                  manualMuniMode ? "bg-purple-700 text-white border-purple-700" : "bg-purple-50 text-purple-700 border-purple-200"
                }`}
              >
                <FiEdit3 size={13} /> {manualMuniMode ? "Switch to Dropdown" : "✍️ Type Custom Village/Muni"}
              </button>
              <button
                type="button"
                onClick={handleDetectGPS}
                className="text-xs font-bold text-purple-700 hover:text-purple-800 flex items-center gap-1 bg-purple-50 px-3 py-1.5 rounded-xl border border-purple-200"
              >
                <FiCrosshair /> GPS Sensor
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 mt-4 text-xs">
            <div>
              <label className="font-semibold text-gray-700">Province *</label>
              <select
                className="input-field mt-1 text-xs font-medium"
                value={selectedProvince}
                onChange={(e) => {
                  const prov = e.target.value
                  setSelectedProvince(prov)
                  const dists = NEPAL_ALL_DISTRICTS[prov] || []
                  if (dists.length > 0) {
                    setSelectedDistrict(dists[0])
                    const dInfo = DISTRICT_DEFAULTS[dists[0]]
                    if (dInfo && dInfo.munis?.length > 0) {
                      setSelectedMunicipality(dInfo.munis[0])
                    }
                  }
                }}
              >
                {NEPAL_ALL_PROVINCES.map((p) => (
                  <option key={p} value={p}>{p} Province</option>
                ))}
              </select>
            </div>

            <div>
              <label className="font-semibold text-gray-700">District (77 Districts) *</label>
              <select
                className="input-field mt-1 text-xs font-medium"
                value={selectedDistrict}
                onChange={(e) => {
                  const dist = e.target.value
                  setSelectedDistrict(dist)
                  const dInfo = DISTRICT_DEFAULTS[dist]
                  if (dInfo && dInfo.munis?.length > 0) {
                    setSelectedMunicipality(dInfo.munis[0])
                  } else {
                    setSelectedMunicipality(`${dist} Municipality`)
                  }
                }}
              >
                {currentDistricts.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="font-semibold text-gray-700">Municipality / Gaunpalika *</label>
              {manualMuniMode ? (
                <input
                  className="input-field mt-1 text-xs font-medium"
                  placeholder="Type Gaunpalika / Municipality name..."
                  value={manualMuniText}
                  onChange={(e) => setManualMuniText(e.target.value)}
                />
              ) : (
                <select
                  className="input-field mt-1 text-xs font-medium"
                  value={selectedMunicipality}
                  onChange={(e) => setSelectedMunicipality(e.target.value)}
                >
                  {currentMunicipalities.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              )}
            </div>

            <div>
              <label className="font-semibold text-gray-700">Ward Number (1-35)</label>
              <input
                type="number"
                min={1}
                max={35}
                className="input-field mt-1 text-xs font-bold text-purple-900"
                value={selectedWard}
                onChange={(e) => setSelectedWard(parseInt(e.target.value, 10) || 1)}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3 text-xs">
            <div>
              <label className="font-semibold text-gray-700">Local Village / Tole / Settlement (Optional)</label>
              <input
                className="input-field mt-1 text-xs"
                placeholder="e.g. Chitre Village, Ghandruk Bazaar, Lakeside Ward 6"
                value={villageTole}
                onChange={(e) => setVillageTole(e.target.value)}
              />
            </div>
            <div>
              <label className="font-semibold text-gray-700">Approx. Elevation / Altitude</label>
              <input
                className="input-field mt-1 text-xs font-semibold"
                placeholder="e.g. 1,400m / 2,121m / 3,840m"
                value={form.altitude}
                onChange={(e) => update("altitude", e.target.value)}
              />
            </div>
          </div>

          {/* Coordinates readout and manual adjustments */}
          <div className="mt-3 p-4 rounded-2xl bg-purple-50/80 border border-purple-200 grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
            <div>
              <label className="text-[10px] text-gray-500 font-bold uppercase">Latitude (DD)</label>
              <input
                type="number"
                step="any"
                className="input-field mt-1 text-xs font-bold text-purple-950 bg-white"
                value={form.latitude}
                onChange={(e) => update("latitude", e.target.value)}
              />
            </div>
            <div>
              <label className="text-[10px] text-gray-500 font-bold uppercase">Longitude (DD)</label>
              <input
                type="number"
                step="any"
                className="input-field mt-1 text-xs font-bold text-purple-950 bg-white"
                value={form.longitude}
                onChange={(e) => update("longitude", e.target.value)}
              />
            </div>
            <div className="col-span-2 sm:col-span-1 flex flex-col justify-end">
              <span className="text-[10px] text-gray-500 font-bold uppercase">Location Geocode</span>
              <p className="text-xs font-extrabold text-purple-900 mt-1">
                📍 {selectedDistrict}, Ward {selectedWard}
              </p>
            </div>
          </div>
        </div>

        {/* Section 3: Descriptions, Cultural & Religious Background */}
        <div>
          <h3 className="font-bold text-base text-gray-900 border-b pb-2 flex items-center gap-2">
            <FiInfo className="text-purple-600" /> 3. Detailed Descriptions & Cultural Heritage
          </h3>
          <div className="space-y-4 mt-4 text-xs">
            <div>
              <label className="font-semibold text-gray-700">Short Summary (1-2 sentences)</label>
              <input
                className="input-field mt-1 text-sm"
                placeholder="Brief highlight shown on search and discovery cards"
                value={form.short_description}
                onChange={(e) => update("short_description", e.target.value)}
              />
            </div>

            <div>
              <label className="font-semibold text-gray-700">Full Description *</label>
              <textarea
                rows={4}
                className="input-field mt-1 text-sm leading-relaxed"
                placeholder="What makes this destination worth visiting? Describe the scenic ridges, trails, mountain panorama, and atmosphere..."
                value={form.description}
                onChange={(e) => update("description", e.target.value)}
                required
              />
            </div>

            <div>
              <label className="font-semibold text-gray-700">Historical Background & Legends</label>
              <textarea
                rows={3}
                className="input-field mt-1 text-sm leading-relaxed"
                placeholder="History, ancient temples, Mahabharata lore, King Bharata / Malla / Licchavi heritage..."
                value={form.history}
                onChange={(e) => update("history", e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Section 4: Travel Planning & Local Amenities */}
        <div>
          <h3 className="font-bold text-base text-gray-900 border-b pb-2 flex items-center gap-2">
            <FiClock className="text-purple-600" /> 4. Travel Logistics & Nearby Services
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4 text-xs">
            <div>
              <label className="font-semibold text-gray-700">Best Time to Visit</label>
              <input
                className="input-field mt-1 text-sm"
                placeholder="e.g. October to April"
                value={form.best_time_to_visit}
                onChange={(e) => update("best_time_to_visit", e.target.value)}
              />
            </div>
            <div>
              <label className="font-semibold text-gray-700">Entry Fee (NPR)</label>
              <input
                type="number"
                min={0}
                className="input-field mt-1 text-sm"
                placeholder="0 for free public places"
                value={form.entry_fee}
                onChange={(e) => update("entry_fee", e.target.value)}
              />
            </div>
            <div>
              <label className="font-semibold text-gray-700">Opening Hours</label>
              <input
                className="input-field mt-1 text-sm"
                placeholder="e.g. 24 Hours / 6am - 6pm"
                value={form.opening_hours}
                onChange={(e) => update("opening_hours", e.target.value)}
              />
            </div>

            <div>
              <label className="font-semibold text-gray-700 flex items-center gap-1">
                <FiPhoneCall /> Nearest Hospital / Clinic
              </label>
              <input
                className="input-field mt-1 text-sm"
                placeholder="e.g. Pyuthan District Hospital (+977-86-460114)"
                value={form.nearest_hospital_info}
                onChange={(e) => update("nearest_hospital_info", e.target.value)}
              />
            </div>

            <div>
              <label className="font-semibold text-gray-700 flex items-center gap-1">
                <FiHome /> Nearest Hotel / Lodge
              </label>
              <input
                className="input-field mt-1 text-sm"
                placeholder="e.g. Swargadwari Pilgrim Ashram & Lodge"
                value={form.nearest_hotel_info}
                onChange={(e) => update("nearest_hotel_info", e.target.value)}
              />
            </div>

            <div>
              <label className="font-semibold text-gray-700 flex items-center gap-1">
                <FiShield /> Nearest Police Station
              </label>
              <input
                className="input-field mt-1 text-sm"
                placeholder="e.g. Pyuthan Police Post (100)"
                value={form.nearest_police_info}
                onChange={(e) => update("nearest_police_info", e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Section 5: High-Resolution Photo Uploads with Live Preview */}
        <div>
          <h3 className="font-bold text-base text-gray-900 border-b pb-2 flex items-center gap-2">
            <FiUploadCloud className="text-purple-600" /> 5. High-Resolution Destination Photos
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
            <div className="p-5 border-2 border-dashed border-purple-200 rounded-2xl text-center bg-purple-50/50 hover:bg-purple-50 transition-colors">
              <FiUploadCloud size={32} className="mx-auto text-purple-600 mb-2" />
              <p className="font-bold text-sm text-gray-800">Main Cover Photo *</p>
              <p className="text-xs text-gray-500 mb-2">Upload featured landscape photo</p>
              <input
                type="file"
                accept="image/*"
                className="text-xs text-gray-600 cursor-pointer"
                onChange={handleCoverImageChange}
              />
              {coverImagePreview && (
                <div className="mt-3 h-32 rounded-xl overflow-hidden border border-purple-200">
                  <img src={coverImagePreview} alt="Cover Preview" className="w-full h-full object-cover" />
                </div>
              )}
            </div>

            <div className="p-5 border-2 border-dashed border-purple-200 rounded-2xl text-center bg-purple-50/50 hover:bg-purple-50 transition-colors">
              <FiImage size={32} className="mx-auto text-purple-600 mb-2" />
              <p className="font-bold text-sm text-gray-800">Additional Gallery Photos</p>
              <p className="text-xs text-gray-500 mb-2">Upload up to 5 additional pictures</p>
              <input
                type="file"
                multiple
                accept="image/*"
                className="text-xs text-gray-600 cursor-pointer"
                onChange={handleGalleryImagesChange}
              />
              {galleryPreviews.length > 0 && (
                <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
                  {galleryPreviews.map((preview, i) => (
                    <img key={i} src={preview} alt={`Gallery ${i}`} className="w-14 h-14 rounded-lg object-cover border border-purple-200 shrink-0" />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="btn-primary w-full py-4 text-base font-bold bg-gradient-to-r from-purple-700 to-rose-600 hover:from-purple-800 hover:to-rose-700 shadow-xl rounded-2xl text-white transition-all disabled:opacity-50"
        >
          {loading ? "Submitting for Verification..." : "Submit Destination for Admin Approval"}
        </button>

        {status && (
          <div className="p-4 rounded-xl bg-purple-50 border border-purple-200 text-purple-900 text-xs leading-relaxed">
            {status}
          </div>
        )}
      </motion.form>
    </div>
  )
}
