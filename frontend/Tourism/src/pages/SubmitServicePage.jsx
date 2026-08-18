import { useState } from "react"
import { FiCamera, FiMapPin, FiSend, FiVideo } from "react-icons/fi"
import axiosClient from "../api/axiosClient"
import useToast from "../hooks/useToast"
import Breadcrumbs from "../components/common/Breadcrumbs"

const TYPES = [
  ["hospital", "Hospital / Clinic"], ["hotel", "Hotel / Homestay"],
  ["police", "Police Station"], ["bank", "Bank / ATM"],
  ["fire_station", "Fire Station"], ["ambulance", "Ambulance Service"],
  ["pharmacy", "Pharmacy"], ["tourism_office", "Tourism Office"],
  ["destination", "Tourism Destination"],
]
const PROVINCES = ["Koshi", "Madhesh", "Bagmati", "Gandaki", "Lumbini", "Karnali", "Sudurpashchim"]

export default function SubmitServicePage() {
  const { showToast } = useToast()
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({ place_type: "hospital", name: "", description: "", phone: "", website: "", address: "", city: "", municipality: "", municipality_type: "municipality", ward_number: "", district: "", province: "Gandaki", latitude: "", longitude: "", transport_mode: "", route_origin: "", travel_time_minutes: "", distance_km: "", road_condition: "", price_npr: "", opening_hours: "", source_notes: "" })
  const [image, setImage] = useState(null)
  const [video, setVideo] = useState(null)
  const update = (key, value) => setForm((old) => ({ ...old, [key]: value }))

  const useGPS = () => navigator.geolocation?.getCurrentPosition(
    ({ coords }) => { update("latitude", coords.latitude.toFixed(6)); update("longitude", coords.longitude.toFixed(6)); showToast("GPS coordinates added", "success") },
    () => showToast("Could not access GPS", "error"),
  )

  const submit = async (e) => {
    e.preventDefault(); setSaving(true)
    try {
      const body = new FormData()
      Object.entries(form).forEach(([key, value]) => { if (value !== "") body.append(key, value) })
      if (image) body.append("image", image)
      if (video) body.append("video", video)
      await axiosClient.post("/infrastructure-submissions/", body, { headers: { "Content-Type": "multipart/form-data" } })
      showToast("Submitted for admin verification. It will appear publicly only after approval.", "success")
      setForm((old) => ({ ...old, name: "", description: "", phone: "", address: "", source_notes: "" })); setImage(null); setVideo(null)
    } catch (error) { showToast(error.response?.data?.detail || "Submission failed. Check required fields.", "error") }
    finally { setSaving(false) }
  }

  return <div className="container-app py-8 space-y-6">
    <Breadcrumbs items={[{ label: "Submit Local Service", to: "/submit-service" }]} />
    <div className="rounded-3xl bg-gradient-to-r from-emerald-900 to-teal-800 text-white p-7"><h1 className="text-3xl font-black">Help Map Local Nepal</h1><p className="text-sm text-emerald-100 mt-2">Send a hospital, hotel, police station, bank, emergency service or destination with GPS and evidence. Admin approval is required before database and CSV publication.</p></div>
    <form onSubmit={submit} className="rounded-3xl bg-white border shadow-sm p-6 space-y-6">
      <div className="grid md:grid-cols-3 gap-4">
        <label className="text-xs font-bold">Place type<select className="input-field mt-1" value={form.place_type} onChange={(e) => update("place_type", e.target.value)}>{TYPES.map(([v,l]) => <option key={v} value={v}>{l}</option>)}</select></label>
        <label className="text-xs font-bold md:col-span-2">Name *<input required className="input-field mt-1" value={form.name} onChange={(e) => update("name", e.target.value)} /></label>
        <label className="text-xs font-bold md:col-span-3">Description / condition<textarea className="input-field mt-1" rows="3" value={form.description} onChange={(e) => update("description", e.target.value)} placeholder="Services, condition, reliability, accessibility…" /></label>
        {[['phone','Phone'],['website','Website'],['opening_hours','Opening hours'],['address','Address'],['city','City'],['municipality','Municipality']].map(([key,label]) => <label key={key} className="text-xs font-bold">{label}<input className="input-field mt-1" value={form[key]} onChange={(e) => update(key,e.target.value)} /></label>)}
        <label className="text-xs font-bold">Municipality type<select className="input-field mt-1" value={form.municipality_type} onChange={(e) => update("municipality_type",e.target.value)}><option value="metropolitan">Metropolitan</option><option value="sub_metropolitan">Sub-metropolitan</option><option value="municipality">Municipality</option><option value="rural_municipality">Rural municipality</option></select></label>
        <label className="text-xs font-bold">Ward<input type="number" className="input-field mt-1" value={form.ward_number} onChange={(e) => update("ward_number",e.target.value)} /></label>
        <label className="text-xs font-bold">District *<input required className="input-field mt-1" value={form.district} onChange={(e) => update("district",e.target.value)} /></label>
        <label className="text-xs font-bold">Province<select className="input-field mt-1" value={form.province} onChange={(e) => update("province",e.target.value)}>{PROVINCES.map(p => <option key={p}>{p}</option>)}</select></label>
      </div>
      <div className="rounded-2xl bg-blue-50 border border-blue-100 p-4 space-y-3"><div className="flex justify-between"><b className="text-sm">Accurate location *</b><button type="button" onClick={useGPS} className="text-xs font-black text-blue-700"><FiMapPin className="inline" /> Use current GPS</button></div><div className="grid grid-cols-2 gap-3"><input required type="number" step="any" className="input-field" placeholder="Latitude" value={form.latitude} onChange={(e) => update("latitude",e.target.value)} /><input required type="number" step="any" className="input-field" placeholder="Longitude" value={form.longitude} onChange={(e) => update("longitude",e.target.value)} /></div></div>
      <div><h2 className="font-black">Route and planning information</h2><div className="grid md:grid-cols-3 gap-3 mt-3">{[['route_origin','Route starts from'],['transport_mode','Transportation mode'],['travel_time_minutes','Travel time (minutes)'],['distance_km','Distance (km)'],['road_condition','Road/trail condition'],['price_npr','Fare or price (NPR)']].map(([key,label]) => <label key={key} className="text-xs font-bold">{label}<input type={['travel_time_minutes','distance_km','price_npr'].includes(key)?'number':'text'} step="any" className="input-field mt-1" value={form[key]} onChange={(e) => update(key,e.target.value)} /></label>)}</div></div>
      <div className="grid sm:grid-cols-2 gap-3"><label className="rounded-2xl border-2 border-dashed p-5 text-center cursor-pointer"><FiCamera className="mx-auto" /> <b className="text-sm block">Photo evidence</b><span className="text-xs text-gray-400">{image?.name || "Choose image"}</span><input hidden type="file" accept="image/*" onChange={(e) => setImage(e.target.files[0])} /></label><label className="rounded-2xl border-2 border-dashed p-5 text-center cursor-pointer"><FiVideo className="mx-auto" /><b className="text-sm block">Video evidence</b><span className="text-xs text-gray-400">{video?.name || "Choose video"}</span><input hidden type="file" accept="video/*" onChange={(e) => setVideo(e.target.files[0])} /></label></div>
      <label className="text-xs font-bold">Source / verification notes<textarea className="input-field mt-1" value={form.source_notes} onChange={(e) => update("source_notes",e.target.value)} /></label>
      <button disabled={saving} className="rounded-xl bg-emerald-700 text-white px-7 py-3 font-black disabled:opacity-50"><FiSend className="inline mr-2" />{saving ? "Submitting…" : "Submit for admin review"}</button>
    </form>
  </div>
}
