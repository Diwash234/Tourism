import { useState, useEffect, useMemo, useCallback } from "react"
import PageHeader from "../components/common/PageHeader"
import { motion, AnimatePresence } from "framer-motion"
import { Link } from "react-router-dom"
import {
  FiMaximize2, FiX, FiChevronLeft, FiChevronRight,
  FiCompass, FiSearch, FiCamera,
} from "react-icons/fi"
import EmptyState from "../components/common/EmptyState"
import PlaceholderImage from "../components/common/PlaceholderImage"
import SkeletonLoader from "../components/common/SkeletonLoader"

const CATEGORY_FILTERS = [
  { id: "all", label: "All photos" },
  { id: "mountain", label: "Mountains & alpine" },
  { id: "lake", label: "Lakes & waters" },
  { id: "temple", label: "Temples & stupas" },
  { id: "wildlife", label: "Wildlife" },
  { id: "heritage", label: "Heritage" },
  { id: "landscape", label: "Landscapes & hills" },
]

import destinationApi from "../api/destinationApi"
import usePublicConfig from "../hooks/usePublicConfig"
import CMSIntro from "../components/cms/CMSIntro"
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
  const { block: cmsBlock } = usePublicConfig().pageCMS("gallery", ["intro", "page-intro"])
  const [selectedCategory, setSelectedCategory] = useState("all")
  const [searchQuery, setSearchQuery] = useState("")
  const [destinationsMedia, setDestinationsMedia] = useState([])
  const [galleryLoading, setGalleryLoading] = useState(true)
  const [galleryError, setGalleryError] = useState(false)
  const [galleryRetry, setGalleryRetry] = useState(0)

  // Lightbox state
  const [activePhoto, setActivePhoto] = useState(null)
  const [activePhotoIndex, setActivePhotoIndex] = useState(0)

  // Load real backend destinations into gallery
  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => {
    setGalleryError(false)
    setDestinationsMedia([])
    let pendingRequests = 3
    const finishRequest = () => {
      pendingRequests -= 1
      if (pendingRequests === 0) setGalleryLoading(false)
    }
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
      .catch(() => setGalleryError(true)).finally(finishRequest)

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
      .catch(() => setGalleryError(true)).finally(finishRequest)

    destinationApi.getDistrictGallery()
      .then(({ data }) => {
        const districtEntries = (data.districts || []).map((group) => ({
          key: `district-${group.district}`,
          name: `${group.district} District`,
          slug: group.images?.[0]?.destination_slug,
          location: `${group.district}, ${group.images?.[0]?.province || "Nepal"}`,
          category: normalizeGalleryCategory(group.images?.[0]?.category_name),
          tag: `🗺️ District Gallery · ${group.images.length} image${group.images.length === 1 ? "" : "s"}`,
          description: `${group.images.length} source-attributed ${group.images.length === 1 ? "view" : "views"} representing destinations, landscapes and cultural places connected with ${group.district} District.`,
          images: group.images.map((media) => ({
            url: media.url, caption: media.caption || media.destination_name,
            category: normalizeGalleryCategory(media.category_name), photographer: media.photographer,
            license: media.license, source: media.source,
          })),
        }))
        setDestinationsMedia((current) => [...current.filter((entry) => !String(entry.key).startsWith("district-")), ...districtEntries])
      })
      .catch(() => setGalleryError(true)).finally(finishRequest)
    }, 0)
    return () => clearTimeout(t)
  }, [galleryRetry])

  const districtMedia = destinationsMedia.filter((dest) => String(dest.key).startsWith("district-") && dest.images.length)
  const districtImageCount = districtMedia.reduce((sum, dest) => sum + dest.images.length, 0)
  const averageDistrictImages = districtMedia.length ? Math.round(districtImageCount / districtMedia.length) : 0

  const filteredDestinations = destinationsMedia.map((dest) => {
    const matchesSearch = !searchQuery.trim() || dest.name.toLowerCase().includes(searchQuery.toLowerCase()) || dest.location.toLowerCase().includes(searchQuery.toLowerCase())
    const images = selectedCategory === "all"
      ? dest.images
      : dest.images.filter((image) => image.category === selectedCategory || normalizeGalleryCategory(image.caption) === selectedCategory)
    return matchesSearch && images.length ? { ...dest, images } : null
  }).filter(Boolean)

  const visibleFlatPhotoList = useMemo(() => filteredDestinations.flatMap((dest) => dest.images.map((image) => ({
    ...image,
    destinationName: dest.name,
    slug: dest.slug,
    location: dest.location,
    photographer: image.photographer || "Attribution unavailable",
    license: image.license || "License information unavailable",
  }))), [filteredDestinations])

  const openLightbox = (photo) => {
    const index = visibleFlatPhotoList.findIndex((item) => item.url === photo.url)
    setActivePhoto(photo)
    setActivePhotoIndex(index >= 0 ? index : 0)
  }

  const nextPhoto = useCallback(() => {
    if (!visibleFlatPhotoList.length) return
    const nextIdx = (activePhotoIndex + 1) % visibleFlatPhotoList.length
    setActivePhotoIndex(nextIdx)
    setActivePhoto(visibleFlatPhotoList[nextIdx])
  }, [activePhotoIndex, visibleFlatPhotoList, setActivePhotoIndex, setActivePhoto])

  const prevPhoto = useCallback(() => {
    if (!visibleFlatPhotoList.length) return
    const prevIdx = (activePhotoIndex - 1 + visibleFlatPhotoList.length) % visibleFlatPhotoList.length
    setActivePhotoIndex(prevIdx)
    setActivePhoto(visibleFlatPhotoList[prevIdx])
  }, [activePhotoIndex, visibleFlatPhotoList, setActivePhotoIndex, setActivePhoto])

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
  }, [activePhoto, nextPhoto, prevPhoto])

  return (
    <div className="ny-page container-app space-y-8 py-6 sm:py-8">
      <CMSIntro section={cmsBlock("intro")} />
      <header className="max-w-3xl">
        <span className="ny-kicker">Visual stories</span>
        <PageHeader title="Nepal in photographs" subtitle="Browse destination-linked images from the Nepal Yatra media library. Search by place, filter by subject, and open a photo for its available attribution details." icon={FiCamera} />
      </header>

      {/* Filter Bar */}
      <section className="ny-panel p-4 sm:p-5" aria-label="Gallery filters"><div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between"><div className="ny-horizontal-scroll flex w-full gap-2 lg:w-auto" role="tablist" aria-label="Photo categories">{CATEGORY_FILTERS.map((filter) => <button key={filter.id} type="button" role="tab" aria-controls="gallery-results" aria-selected={selectedCategory === filter.id} onClick={() => setSelectedCategory(filter.id)} className={`min-h-10 whitespace-nowrap rounded-full border px-3.5 text-sm font-semibold transition ${selectedCategory === filter.id ? "border-[var(--ny-green)] bg-[var(--ny-green)] text-white" : "border-[var(--ny-border)] bg-white text-[var(--ny-text-secondary)] hover:bg-[var(--ny-soft-green)] hover:text-[var(--ny-green)]"}`}>{filter.label}</button>)}</div><div className="relative w-full lg:w-72"><FiSearch size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--ny-text-muted)]" aria-hidden="true" /><label htmlFor="gallery-search" className="sr-only">Search photos</label><input id="gallery-search" value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder="Search by place or district" className="input-field pl-10" /></div></div></section>

      {galleryLoading && <SkeletonLoader count={6} type="card" />}
      {galleryError && <div role="alert" className="ny-panel flex flex-col gap-3 border-[#E9D39A] bg-[var(--ny-soft-gold)] p-4 text-sm text-[var(--ny-warning)] sm:flex-row sm:items-center sm:justify-between"><span>Some gallery sources could not be loaded. Available photos are still shown below.</span><button type="button" onClick={() => setGalleryRetry((value) => value + 1)} className="ny-btn ny-btn-secondary min-h-11 shrink-0">Retry gallery</button></div>}

      {/* 77-district moving visual index */}
      {districtMedia.length > 0 && (
        <section className="overflow-hidden rounded-3xl bg-slate-950 py-5 border border-purple-900/40">
          <div className="px-5 mb-4 flex items-center justify-between">
            <div><p className="text-[10px] uppercase tracking-widest text-purple-300 font-black">All Nepal District Visual Index</p><h2 className="text-white font-black text-xl">77 District Photo Marquee</h2></div>
            <span className="text-xs text-slate-400">{averageDistrictImages ? `${averageDistrictImages} images per district on average` : "District photo index"} · swipe or browse below</span>
          </div>
          <motion.div
            className="flex gap-3 w-max px-3"
            animate={{ x: ["0%", "-50%"] }}
            transition={{ duration: 90, repeat: Infinity, ease: "linear" }}
          >
            {[...districtMedia, ...districtMedia].map((district, index) => (
              <button key={`${district.key}-${index}`} onClick={() => setSearchQuery(district.name.replace(" District", ""))} className="relative w-48 h-28 shrink-0 rounded-2xl overflow-hidden border border-white/10 group">
                <PlaceholderImage src={district.images[index % district.images.length]?.url} title={district.name} alt={district.name} className="h-full w-full transition-transform group-hover:scale-110" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/10" />
                <span className="absolute bottom-2 left-3 text-white text-xs font-black">{district.name}</span>
              </button>
            ))}
          </motion.div>
        </section>
      )}

      {!galleryLoading && filteredDestinations.length === 0 && <EmptyState title="No photos found" subtitle="No published photos match this category or search yet." action={<button type="button" onClick={() => { setSelectedCategory("all"); setSearchQuery("") }} className="ny-btn ny-btn-primary">Clear gallery filters</button>} />}

      {filteredDestinations.length > 0 && <div id="gallery-results" role="tabpanel" aria-label="Photo results" className="space-y-10">
        {filteredDestinations.map((dest) => (
          <div key={dest.key} className="space-y-3 bg-white p-6 rounded-3xl border border-[#E5E0D5] shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-100 pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-[#102A2E] text-[10px] font-bold">
                    {dest.tag}
                  </span>
                  <span className="text-xs text-gray-500">• {dest.location}</span>
                </div>
                <h3 className="text-xl font-black text-gray-900 mt-1">{dest.name}</h3>
                {dest.description && <p className="text-xs text-gray-500 mt-1 max-w-3xl leading-relaxed">{dest.description}</p>}
              </div>

              {dest.slug ? (
                <Link
                  to={`/destinations/${dest.slug}`}
                  className="ny-btn ny-btn-primary min-h-11 self-start text-xs sm:self-auto"
                >
                  <FiCompass size={14} aria-hidden="true" /> Explore destination
                </Link>
              ) : (
                <span className="self-start text-sm text-[var(--ny-text-muted)] sm:self-auto">Destination link unavailable</span>
              )}
            </div>

            {/* Photo Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
              {dest.images.map((img, idx) => {
                return (
                  <button
                    type="button"
                    key={idx}
                    aria-label={`Open photo: ${img.caption || dest.name}`}
                    className="group relative flex flex-col justify-between overflow-hidden rounded-[var(--ny-radius-md)] border border-[var(--ny-border)] bg-slate-900 text-left shadow-[var(--ny-shadow)]"
                    onClick={() => openLightbox({
                      ...img,
                      destinationName: dest.name,
                      slug: dest.slug,
                      location: dest.location,
                      photographer: img.photographer || "Attribution unavailable",
                      license: img.license || "License information unavailable",
                    })}
                  >
                    <div className="h-40 w-full relative overflow-hidden">
                      <PlaceholderImage
                        src={img.url}
                        title={img.caption || dest.name}
                        alt={img.caption || dest.name}
                        className="h-full w-full transition-transform duration-500 group-hover:scale-110"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-2.5">
                        <span className="text-[10px] font-bold text-amber-300 flex items-center gap-1">
                          <FiMaximize2 size={12} /> Click to Fullscreen
                        </span>
                      </div>
                    </div>

                    <div className="p-2 bg-white text-[11px] space-y-0.5">
                      <p className="font-bold text-gray-900 truncate">{img.caption}</p>
                      <p className="text-[9px] text-emerald-600 font-mono truncate">{img.license || "Attribution unavailable"}</p>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
        ))}
      </div>}

      {/* FULLSCREEN LIGHTBOX MODAL */}
      <AnimatePresence>
        {activePhoto && (
          <div className="fixed inset-0 z-[90] flex flex-col justify-between bg-black/95 p-4 backdrop-blur-md sm:p-6" role="dialog" aria-modal="true" aria-label="Photo viewer">
            {/* Header */}
            <div className="flex flex-col items-start gap-3 text-white border-b border-white/10 pb-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="space-y-0.5">
                <span className="font-black text-lg text-amber-300">{activePhoto.destinationName}</span>
                <p className="text-xs text-gray-300">
                  {activePhoto.caption} · <b>Photographer:</b> {activePhoto.photographer} · <b>License:</b> <span className="text-emerald-400">{activePhoto.license}</span>
                </p>
              </div>
              <div className="flex items-center gap-3">
                {activePhoto.slug ? <Link
                  to={`/destinations/${activePhoto.slug}`}
                  className="ny-btn ny-btn-primary min-h-11 text-xs"
                >
                  <FiCompass size={13} aria-hidden="true" /> View place details
                </Link> : <span className="text-xs text-white/70">Place link unavailable</span>}
                <button
                  type="button"
                  aria-label="Close photo viewer"
                  onClick={() => setActivePhoto(null)}
                  className="grid h-11 w-11 place-items-center rounded-[var(--ny-radius-sm)] text-white transition hover:bg-white/20"
                >
                  <FiX size={24} aria-hidden="true" />
                </button>
              </div>
            </div>

            {/* Main Center Image */}
            <div className="flex-1 flex items-center justify-center relative my-3">
              <PlaceholderImage
                src={activePhoto.url}
                title={activePhoto.destinationName}
                alt={activePhoto.caption}
                className="max-h-[76vh] max-w-full !object-contain rounded-2xl shadow-2xl"
              />
              <button
                type="button"
                aria-label="Previous photo"
                onClick={prevPhoto}
                className="absolute left-2 grid h-12 w-12 place-items-center rounded-full bg-black/60 text-white backdrop-blur transition hover:bg-black/90 sm:left-6"
              >
                <FiChevronLeft size={28} />
              </button>
              <button
                type="button"
                aria-label="Next photo"
                onClick={nextPhoto}
                className="absolute right-2 grid h-12 w-12 place-items-center rounded-full bg-black/60 text-white backdrop-blur transition hover:bg-black/90 sm:right-6"
              >
                <FiChevronRight size={28} />
              </button>
            </div>

            {/* Bottom Navigation Strip */}
            <div className="flex gap-2 overflow-x-auto justify-center pb-2 no-scrollbar">
              {visibleFlatPhotoList.map((p, i) => (
                <button
                  key={i}
                  type="button"
                  aria-label={`Open photo ${i + 1}`}
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
