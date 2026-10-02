import { useEffect, useState } from "react"
import PageHeader from "../components/common/PageHeader"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import { motion } from "framer-motion"
import {
  FiMapPin, FiUploadCloud, FiClock, FiShield,
  FiCompass, FiInfo, FiCrosshair, FiHome, FiPhoneCall,
  FiLayers, FiImage, FiEdit3
} from "react-icons/fi"
import { getCurrentPosition } from "../services/api.js"
import destinationApi from "../api/destinationApi"
import photoApi from "../services/photoApi"
import useToast from "../hooks/useToast"
import Breadcrumbs from "../components/common/Breadcrumbs"
import {
  NEPAL_ALL_PROVINCES, NEPAL_ALL_DISTRICTS,
  DISTRICT_DEFAULTS, resolveFuzzyPlaceLocation
} from "../utils/nepalGeocoder"

export default function SubmitPlacePage() {
  const { showToast } = useToast()
  const [categories, setCategories] = useState([])
  const [submitting, setSubmitting] = useState(false)
  const [status, setStatus] = useState(null)
  const [autoGeocodeMatch, setAutoGeocodeMatch] = useState(null)

  // Administrative selection
  const [selectedProvince, setSelectedProvince] = useState("")
  const [selectedDistrict, setSelectedDistrict] = useState("")
  const [selectedMunicipality, setSelectedMunicipality] = useState("")
  const [manualMuniMode, setManualMuniMode] = useState(false)
  const [manualMuniText, setManualMuniText] = useState("")
  const [selectedWard, setSelectedWard] = useState("")
  const [villageTole, setVillageTole] = useState("")

  const [form, setForm] = useState({
    name: "",
    category: "",
    district: "",
    municipality: "",
    ward_number: "",
    province: "",
    city: "",
    latitude: "",
    longitude: "",
    altitude: "",
    entry_fee: "",
    opening_hours: "",
    best_time_to_visit: "",
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
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => {
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
    }, 0)
    return () => clearTimeout(t)
  }, [])

  // Administrative selections are kept separate from coordinates. A district
  // centre is not a verified point for a new place, so coordinates remain
  // blank until the submitter uses GPS or enters them manually.
  useEffect(() => {
    const t = setTimeout(() => {
      const muniNameToUse = manualMuniMode ? manualMuniText : selectedMunicipality
      setForm((prev) => ({
        ...prev,
        province: selectedProvince,
        district: selectedDistrict,
        municipality: muniNameToUse || "",
        ward_number: selectedWard,
        city: "",
        latitude: "",
        longitude: "",
        altitude: "",
      }))
    }, 0)
    return () => clearTimeout(t)
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
        update("latitude", "")
        update("longitude", "")
        update("altitude", "")
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
      showToast("GPS position acquired", "success")
    } else {
      setStatus("No device GPS position was acquired. You can enter coordinates manually or leave them blank.")
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

    // Sanitize numbers to prevent nan-08 errors
    const latRaw = form.latitude === "" || form.latitude == null ? null : parseFloat(form.latitude)
    const lonRaw = form.longitude === "" || form.longitude == null ? null : parseFloat(form.longitude)
    const coordsValid = (latRaw == null && lonRaw == null) ||
      (latRaw != null && lonRaw != null && Number.isFinite(latRaw) && Number.isFinite(lonRaw) &&
        latRaw >= 26 && latRaw <= 31 && lonRaw >= 80 && lonRaw <= 89)
    if (!coordsValid) {
      showToast("Coordinates must be inside Nepal (lat 26–31, lng 80–89) or left blank.", "error")
      return
    }
    setSubmitting(true)
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
        if (latRaw != null && lonRaw != null) {
          formData.append("latitude", latRaw.toFixed(6))
          formData.append("longitude", lonRaw.toFixed(6))
        }
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
      const { data: submittedDestination } = await destinationApi.submit(formData)
       const uploadedGallery = galleryImages.slice(0, 5)
       if (uploadedGallery.length && (submittedDestination?.slug || submittedDestination?.id)) {
         const destinationRef = submittedDestination.slug || submittedDestination.id
         const galleryResults = await Promise.allSettled(uploadedGallery.map((file) => {
           const galleryForm = new FormData()
           galleryForm.append("image", file)
           galleryForm.append("caption", file.name)
           return photoApi.upload(destinationRef, galleryForm)
         }))
         if (galleryResults.some((result) => result.status === "rejected")) {
           showToast("Place submitted, but some additional photos need to be uploaded again.", "info")
         }
       }
      showToast("Place submitted for review.", "success")
      setStatus("Submission sent for review. An administrator will review your place, pictures and coordinates before publication.")
       try { sessionStorage.setItem("nepal_yatra_submission_receipt", "place") } catch { /* private mode */ }
      setForm({
        name: "",
        category: categories[0]?.id || "",
        district: selectedDistrict,
        municipality: selectedMunicipality,
        ward_number: selectedWard,
        province: selectedProvince,
        city: selectedDistrict,
        latitude: "",
        longitude: "",
        altitude: "",
        entry_fee: "",
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
      setSubmitting(false)
    }
  }

  const currentDistricts = NEPAL_ALL_DISTRICTS[selectedProvince] || []
  const distInfo = DISTRICT_DEFAULTS[selectedDistrict]
  const currentMunicipalities = selectedDistrict ? (distInfo?.munis || [`${selectedDistrict} Municipality`, `${selectedDistrict} Rural Municipality`]) : []

  return (
    <div className="ny-page container-app max-w-5xl space-y-6 py-6 sm:py-8">
      <CMSPageIntro pageKey="submit-place" />
      <Breadcrumbs items={[{ label: "Submit a Place", to: "/destinations/submit" }]} />

      <div className="text-center mb-8">
        <span className="px-3.5 py-1 rounded-full bg-emerald-100 text-[#1D5146] text-xs font-black uppercase tracking-wider">
          All 77 Districts & 753 Local Bodies
        </span>
        <PageHeader title="Submit a New Nepal Destination" subtitle="Share a place with evidence. Submissions are reviewed before they appear publicly." icon={FiMapPin} />
        <p className="text-gray-500 text-sm max-w-2xl mx-auto mt-1">
          Select or manually enter a district, municipality, village or ward, attach photos, and submit the record for review. Leave a field blank when it is not known.
        </p>
      </div>

      <motion.form
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        onSubmit={handleSubmit}
        className="ny-panel p-5 sm:p-8"
      >
        {/* Section 1: Basic Details */}
        <div>
          <h3 className="font-bold text-base text-gray-900 border-b pb-2 flex items-center gap-2">
            <FiCompass className="text-emerald-700" /> 1. Destination Identification
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
                <div className="mt-2 p-2.5 rounded-xl bg-[#F7F8F5] border border-[#E5E0D5] text-xs text-[#102A2E] flex items-center justify-between">
                  <div>
                    <span className="font-bold">Administrative match:</span> {autoGeocodeMatch.district}, {autoGeocodeMatch.province}
                    <span className="text-[11px] text-[#102A2E] ml-2">
                      (Provide GPS or coordinates manually for an exact map point.)
                    </span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[10px] font-black uppercase">
                    Name match
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
                <FiLayers className="text-emerald-700" /> 2. Administrative Location (77 Districts & Municipalities)
              </h3>
              <p className="text-[11px] text-gray-400">
                Choose the administrative area, then use GPS or enter coordinates manually. A district centre is not treated as an exact place location.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setManualMuniMode(!manualMuniMode)}
                className={`text-xs font-bold px-3 py-1.5 rounded-xl border flex items-center gap-1 transition-all ${
                  manualMuniMode ? "bg-[#102A2E] text-white border-purple-700" : "bg-[#F7F8F5] text-[#102A2E] border-[#E5E0D5]"
                }`}
              >
                <FiEdit3 size={13} /> {manualMuniMode ? "Switch to Dropdown" : "✍️ Type Custom Village/Muni"}
              </button>
              <button
                type="button"
                onClick={handleDetectGPS}
                className="text-xs font-bold text-[#102A2E] hover:text-[#1D5146] flex items-center gap-1 bg-[#F7F8F5] px-3 py-1.5 rounded-xl border border-[#E5E0D5]"
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
                required
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
                <option value="">Select province</option>
                 {NEPAL_ALL_PROVINCES.map((p) => (
                  <option key={p} value={p}>{p} Province</option>
                ))}
              </select>
            </div>

            <div>
              <label className="font-semibold text-gray-700">District (77 Districts) *</label>
              <select
                className="input-field mt-1 text-xs font-medium"
                required
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
                <option value="">Select district</option>
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
                  required
                   value={selectedMunicipality}
                  onChange={(e) => setSelectedMunicipality(e.target.value)}
                >
                  <option value="">Select municipality</option>
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
                className="input-field mt-1 text-xs font-bold text-[#102A2E]"
                value={selectedWard}
                onChange={(e) => setSelectedWard(e.target.value)}
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
          <div className="mt-3 p-4 rounded-2xl bg-[#F7F8F5]/80 border border-[#E5E0D5] grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
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
              <p className="text-xs font-extrabold text-[#102A2E] mt-1">
                {selectedDistrict}, Ward {selectedWard}
              </p>
            </div>
          </div>
        </div>

        {/* Section 3: Descriptions, Cultural & Religious Background */}
        <div>
          <h3 className="font-bold text-base text-gray-900 border-b pb-2 flex items-center gap-2">
            <FiInfo className="text-emerald-700" /> 3. Detailed Descriptions & Cultural Heritage
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
            <FiClock className="text-emerald-700" /> 4. Travel Logistics & Nearby Services
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
                placeholder="e.g. name, address and verified contact number"
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
                placeholder="e.g. name, address and verified contact number"
                value={form.nearest_police_info}
                onChange={(e) => update("nearest_police_info", e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Section 5: High-Resolution Photo Uploads with Live Preview */}
        <div>
          <h3 className="font-bold text-base text-gray-900 border-b pb-2 flex items-center gap-2">
            <FiUploadCloud className="text-emerald-700" /> 5. High-Resolution Destination Photos
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
            <div className="p-5 border-2 border-dashed border-[#E5E0D5] rounded-2xl text-center bg-[#F7F8F5]/50 hover:bg-[#F7F8F5] transition-colors">
              <FiUploadCloud size={32} className="mx-auto text-emerald-700 mb-2" />
              <p className="font-bold text-sm text-gray-800">Main Cover Photo *</p>
              <p className="text-xs text-gray-500 mb-2">Upload featured landscape photo</p>
              <input
                type="file"
                accept="image/*"
                className="text-xs text-gray-600 cursor-pointer"
                onChange={handleCoverImageChange}
              />
              {coverImagePreview && (
                <div className="mt-3 h-32 rounded-xl overflow-hidden border border-[#E5E0D5]">
                  <img src={coverImagePreview} alt="Cover Preview" className="w-full h-full object-cover" />
                </div>
              )}
            </div>

            <div className="p-5 border-2 border-dashed border-[#E5E0D5] rounded-2xl text-center bg-[#F7F8F5]/50 hover:bg-[#F7F8F5] transition-colors">
              <FiImage size={32} className="mx-auto text-emerald-700 mb-2" />
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
                    <img key={i} src={preview} alt={`Gallery ${i}`} className="w-14 h-14 rounded-lg object-cover border border-[#E5E0D5] shrink-0" />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="btn-primary w-full py-4 text-base font-bold bg-gradient-to-r from-[#1f6b4d] to-[#14503a] hover:from-[#2a8562] hover:to-[#14503a] shadow-xl rounded-2xl text-white transition-all disabled:opacity-50"
        >
          {submitting ? "Submitting for Verification..." : "Submit Destination for Admin Approval"}
        </button>

        {status && (
          <div className="p-4 rounded-xl bg-[#F7F8F5] border border-[#E5E0D5] text-[#102A2E] text-xs leading-relaxed">
            {status}
          </div>
        )}
      </motion.form>
    </div>
  )
}
