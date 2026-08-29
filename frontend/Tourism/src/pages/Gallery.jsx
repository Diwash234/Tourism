import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Link } from "react-router-dom"
import {
  FiImage, FiMaximize2, FiX, FiChevronLeft, FiChevronRight,
  FiMapPin, FiCompass, FiAward, FiExternalLink, FiSearch, FiFilter
} from "react-icons/fi"

const CATEGORY_FILTERS = [
  { id: "all", label: "All Photos (100+)" },
  { id: "mountain", label: "🏔️ Mountains & Alpine" },
  { id: "lake", label: "🌊 Lakes & Waters" },
  { id: "temple", label: "🏛️ Temples & Stupas" },
  { id: "wildlife", label: "🐅 Wildlife & Safaris" },
  { id: "heritage", label: "🏰 Heritage Cities" },
  { id: "landscape", label: "🌿 Landscapes & Hills" },
]

import destinationApi from "../api/destinationApi"
import { getDestinationImageUrl } from "../utils/imageUtils"

const normalizeGalleryCategory = (value = "") => {
  const category = String(value).toLowerCase()
  if (/(mountain|trek|peak|winter|viewpoint|hill)/.test(category)) return "mountain"
  if (/(lake|river|waterfall|water-sport|wetland)/.test(category)) return "lake"
  if (/(temple|buddhist|pilgrimage|stupa|monastery|spiritual)/.test(category)) return "temple"
  if (/(wildlife|bird|forest|national park|eco-tourism)/.test(category)) return "wildlife"
  if (/(heritage|museum|culture|historic|palace|city)/.test(category)) return "heritage"
  return "landscape"
}

export default function Gallery() {
  const [selectedCategory, setSelectedCategory] = useState("all")
  const [searchQuery, setSearchQuery] = useState("")
  const [destinationsMedia, setDestinationsMedia] = useState([])
  const [galleryLoading, setGalleryLoading] = useState(true)

  // Lightbox state
  const [activePhoto, setActivePhoto] = useState(null)
  const [activePhotoIndex, setActivePhotoIndex] = useState(0)
  const [flatPhotoList, setFlatPhotoList] = useState([])

  // Load real backend destinations into gallery
  useEffect(() => {
    destinationApi.getDestinations({ page_size: 100 })
      .then(({ data }) => {
        const list = data.results || data.items || data || []
        if (Array.isArray(list) && list.length > 0) {
          const existingNames = new Set()
          const dynamicEntries = []
          list.forEach((dest) => {
            if (!dest.name || existingNames.has(dest.name.toLowerCase())) return
            existingNames.add(dest.name.toLowerCase())
            const preview = Array.isArray(dest.gallery_preview) ? dest.gallery_preview : []
            const fallback = getDestinationImageUrl(dest)
            const manuallyCorrected = fallback && ["hot-air-balloon-pokhara", "ultralight-flight-pokhara", "zipflyer-pokhara", "chhoser-sky-caves", "gupteswor-gupha"].some((folder) => fallback.includes(`/${folder}/`))
            const images = manuallyCorrected
              ? [{ url: fallback, caption: dest.name, category: normalizeGalleryCategory(dest.category_name), source: "manual_correction" }]
              : preview.length ? preview.map((media) => ({
                  url: media.url,
                  caption: media.caption || dest.name,
                  category: normalizeGalleryCategory(dest.category_name),
                  photographer: media.photographer,
                  license: media.license,
                  source: media.source,
                  verification_status: media.verification_status,
                })) : (fallback ? [{ url: fallback, caption: dest.name, category: normalizeGalleryCategory(dest.category_name) }] : [])
            if (!images.length) return
            dynamicEntries.push({
              key: dest.slug || dest.id,
              name: dest.name,
              slug: dest.slug,
              location: `${dest.district || dest.city || "Nepal"}, ${dest.province || ""}`.replace(/, $/, ""),
              category: normalizeGalleryCategory(dest.category_name),
              tag: `🌿 Nepal Destination · ${images.length} image${images.length === 1 ? "" : "s"}`,
              description: dest.short_description || `Explore the landscape, culture and visitor highlights of ${dest.name}.`,
              images,
            })
          })
          setDestinationsMedia((current) => [...current.filter((entry) => String(entry.key).startsWith("featured-")), ...dynamicEntries, ...current.filter((entry) => String(entry.key).startsWith("district-"))])
        }
      })
      .catch(() => {})

    destinationApi.getFeaturedGallery()
      .then(({ data }) => {
        const featuredEntries = (data.results || []).map((dest) => {
          const preview = Array.isArray(dest.gallery_preview) ? dest.gallery_preview : []
          const fallback = getDestinationImageUrl(dest)
          const images = preview.length ? preview.map((media) => ({
            url: media.url, caption: media.caption || dest.name,
            category: normalizeGalleryCategory(dest.category_name),
            photographer: media.photographer, license: media.license,
            source: media.source, verification_status: media.verification_status,
          })) : fallback ? [{ url: fallback, caption: dest.name, category: normalizeGalleryCategory(dest.category_name) }] : []
          return {
            key: `featured-${dest.slug || dest.id}`, name: dest.name, slug: dest.slug,
            location: `${dest.district || dest.city || "Nepal"}, ${dest.province || ""}`.replace(/, $/, ""),
            category: normalizeGalleryCategory(dest.category_name),
            tag: `⭐ Featured Nepal Collection · ${images.length} image${images.length === 1 ? "" : "s"}`,
            description: dest.short_description || `A featured visual journey through ${dest.name}, its scenery, heritage and travel experiences.`,
            images,
          }
        }).filter((entry) => entry.images.length)
        setDestinationsMedia((current) => [...featuredEntries, ...current.filter((entry) => !String(entry.key).startsWith("featured-"))])
      })
      .catch(() => {})

    destinationApi.getDistrictGallery()
      .then(({ data }) => {
        const districtEntries = (data.districts || []).map((group) => ({
          key: `district-${group.district}`,
          name: `${group.district} District`,
          slug: group.images?.[0]?.destination_slug,
          location: `${group.district}, ${group.images?.[0]?.province || "Nepal"}`,
          category: normalizeGalleryCategory(group.images?.[0]?.category_name),
          tag: `🗺️ District Gallery · ${group.images.length} image${group.images.length === 1 ? "" : "s"}`,
          description: `Five source-attributed views representing destinations, landscapes and cultural places connected with ${group.district} District.`,
          images: group.images.map((media) => ({
            url: media.url, caption: media.caption || media.destination_name,
            category: normalizeGalleryCategory(media.category_name), photographer: media.photographer,
            license: media.license, source: media.source,
          })),
        }))
        setDestinationsMedia((current) => [...current.filter((entry) => !String(entry.key).startsWith("district-")), ...districtEntries])
      })
      .catch(() => {})
      .finally(() => setGalleryLoading(false))
  }, [])

  // Flatten all photos for lightbox navigation
  useEffect(() => {
    const all = []
    destinationsMedia.forEach((d) => {
      d.images.forEach((img) => {
        all.push({
          ...img,
          destinationName: d.name,
          slug: d.slug,
          location: d.location,
          photographer: img.photographer || "Source contributor",
          license: img.license || "See source record",
        })
      })
    })
    setFlatPhotoList(all)
  }, [destinationsMedia])

  const districtMedia = destinationsMedia.filter((dest) => String(dest.key).startsWith("district-") && dest.images.length)

  const filteredDestinations = destinationsMedia.filter((dest) => {
    const matchesCat = selectedCategory === "all" || dest.category === selectedCategory || dest.images.some(i => i.category === selectedCategory)
    const matchesSearch = !searchQuery.trim() || dest.name.toLowerCase().includes(searchQuery.toLowerCase()) || dest.location.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesCat && matchesSearch
  })

  const openLightbox = (photo, globalIndex) => {
    setActivePhoto(photo)
    setActivePhotoIndex(globalIndex)
  }

  const nextPhoto = () => {
    const nextIdx = (activePhotoIndex + 1) % flatPhotoList.length
    setActivePhotoIndex(nextIdx)
    setActivePhoto(flatPhotoList[nextIdx])
  }

  const prevPhoto = () => {
    const prevIdx = (activePhotoIndex - 1 + flatPhotoList.length) % flatPhotoList.length
    setActivePhotoIndex(prevIdx)
    setActivePhoto(flatPhotoList[prevIdx])
  }

  // Keyboard navigation for Lightbox
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!activePhoto) return
      if (e.key === "Escape") setActivePhoto(null)
      if (e.key === "ArrowRight") nextPhoto()
      if (e.key === "ArrowLeft") prevPhoto()
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [activePhoto, activePhotoIndex, flatPhotoList])

  return (
    <div className="container-app theme-indigo py-8 space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto space-y-2">
        <span className="px-3.5 py-1 rounded-full bg-purple-100 text-purple-800 text-xs font-black uppercase tracking-wider">
          Visual Media & Photo Story Archive
        </span>
        <h1 className="text-3xl sm:text-4xl font-black text-gray-900 flex items-center justify-center gap-2">
          📸 Nepal Destination Photography & Visual Stories
        </h1>
        <p className="text-sm text-gray-500">
          Explore destination-linked and source-attributed photographs from all 77 districts and 7 provinces. Imported and corrected media remains manageable through the Admin Image Dashboard.
        </p>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-purple-50/70 border border-purple-100 p-4 rounded-3xl">
        {/* Category Pills */}
        <div className="flex overflow-x-auto gap-2 w-full sm:w-auto no-scrollbar pb-1 sm:pb-0">
          {CATEGORY_FILTERS.map((f) => (
            <button
              key={f.id}
              onClick={() => setSelectedCategory(f.id)}
              className={`px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all ${
                selectedCategory === f.id
                  ? "bg-purple-700 text-white shadow-md shadow-purple-900/20"
                  : "bg-white text-gray-700 hover:bg-purple-100/60 border border-purple-200"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-64">
          <FiSearch className="absolute left-3.5 top-1/2 -translate-y-1/2 text-purple-400" size={15} />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by place or district..."
            className="w-full pl-10 pr-4 py-2 bg-white border border-purple-200 rounded-xl text-xs text-gray-900 placeholder-gray-400 focus:outline-none focus:border-purple-600 shadow-sm"
          />
        </div>
      </div>

      {galleryLoading && <div className="rounded-3xl bg-purple-50 border border-purple-100 p-10 text-center text-purple-800 font-bold animate-pulse">Loading destination, mountain, lake and 77-district photo collections…</div>}

      {/* 77-district moving visual index */}
      {districtMedia.length > 0 && (
        <section className="overflow-hidden rounded-3xl bg-slate-950 py-5 border border-purple-900/40">
          <div className="px-5 mb-4 flex items-center justify-between">
            <div><p className="text-[10px] uppercase tracking-widest text-purple-300 font-black">All Nepal District Visual Index</p><h2 className="text-white font-black text-xl">77 District Photo Marquee</h2></div>
            <span className="text-xs text-slate-400">5 images per district · swipe or browse below</span>
          </div>
          <motion.div
            className="flex gap-3 w-max px-3"
            animate={{ x: ["0%", "-50%"] }}
            transition={{ duration: 90, repeat: Infinity, ease: "linear" }}
          >
            {[...districtMedia, ...districtMedia].map((district, index) => (
              <button key={`${district.key}-${index}`} onClick={() => setSearchQuery(district.name.replace(" District", ""))} className="relative w-48 h-28 shrink-0 rounded-2xl overflow-hidden border border-white/10 group">
                <img src={district.images[index % district.images.length]?.url} alt={district.name} className="w-full h-full object-cover group-hover:scale-110 transition-transform" onError={(e)=>{e.currentTarget.style.display="none"}} />
                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/10" />
                <span className="absolute bottom-2 left-3 text-white text-xs font-black">{district.name}</span>
              </button>
            ))}
          </motion.div>
        </section>
      )}

      {/* Destination Collections Grid */}
      <div className="space-y-10">
        {filteredDestinations.map((dest) => (
          <div key={dest.key} className="space-y-3 bg-white p-6 rounded-3xl border border-purple-100 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-100 pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full bg-purple-100 text-purple-900 text-[10px] font-bold">
                    {dest.tag}
                  </span>
                  <span className="text-xs text-gray-500">• {dest.location}</span>
                </div>
                <h3 className="text-xl font-black text-gray-900 mt-1">{dest.name}</h3>
                {dest.description && <p className="text-xs text-gray-500 mt-1 max-w-3xl leading-relaxed">{dest.description}</p>}
              </div>

              <Link
                to={`/destinations/${dest.slug}`}
                className="px-4 py-2 rounded-xl bg-purple-700 hover:bg-purple-800 text-white font-bold text-xs inline-flex items-center gap-1.5 shadow transition-all self-start sm:self-auto"
              >
                <FiCompass size={14} /> Explore Destination ➔
              </Link>
            </div>

            {/* Photo Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
              {dest.images.map((img, idx) => {
                const globalIdx = flatPhotoList.findIndex((p) => p.url === img.url)
                return (
                  <motion.div
                    key={idx}
                    whileHover={{ scale: 1.02 }}
                    className="group relative rounded-2xl overflow-hidden bg-slate-900 shadow border border-gray-100 cursor-pointer flex flex-col justify-between"
                    onClick={() => openLightbox({
                      ...img,
                      destinationName: dest.name,
                      slug: dest.slug,
                      location: dest.location,
                      photographer: img.photographer || "Source contributor",
                      license: img.license || "See source record",
                    }, globalIdx)}
                  >
                    <div className="h-40 w-full relative overflow-hidden">
                      <img
                        src={img.url}
                        alt={img.caption}
                        loading="lazy"
                        onError={(e) => {
                          e.currentTarget.style.display = "none"
                        }}
                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-2.5">
                        <span className="text-[10px] font-bold text-amber-300 flex items-center gap-1">
                          <FiMaximize2 size={12} /> Click to Fullscreen
                        </span>
                      </div>
                    </div>

                    <div className="p-2 bg-white text-[11px] space-y-0.5">
                      <p className="font-bold text-gray-900 truncate">{img.caption}</p>
                      <p className="text-[9px] text-emerald-600 font-mono truncate">{img.license || "Source attribution available"}</p>
                    </div>
                  </motion.div>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      {/* FULLSCREEN LIGHTBOX MODAL */}
      <AnimatePresence>
        {activePhoto && (
          <div className="fixed inset-0 z-50 bg-black/95 flex flex-col justify-between p-4 sm:p-6 backdrop-blur-md">
            {/* Header */}
            <div className="flex items-center justify-between text-white border-b border-white/10 pb-3">
              <div className="space-y-0.5">
                <span className="font-black text-lg text-amber-300">{activePhoto.destinationName}</span>
                <p className="text-xs text-gray-300">
                  {activePhoto.caption} · <b>Photographer:</b> {activePhoto.photographer} · <b>License:</b> <span className="text-emerald-400">{activePhoto.license}</span>
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Link
                  to={`/destinations/${activePhoto.slug}`}
                  className="px-3.5 py-1.5 rounded-xl bg-purple-700 hover:bg-purple-800 text-white font-bold text-xs flex items-center gap-1"
                >
                  <FiCompass size={13} /> View Place Details
                </Link>
                <button
                  onClick={() => setActivePhoto(null)}
                  className="p-2 rounded-full bg-white/20 hover:bg-white/40 text-white transition-all"
                >
                  <FiX size={24} />
                </button>
              </div>
            </div>

            {/* Main Center Image */}
            <div className="flex-1 flex items-center justify-center relative my-3">
              <img
                src={activePhoto.url}
                alt={activePhoto.caption}
                onError={(e) => {
                  e.currentTarget.style.display = "none"
                }}
                className="max-h-[76vh] max-w-full object-contain rounded-2xl shadow-2xl"
              />
              <button
                onClick={prevPhoto}
                className="absolute left-2 sm:left-6 p-4 rounded-full bg-black/60 hover:bg-black/90 text-white backdrop-blur transition-all"
              >
                <FiChevronLeft size={28} />
              </button>
              <button
                onClick={nextPhoto}
                className="absolute right-2 sm:right-6 p-4 rounded-full bg-black/60 hover:bg-black/90 text-white backdrop-blur transition-all"
              >
                <FiChevronRight size={28} />
              </button>
            </div>

            {/* Bottom Navigation Strip */}
            <div className="flex gap-2 overflow-x-auto justify-center pb-2 no-scrollbar">
              {flatPhotoList.map((p, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setActivePhotoIndex(i)
                    setActivePhoto(p)
                  }}
                  className={`w-14 h-10 rounded-lg overflow-hidden shrink-0 border-2 transition-all ${
                    activePhotoIndex === i ? "border-amber-400 scale-110 shadow-lg" : "border-transparent opacity-40 hover:opacity-80"
                  }`}
                >
                  <img
                    src={p.url}
                    alt={`Thumb ${i}`}
                    onError={(e) => {
                      e.currentTarget.style.display = "none"
                    }}
                    className="w-full h-full object-cover"
                  />
                </button>
              ))}
            </div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
