import React, { useState, useEffect } from "react"
import { FiSearch, FiCheck, FiExternalLink, FiImage, FiEye, FiDownload, FiStar, FiFilter, FiRefreshCw } from "react-icons/fi"
import adminApi from "../../../api/adminApi"
import destinationApi from "../../../api/destinationApi"
import useToast from "../../../hooks/useToast"

const ALL_SOURCES = [
  { id: "wikimedia", label: "Wikimedia Commons", desc: "Authentic, licensed historical & landmark photos", color: "bg-blue-500/20 text-blue-300 border-blue-500/30" },
  { id: "openverse", label: "Openverse", desc: "Aggregated CC-licensed heritage & cultural media", color: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30" },
  { id: "flickr", label: "Flickr", desc: "Local community & contributor photography", color: "bg-pink-500/20 text-pink-300 border-pink-500/30" },
  { id: "unsplash", label: "Unsplash", desc: "High-resolution scenic & travel photography", color: "bg-purple-500/20 text-purple-300 border-purple-500/30" },
  { id: "pexels", label: "Pexels", desc: "Curated nature, landscapes & outdoor photography", color: "bg-amber-500/20 text-amber-300 border-amber-500/30" },
  { id: "pixabay", label: "Pixabay", desc: "Free high-quality travel photographs", color: "bg-teal-500/20 text-teal-300 border-teal-500/30" },
]

export default function ImageSearchImportPanel({ initialDestinationId = null, onImageImported = null }) {
  const { showToast } = useToast()

  const [destinations, setDestinations] = useState([])
  const [selectedDestId, setSelectedDestId] = useState(initialDestinationId || "")
  const [destName, setDestName] = useState("")
  const [district, setDistrict] = useState("")
  const [province, setProvince] = useState("")
  const [country, setCountry] = useState("Nepal")

  const [selectedSources, setSelectedSources] = useState(["wikimedia", "openverse", "flickr", "unsplash", "pexels", "pixabay"])
  const [isSearching, setIsSearching] = useState(false)
  const [results, setResults] = useState([])
  const [hasSearched, setHasSearched] = useState(false)
  const [previewItem, setPreviewItem] = useState(null)
  const [importingUrl, setImportingUrl] = useState(null)

  // Load destination options for the picker
  useEffect(() => {
    destinationApi.getDestinations({ page_size: 100 })
      .then(({ data }) => {
        const list = data.results || data || []
        setDestinations(list)
        if (initialDestinationId && !destName) {
          const found = list.find(d => String(d.id) === String(initialDestinationId))
          if (found) {
            setSelectedDestId(found.id)
            setDestName(found.name)
            setDistrict(found.district || "")
            setProvince(found.province || "")
          }
        }
      })
      .catch(() => {})
  }, [initialDestinationId])

  const handleDestinationSelect = (e) => {
    const val = e.target.value
    setSelectedDestId(val)
    if (!val) {
      return
    }
    const found = destinations.find(d => String(d.id) === String(val))
    if (found) {
      setDestName(found.name)
      setDistrict(found.district || "")
      setProvince(found.province || "")
    }
  }

  const toggleSource = (sourceId) => {
    setSelectedSources(prev =>
      prev.includes(sourceId)
        ? prev.filter(s => s !== sourceId)
        : [...prev, sourceId]
    )
  }

  const handleSearch = async (e) => {
    if (e) e.preventDefault()
    if (!destName.trim()) {
      showToast("Please enter a destination or search term", "error")
      return
    }
    if (selectedSources.length === 0) {
      showToast("Select at least one image source", "error")
      return
    }

    setIsSearching(true)
    setHasSearched(true)
    try {
      const payload = {
        destination_id: selectedDestId || null,
        query: destName.trim(),
        district: district.trim(),
        province: province.trim(),
        country: country.trim(),
        sources: selectedSources,
        limit: 30,
      }
      const { data } = await adminApi.searchMultiSourceImages(payload)
      setResults(data.results || [])
      if ((data.results || []).length === 0) {
        showToast("No images found with matching criteria. Try broader keywords.", "info")
      } else {
        showToast(`Found ${data.results.length} ranked images across ${selectedSources.length} sources`, "success")
      }
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to search images", "error")
    } finally {
      setIsSearching(false)
    }
  }

  const handleImport = async (item, asCover = false) => {
    if (!selectedDestId) {
      showToast("Please select a target destination to attach this image to", "error")
      return
    }

    setImportingUrl(item.url)
    try {
      const payload = {
        destination_id: selectedDestId,
        image_url: item.url,
        thumbnail_url: item.thumbnail || item.url,
        caption: item.title || `${destName} — ${item.source_title || item.source}`,
        source_platform: item.source,
        source_url: item.source_page_url || item.source_page || "",
        photographer: item.author || "",
        license_type: item.license || "CC BY-SA",
        attribution_requirement: item.attribution_requirement || "",
        dimensions: `${item.width || 0}x${item.height || 0}`,
        confidence_score: item.confidence_score || 90,
        is_cover: asCover,
      }
      const { data } = await adminApi.importMediaImage(payload)
      showToast(asCover ? "Image saved and set as primary destination cover!" : "Image added to destination gallery!", "success")
      if (onImageImported) {
        onImageImported(data)
      }
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to import image", "error")
    } finally {
      setImportingUrl(null)
    }
  }

  return (
    <div className="space-y-6">
      {/* Search Header Form */}
      <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-black uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                Multi-Source Search &amp; Import
              </span>
              <span className="text-xs text-slate-400">Authentic Provenance</span>
            </div>
            <h2 className="text-xl font-black text-white mt-1">Image Search &amp; Verification Studio</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Query 6 openly-licensed &amp; contributor photography sources with place-specific relevance scoring.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleSearch}
              disabled={isSearching}
              className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-black text-xs flex items-center gap-2 shadow-lg shadow-emerald-950/40 transition-all cursor-pointer"
            >
              {isSearching ? <FiRefreshCw className="animate-spin w-3.5 h-3.5" /> : <FiSearch className="w-3.5 h-3.5" />}
              {isSearching ? "Searching All Sources..." : "Search Images"}
            </button>
          </div>
        </div>

        {/* Inputs Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-5">
          <div>
            <label className="block text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              Destination / Sight
            </label>
            <input
              type="text"
              value={destName}
              onChange={(e) => setDestName(e.target.value)}
              placeholder="e.g. Rara Lake, Ilam Tea Garden"
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              District
            </label>
            <input
              type="text"
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              placeholder="e.g. Mugu, Ilam, Kaski"
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              Province
            </label>
            <input
              type="text"
              value={province}
              onChange={(e) => setProvince(e.target.value)}
              placeholder="e.g. Karnali, Koshi, Gandaki"
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              Link To DB Destination
            </label>
            <select
              value={selectedDestId}
              onChange={handleDestinationSelect}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none focus:border-emerald-500"
            >
              <option value="">-- Choose Existing Destination --</option>
              {destinations.map(d => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.district || "Nepal"})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Source Checkboxes matching mockup */}
        <div className="mt-5 pt-4 border-t border-slate-800">
          <p className="text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <FiFilter className="w-3.5 h-3.5 text-amber-400" /> Image Sources:
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
            {ALL_SOURCES.map(src => {
              const active = selectedSources.includes(src.id)
              return (
                <button
                  key={src.id}
                  type="button"
                  onClick={() => toggleSource(src.id)}
                  className={`p-2.5 rounded-xl border text-left transition-all cursor-pointer ${
                    active
                      ? `${src.color} shadow-sm font-black`
                      : "bg-slate-950/60 border-slate-800 text-slate-500 hover:text-slate-300 hover:bg-slate-800/40"
                  }`}
                >
                  <div className="flex items-center justify-between text-xs">
                    <span>{src.label}</span>
                    <span className={`w-3.5 h-3.5 rounded flex items-center justify-center text-[10px] ${active ? "bg-white text-slate-950" : "border border-slate-700"}`}>
                      {active ? "✓" : ""}
                    </span>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* Results Header */}
      {hasSearched && (
        <div className="flex items-center justify-between text-xs text-slate-400 px-1">
          <span>Found <b>{results.length}</b> verified results for &ldquo;{destName}&rdquo;</span>
          <span className="text-[11px] text-emerald-400">Higher match % indicates verified place specificity</span>
        </div>
      )}

      {/* Results Grid matching Mockup */}
      {results.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {results.map((item, idx) => {
            const isImporting = importingUrl === item.url
            return (
              <div
                key={item.url + idx}
                className="group rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden flex flex-col hover:border-emerald-500/50 hover:shadow-xl transition-all"
              >
                {/* Thumbnail Preview */}
                <div className="relative aspect-video bg-slate-950 overflow-hidden">
                  <img
                    src={item.thumbnail || item.url}
                    alt={item.title}
                    loading="lazy"
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    onError={(e) => { e.currentTarget.style.opacity = "0.4" }}
                  />
                  <div className="absolute top-2 left-2 flex flex-wrap gap-1">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-slate-900/80 text-white backdrop-blur border border-white/20">
                      {item.source}
                    </span>
                  </div>
                  <div className="absolute top-2 right-2">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-black tracking-wider border ${
                      item.confidence_score >= 80
                        ? "bg-emerald-500/90 text-white border-emerald-400"
                        : "bg-amber-500/90 text-white border-amber-400"
                    }`}>
                      {item.confidence_score}% Match
                    </span>
                  </div>
                </div>

                {/* Card Content */}
                <div className="p-3.5 flex-1 flex flex-col justify-between space-y-3">
                  <div>
                    <h4 className="text-xs font-bold text-white line-clamp-2" title={item.title}>
                      {item.title || "Nepal Landmark"}
                    </h4>
                    <p className="text-[11px] text-slate-400 mt-1 truncate" title={item.author}>
                      Author: <span className="text-slate-300">{item.author || "Unknown"}</span>
                    </p>
                    <p className="text-[10px] text-slate-400 truncate" title={item.license}>
                      License: <span className="text-emerald-400">{item.license}</span>
                    </p>
                  </div>

                  {/* Match Scores */}
                  <div className="space-y-1.5 bg-slate-950/60 p-2 rounded-xl border border-slate-800/80 text-[10px]">
                    <div className="flex justify-between items-center text-slate-300">
                      <span>Location Match:</span>
                      <span className="font-bold text-emerald-400">{item.location_match}%</span>
                    </div>
                    <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                      <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${item.location_match}%` }} />
                    </div>

                    <div className="flex justify-between items-center text-slate-300 pt-1">
                      <span>Keyword Match:</span>
                      <span className="font-bold text-amber-400">{item.keyword_match}%</span>
                    </div>
                    <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                      <div className="bg-amber-400 h-full rounded-full" style={{ width: `${item.keyword_match}%` }} />
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="grid grid-cols-3 gap-1.5 pt-1">
                    <button
                      type="button"
                      onClick={() => setPreviewItem(item)}
                      className="px-2 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-[11px] font-bold flex items-center justify-center gap-1 cursor-pointer"
                    >
                      <FiEye className="w-3 h-3" /> Preview
                    </button>
                    <button
                      type="button"
                      disabled={isImporting}
                      onClick={() => handleImport(item, false)}
                      className="px-2 py-1.5 rounded-lg bg-blue-600/30 hover:bg-blue-600 text-blue-300 hover:text-white border border-blue-500/40 text-[11px] font-bold flex items-center justify-center gap-1 cursor-pointer disabled:opacity-40"
                    >
                      <FiDownload className="w-3 h-3" /> Gallery
                    </button>
                    <button
                      type="button"
                      disabled={isImporting}
                      onClick={() => handleImport(item, true)}
                      className="px-2 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-black flex items-center justify-center gap-1 cursor-pointer shadow-md disabled:opacity-40"
                    >
                      <FiStar className="w-3 h-3" /> Cover
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Full Preview Modal */}
      {previewItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full p-5 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="text-sm font-black text-white">{previewItem.title || "Image Preview"}</h3>
                <p className="text-xs text-slate-400">Source: {previewItem.source_title} ({previewItem.source})</p>
              </div>
              <button
                type="button"
                onClick={() => setPreviewItem(null)}
                className="w-7 h-7 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center text-xs"
              >
                ✕
              </button>
            </div>

            <div className="rounded-xl overflow-hidden bg-black flex items-center justify-center max-h-[50vh]">
              <img
                src={previewItem.url}
                alt={previewItem.title}
                className="max-h-[50vh] max-w-full object-contain"
              />
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs bg-slate-950 p-3 rounded-xl border border-slate-800">
              <div>
                <p className="text-slate-400">Author / Photographer:</p>
                <p className="font-bold text-white">{previewItem.author || "Unknown"}</p>
              </div>
              <div>
                <p className="text-slate-400">License:</p>
                <p className="font-bold text-emerald-400">{previewItem.license}</p>
              </div>
              <div>
                <p className="text-slate-400">Attribution Notice:</p>
                <p className="text-slate-300 font-mono text-[10px] truncate">{previewItem.attribution_requirement}</p>
              </div>
              <div>
                <p className="text-slate-400">Original Source Page:</p>
                {previewItem.source_page ? (
                  <a href={previewItem.source_page} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline inline-flex items-center gap-1">
                    Visit Source <FiExternalLink className="w-3 h-3" />
                  </a>
                ) : (
                  <span className="text-slate-500">Not recorded</span>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setPreviewItem(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold cursor-pointer"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => { handleImport(previewItem, false); setPreviewItem(null) }}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold cursor-pointer"
              >
                Add to Destination Gallery
              </button>
              <button
                type="button"
                onClick={() => { handleImport(previewItem, true); setPreviewItem(null) }}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-black cursor-pointer"
              >
                Set as Primary Cover
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
