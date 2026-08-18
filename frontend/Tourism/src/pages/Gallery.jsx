import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Link } from "react-router-dom"
import {
  FiImage, FiMaximize2, FiX, FiChevronLeft, FiChevronRight,
  FiMapPin, FiCompass, FiAward, FiExternalLink, FiSearch, FiFilter
} from "react-icons/fi"

const DESTINATIONS_MEDIA = [
  {
    key: "annapurna",
    name: "Annapurna Sanctuary & ABC",
    slug: "annapurna-base-camp-abc-sanctuary",
    location: "Kaski, Gandaki Province",
    category: "mountain",
    tag: "🏔️ Mountains & Alpine",
    images: [
      { url: "/images/destinations/everest/base-camp.jpg", caption: "Annapurna Base Camp Amphitheater", category: "mountain" },
      { url: "/images/destinations/tilicho/himalayan-lake.jpg", caption: "Machhapuchhre (Fishtail) Sunrise", category: "mountain" },
      { url: "/images/destinations/everest/base-camp.jpg", caption: "Alpine Valley Hiking Trail", category: "mountain" },
      { url: "/images/destinations/boudhanath/stupa.jpg", caption: "Glacial Stream & Suspension Bridge", category: "nature" },
      { url: "/images/destinations/everest/base-camp.jpg", caption: "Snow-Capped Annapurna South Peak", category: "mountain" },
    ]
  },
  {
    key: "everest",
    name: "Everest Base Camp & Khumbu",
    slug: "everest-base-camp-ebc",
    location: "Solukhumbu, Koshi Province",
    category: "mountain",
    tag: "🏔️ Mountains & Alpine",
    images: [
      { url: "/images/destinations/everest/base-camp.jpg", caption: "Mt. Everest (8,848m) High Summit", category: "mountain" },
      { url: "/images/destinations/pokhara/fewatal.jpg", caption: "Namche Bazaar Sherpa Capital", category: "village" },
      { url: "/images/destinations/everest/base-camp.jpg", caption: "Tengboche Monastery with Everest Backdrop", category: "temple" },
      { url: "/images/destinations/everest/base-camp.jpg", caption: "Khumbu Glacier & Icefall", category: "nature" },
      { url: "/images/destinations/rara/alpine-lake.jpg", caption: "Prayer Flags at Kala Patthar (5,545m)", category: "mountain" },
    ]
  },
  {
    key: "pokhara",
    name: "Pokhara & Phewa Lake",
    slug: "phewa-lake-tal-barahi",
    location: "Kaski, Gandaki Province",
    category: "lake",
    tag: "🌊 Lakes & Waters",
    images: [
      { url: "/images/destinations/pokhara/fewatal.jpg", caption: "Phewa Lake with Colorful Wooden Boats", category: "lake" },
      { url: "/images/destinations/manakamana/temple.jpg", caption: "Tal Barahi Island Temple at Sunset", category: "temple" },
      { url: "/images/destinations/everest/base-camp.jpg", caption: "Sarangkot Sunrise Mountain View", category: "viewpoint" },
      { url: "/images/destinations/pokhara/fewatal.jpg", caption: "Paragliding over Lakeside Pokhara", category: "adventure" },
      { url: "/images/destinations/koshi-tappu/wetlands.jpg", caption: "World Peace Pagoda Overlook", category: "temple" },
    ]
  },
  {
    key: "mustang",
    name: "Upper Mustang & Lo Manthang",
    slug: "upper-mustang-lo-manthang",
    location: "Mustang, Gandaki Province",
    category: "landscape",
    tag: "🏜️ High Altitude Deserts",
    images: [
      { url: "/images/destinations/ghandruk/village.jpg", caption: "Walled Kingdom of Lo Manthang", category: "heritage" },
      { url: "/images/destinations/davis-falls/waterfall.jpg", caption: "Red Clay Canyon Cliffs & Caves", category: "landscape" },
      { url: "/images/destinations/gorkha/durbar.jpg", caption: "Ancient Tibetan Chortens", category: "temple" },
      { url: "/images/destinations/ghandruk/village.jpg", caption: "Kali Gandaki River Valley", category: "landscape" },
      { url: "/images/destinations/gosaikunda/glacial-lake.jpg", caption: "Horse Caravans along Tibetan Border", category: "culture" },
    ]
  },
  {
    key: "rara",
    name: "Rara Lake & National Park",
    slug: "rara-lake-national-park",
    location: "Mugu, Karnali Province",
    category: "lake",
    tag: "🌊 Lakes & Waters",
    images: [
      { url: "/images/destinations/pokhara/fewatal.jpg", caption: "Crystal Turquoise Waters of Rara Lake", category: "lake" },
      { url: "/images/destinations/pokhara/fewatal.jpg", caption: "Pine Forests Surrounding the Lake", category: "nature" },
      { url: "/images/destinations/ilam/tea-gardens.jpg", caption: "Murma Top Viewpoint Panorama", category: "viewpoint" },
      { url: "/images/destinations/kanchenjunga/peak.jpg", caption: "Wildflowers & Meadow Horse Riding", category: "landscape" },
      { url: "/images/destinations/pokhara/fewatal.jpg", caption: "Morning Mist over Rara Mirror Lake", category: "lake" },
    ]
  },
  {
    key: "chitwan",
    name: "Chitwan National Park Safari",
    slug: "chitwan-national-park-safari",
    location: "Sauraha, Chitwan",
    category: "wildlife",
    tag: "🐅 Wildlife & Safaris",
    images: [
      { url: "/images/destinations/chitwan/safari.jpg", caption: "One-Horned Rhinoceros in Grasslands", category: "wildlife" },
      { url: "/images/destinations/pashupatinath/main-temple.jpg", caption: "Rapti River Sunset Canoe Ride", category: "lake" },
      { url: "/images/destinations/chitwan/safari.jpg", caption: "Bengal Tiger Track Safari", category: "wildlife" },
      { url: "/images/destinations/koshi-tappu/wetlands.jpg", caption: "Tharu Cultural Stick Dance Performance", category: "culture" },
      { url: "/images/destinations/annapurna/trek.jpg", caption: "Gharial Crocodile Sanctuary", category: "wildlife" },
    ]
  },
  {
    key: "lumbini",
    name: "Lumbini Sacred Garden & Maya Devi",
    slug: "lumbini-sacred-garden-maya-devi-temple",
    location: "Rupandehi, Lumbini Province",
    category: "temple",
    tag: "🏛️ Spiritual & UNESCO Heritage",
    images: [
      { url: "/images/destinations/manakamana/temple.jpg", caption: "Maya Devi Temple & Sacred Pond", category: "temple" },
      { url: "/images/destinations/kathmandu/durbar-square.jpg", caption: "Emperor Ashoka Pillar Inscription", category: "heritage" },
      { url: "/images/destinations/manakamana/temple.jpg", caption: "World Peace Pagoda Lumbini", category: "temple" },
      { url: "/images/destinations/chitwan/safari.jpg", caption: "Eternal Peace Flame", category: "culture" },
      { url: "/images/destinations/patan/durbar-square.jpg", caption: "Monastic Zone Architecture", category: "temple" },
    ]
  },
  {
    key: "bhaktapur",
    name: "Bhaktapur Durbar Square",
    slug: "bhaktapur-durbar-square",
    location: "Bhaktapur, Bagmati Province",
    category: "heritage",
    tag: "🏛️ Spiritual & UNESCO Heritage",
    images: [
      { url: "/images/destinations/kathmandu/durbar-square.jpg", caption: "55-Window Palace & Golden Gate", category: "heritage" },
      { url: "/images/destinations/manakamana/temple.jpg", caption: "Nyatapola 5-Story Pagoda Temple", category: "temple" },
      { url: "/images/destinations/kathmandu/durbar-square.jpg", caption: "Pottery Square Clay Artisans", category: "culture" },
      { url: "/images/destinations/kathmandu/durbar-square.jpg", caption: "Dattatreya Square Ancient Wood Carvings", category: "heritage" },
      { url: "/images/destinations/rani-mahal/palace.jpg", caption: "Traditional Newari Brick Courtyards", category: "culture" },
    ]
  },
  {
    key: "patan",
    name: "Patan Durbar Square",
    slug: "patan-durbar-square",
    location: "Lalitpur, Bagmati Province",
    category: "heritage",
    tag: "🏛️ Spiritual & UNESCO Heritage",
    images: [
      { url: "/images/destinations/manakamana/temple.jpg", caption: "Krishna Mandir Stone Pagoda Architecture", category: "temple" },
      { url: "/images/destinations/manakamana/temple.jpg", caption: "Golden Temple (Hiranya Varna Mahavihar)", category: "temple" },
      { url: "/images/destinations/kathmandu/durbar-square.jpg", caption: "Patan Museum Courtyard & Bronzes", category: "heritage" },
      { url: "/images/destinations/kanchenjunga/peak.jpg", caption: "Mul Chowk Royal Bath Tusha Hiti", category: "heritage" },
      { url: "/images/destinations/kathmandu/durbar-square.jpg", caption: "Evening Oil Lamps at Durbar Square", category: "culture" },
    ]
  },
  {
    key: "janakpur",
    name: "Janakpurdham & Janaki Mandir",
    slug: "janakpurdham-janaki-mandir",
    location: "Dhanusha, Madhesh Province",
    category: "temple",
    tag: "🏛️ Spiritual & UNESCO Heritage",
    images: [
      { url: "/images/destinations/manakamana/temple.jpg", caption: "Grand Janaki Temple (Naulakha Mandir)", category: "temple" },
      { url: "/images/destinations/bhote-koshi/rafting.jpg", caption: "Mithila Folk Painting Murals", category: "culture" },
      { url: "/images/destinations/manakamana/temple.jpg", caption: "Ganga Sagar Holy Bathing Ghat", category: "lake" },
      { url: "/images/destinations/manakamana/temple.jpg", caption: "Dhanush Sagar Temple Reflection", category: "temple" },
      { url: "/images/destinations/patan/durbar.jpg", caption: "Vivah Mandap Monument", category: "culture" },
    ]
  },
  {
    key: "ilam",
    name: "Ilam Tea Gardens & Kanyam",
    slug: "ilam-tea-gardens-kanyam",
    location: "Ilam, Koshi Province",
    category: "landscape",
    tag: "🌿 Tea Gardens & Landscapes",
    images: [
      { url: "/images/destinations/ilam/tea-gardens.jpg", caption: "Rolling Green Slopes of Kanyam Tea Estate", category: "landscape" },
      { url: "/images/destinations/ilam/tea-gardens.jpg", caption: "Horse Riding across Tea Plantations", category: "adventure" },
      { url: "/images/destinations/everest/base-camp.jpg", caption: "Antu Danda Sunrise & Mt. Kanchenjunga", category: "viewpoint" },
      { url: "/images/destinations/ghandruk/village.jpg", caption: "Mai Pokhari Sacred Ramsar Wetland", category: "lake" },
      { url: "/images/destinations/ilam/tea-gardens.jpg", caption: "Fresh Orthodox Tea Plucking Experience", category: "culture" },
    ]
  },
  {
    key: "nagarkot",
    name: "Nagarkot Himalayan Viewpoint",
    slug: "nagarkot-himalayan-sunrise-viewpoint",
    location: "Bhaktapur/Kavre, Bagmati Province",
    category: "viewpoint",
    tag: "🏔️ Mountains & Alpine",
    images: [
      { url: "/images/destinations/everest/base-camp.jpg", caption: "Nagarkot Sunrise over the Himalayan Range", category: "viewpoint" },
      { url: "/images/destinations/everest/base-camp.jpg", caption: "View of 8 Himalayan Ranges from Tower", category: "mountain" },
      { url: "/images/destinations/everest/base-camp.jpg", caption: "Pine Forest Nature Walking Trails", category: "nature" },
      { url: "/images/destinations/ghandruk/village.jpg", caption: "Terraced Farmlands & Valley Clouds", category: "landscape" },
      { url: "/images/destinations/bhaktapur/durbar.jpg", caption: "Evening Golden Hour over Langtang", category: "viewpoint" },
    ]
  },
  {
    key: "tilicho",
    name: "Tilicho Lake (4,919m)",
    slug: "tilicho-lake-trek",
    location: "Manang, Gandaki Province",
    category: "lake",
    tag: "🌊 Lakes & Waters",
    images: [
      { url: "/images/destinations/pokhara/fewatal.jpg", caption: "One of the Highest Lakes in the World", category: "lake" },
      { url: "/images/destinations/pokhara/fewatal.jpg", caption: "Tilicho Peak (7,134m) Glacial Backdrop", category: "mountain" },
      { url: "/images/destinations/everest/base-camp.jpg", caption: "High Landslide Scree Slope Trail", category: "adventure" },
      { url: "/images/destinations/pokhara/fewatal.jpg", caption: "Deep Indigo Blue Alpine Water", category: "lake" },
      { url: "/images/destinations/pokhara/fewatal.jpg", caption: "Tilicho Base Camp Teahouses", category: "village" },
    ]
  },
  {
    key: "bandipur",
    name: "Bandipur Heritage Hill Station",
    slug: "bandipur-heritage-hill-station",
    location: "Tanahun, Gandaki Province",
    category: "heritage",
    tag: "🏡 Heritage Hill Stations",
    images: [
      { url: "/images/destinations/patan/durbar.jpg", caption: "Preserved 18th-Century Newari Main Street", category: "heritage" },
      { url: "/images/destinations/manakamana/temple.jpg", caption: "Thani Mai Temple Sunrise Ridge", category: "viewpoint" },
      { url: "/images/destinations/davis-falls/waterfall.jpg", caption: "Siddha Cave (Largest Cave in Nepal)", category: "nature" },
      { url: "/images/destinations/pashupatinath/main-temple.jpg", caption: "Traditional Carved Wooden Balconies", category: "culture" },
      { url: "/images/destinations/everest/base-camp.jpg", caption: "Silkworm Farm & Mountain Overlook", category: "landscape" },
    ]
  },
  {
    key: "bardiya",
    name: "Bardiya National Park",
    slug: "bardiya-national-park",
    location: "Bardiya, Lumbini Province",
    category: "wildlife",
    tag: "🐅 Wildlife & Safaris",
    images: [
      { url: "/images/destinations/chitwan/safari.jpg", caption: "Wild Royal Bengal Tiger in Riverbank", category: "wildlife" },
      { url: "/images/destinations/ghandruk/village.jpg", caption: "Karnali River Rafting & Gangetic Dolphins", category: "lake" },
      { url: "/images/destinations/chitwan/safari.jpg", caption: "Wild Asian Elephant Herd", category: "wildlife" },
      { url: "/images/destinations/manaslu/mountain-peak.jpg", caption: "Untamed Sal Hardwood Forests", category: "nature" },
      { url: "/images/destinations/annapurna/trek.jpg", caption: "Tharu Indigenous Community Homestay", category: "culture" },
    ]
  },
  {
    key: "gosaikunda",
    name: "Gosaikunda Holy Alpine Lake (4,380m)",
    slug: "gosaikunda-holy-lake",
    location: "Rasuwa, Bagmati Province",
    category: "lake",
    tag: "🌊 Lakes & Waters",
    images: [
      { url: "/images/destinations/manakamana/temple.jpg", caption: "Sacred Lake Dedicated to Lord Shiva", category: "lake" },
      { url: "/images/destinations/gorkha/durbar.jpg", caption: "Laurebina Pass (4,610m) View of Langtang", category: "mountain" },
      { url: "/images/destinations/phoksundo/lake.jpg", caption: "Surrounding Bhairav Kunda & Saraswati Kunda", category: "lake" },
      { url: "/images/destinations/manakamana/temple.jpg", caption: "Janai Purnima Pilgrim Festival Gathering", category: "culture" },
      { url: "/images/destinations/pathibhara/temple.jpg", caption: "Snow-Dusted Glacial Basin", category: "landscape" },
    ]
  },
  {
    key: "manaslu",
    name: "Manaslu Circuit Trek (8,163m)",
    slug: "manaslu-circuit-trek",
    location: "Gorkha, Gandaki Province",
    category: "mountain",
    tag: "🏔️ Mountains & Alpine",
    images: [
      { url: "/images/destinations/everest/base-camp.jpg", caption: "Mt. Manaslu 'Mountain of the Spirit'", category: "mountain" },
      { url: "/images/destinations/patan/durbar-square.jpg", caption: "Larkya La Pass (5,106m) Summit Crossing", category: "mountain" },
      { url: "/images/destinations/ghandruk/village.jpg", caption: "Samagaun Tibetan Buddhist Village", category: "village" },
      { url: "/images/destinations/pokhara/fewatal.jpg", caption: "Birendra Glacial Lake & Ice Falls", category: "lake" },
      { url: "/images/destinations/phoksundo/lake.jpg", caption: "Historic Mani Stone Walls & Chortens", category: "temple" },
    ]
  },
  {
    key: "dolpo",
    name: "Shey Phoksundo & Upper Dolpo",
    slug: "shey-phoksundo-national-park",
    location: "Dolpa, Karnali Province",
    category: "lake",
    tag: "🌊 Lakes & Waters",
    images: [
      { url: "/images/destinations/pokhara/fewatal.jpg", caption: "Deep Turquoise Water of Shey Phoksundo", category: "lake" },
      { url: "/images/destinations/ghandruk/village.jpg", caption: "Ringmo Bon Monastic Village", category: "culture" },
      { url: "/images/destinations/pokhara/fewatal.jpg", caption: "Suligad 167m High Waterfall", category: "nature" },
      { url: "/images/destinations/everest/base-camp.jpg", caption: "Yak Caravans across Trans-Himalayan Pass", category: "landscape" },
      { url: "/images/destinations/pokhara/fewatal.jpg", caption: "Shey Gompa Crystal Mountain Sanctuary", category: "temple" },
    ]
  },
  {
    key: "koshi-tappu",
    name: "Koshi Tappu Wildlife Reserve",
    slug: "koshi-tappu-wildlife-reserve",
    location: "Sunsari/Saptari, Koshi Province",
    category: "wildlife",
    tag: "🐅 Wildlife & Safaris",
    images: [
      { url: "/images/destinations/pokhara/fewatal.jpg", caption: "Last Surviving Wild Water Buffaloes (Arna)", category: "wildlife" },
      { url: "/images/destinations/pokhara/fewatal.jpg", caption: "Wetland Birdwatching Paradise (500+ Species)", category: "wildlife" },
      { url: "/images/destinations/tilicho/himalayan-lake.jpg", caption: "Saptakoshi River Floodplain Sunset", category: "lake" },
      { url: "/images/destinations/bardiya/tiger-reserve.jpg", caption: "Gangetic River Dolphin Observation", category: "nature" },
      { url: "/images/destinations/patan/durbar.jpg", caption: "Koshi Barrage & Migratory Flocks", category: "landscape" },
    ]
  },
  {
    key: "kathmandu",
    name: "Kathmandu Valley & Pashupatinath",
    slug: "pashupatinath-temple",
    location: "Kathmandu Valley, Bagmati Province",
    category: "temple",
    tag: "🏛️ Spiritual & UNESCO Heritage",
    images: [
      { url: "/images/destinations/manakamana/temple.jpg", caption: "Pashupatinath Temple on the Holy Bagmati River", category: "temple" },
      { url: "/images/destinations/manakamana/temple.jpg", caption: "Boudhanath Stupa Prayer Wheels & Kora", category: "temple" },
      { url: "/images/destinations/manakamana/temple.jpg", caption: "Swayambhunath Monkey Temple Hilltop", category: "temple" },
      { url: "/images/destinations/manakamana/temple.jpg", caption: "Kathmandu Durbar Square Taleju Temple", category: "heritage" },
      { url: "/images/destinations/gorkha/durbar.jpg", caption: "Evening Bagmati Ganga Aarti Ritual", category: "culture" },
    ]
  }
]

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

export default function Gallery() {
  const [selectedCategory, setSelectedCategory] = useState("all")
  const [searchQuery, setSearchQuery] = useState("")
  const [destinationsMedia, setDestinationsMedia] = useState([])

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
              ? [{ url: fallback, caption: dest.name, category: dest.category_name?.toLowerCase() || "landscape", source: "manual_correction" }]
              : preview.length ? preview.map((media) => ({
                  url: media.url,
                  caption: media.caption || dest.name,
                  category: dest.category_name?.toLowerCase() || "landscape",
                  photographer: media.photographer,
                  license: media.license,
                  source: media.source,
                  verification_status: media.verification_status,
                })) : (fallback ? [{ url: fallback, caption: dest.name, category: dest.category_name?.toLowerCase() || "landscape" }] : [])
            if (!images.length) return
            dynamicEntries.push({
              key: dest.slug || dest.id,
              name: dest.name,
              slug: dest.slug,
              location: `${dest.district || dest.city || "Nepal"}, ${dest.province || ""}`.replace(/, $/, ""),
              category: dest.category_name?.toLowerCase() || "landscape",
              tag: `🌿 Nepal Destination · ${images.length} image${images.length === 1 ? "" : "s"}`,
              images,
            })
          })
          setDestinationsMedia((current) => [...dynamicEntries, ...current.filter((entry) => String(entry.key).startsWith("district-"))])
        }
      })
      .catch(() => {})

    destinationApi.getDistrictGallery()
      .then(({ data }) => {
        const districtEntries = (data.districts || []).map((group) => ({
          key: `district-${group.district}`,
          name: `${group.district} District`,
          slug: group.images?.[0]?.destination_slug,
          location: `${group.district}, ${group.images?.[0]?.province || "Nepal"}`,
          category: "landscape",
          tag: `🗺️ District Gallery · ${group.images.length} image${group.images.length === 1 ? "" : "s"}`,
          images: group.images.map((media) => ({
            url: media.url, caption: media.caption || media.destination_name,
            category: "landscape", photographer: media.photographer,
            license: media.license, source: media.source,
          })),
        }))
        setDestinationsMedia((current) => [...current.filter((entry) => !String(entry.key).startsWith("district-")), ...districtEntries])
      })
      .catch(() => {})
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
