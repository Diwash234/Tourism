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
      { url: "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&q=80", caption: "Annapurna Base Camp Amphitheater", category: "mountain" },
      { url: "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&q=80", caption: "Machhapuchhre (Fishtail) Sunrise", category: "mountain" },
      { url: "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1200&q=80", caption: "Alpine Valley Hiking Trail", category: "mountain" },
      { url: "https://images.unsplash.com/photo-1486870591958-9b9d0d1dda99?w=1200&q=80", caption: "Glacial Stream & Suspension Bridge", category: "nature" },
      { url: "https://images.unsplash.com/photo-1483728642387-6c3bdd6c93e5?w=1200&q=80", caption: "Snow-Capped Annapurna South Peak", category: "mountain" },
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
      { url: "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=1200&q=80", caption: "Mt. Everest (8,848m) High Summit", category: "mountain" },
      { url: "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=1200&q=80", caption: "Namche Bazaar Sherpa Capital", category: "village" },
      { url: "https://images.unsplash.com/photo-1558981359-219d6364c9c8?w=1200&q=80", caption: "Tengboche Monastery with Everest Backdrop", category: "temple" },
      { url: "https://images.unsplash.com/photo-1486870591958-9b9d0d1dda99?w=1200&q=80", caption: "Khumbu Glacier & Icefall", category: "nature" },
      { url: "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&q=80", caption: "Prayer Flags at Kala Patthar (5,545m)", category: "mountain" },
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
      { url: "https://images.unsplash.com/photo-1502786129293-79981df4e689?w=1200&q=80", caption: "Phewa Lake with Colorful Wooden Boats", category: "lake" },
      { url: "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&q=80", caption: "Tal Barahi Island Temple at Sunset", category: "temple" },
      { url: "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1200&q=80", caption: "Sarangkot Sunrise Mountain View", category: "viewpoint" },
      { url: "https://images.unsplash.com/photo-1546484475-7f7bd55792da?w=1200&q=80", caption: "Paragliding over Lakeside Pokhara", category: "adventure" },
      { url: "https://images.unsplash.com/photo-1558981359-219d6364c9c8?w=1200&q=80", caption: "World Peace Pagoda Overlook", category: "temple" },
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
      { url: "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=1200&q=80", caption: "Walled Kingdom of Lo Manthang", category: "heritage" },
      { url: "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1200&q=80", caption: "Red Clay Canyon Cliffs & Caves", category: "landscape" },
      { url: "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&q=80", caption: "Ancient Tibetan Chortens", category: "temple" },
      { url: "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1200&q=80", caption: "Kali Gandaki River Valley", category: "landscape" },
      { url: "https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1200&q=80", caption: "Horse Caravans along Tibetan Border", category: "culture" },
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
      { url: "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=1200&q=80", caption: "Crystal Turquoise Waters of Rara Lake", category: "lake" },
      { url: "https://images.unsplash.com/photo-1439066615861-d1af74d74000?w=1200&q=80", caption: "Pine Forests Surrounding the Lake", category: "nature" },
      { url: "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1200&q=80", caption: "Murma Top Viewpoint Panorama", category: "viewpoint" },
      { url: "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1200&q=80", caption: "Wildflowers & Meadow Horse Riding", category: "landscape" },
      { url: "https://images.unsplash.com/photo-1502786129293-79981df4e689?w=1200&q=80", caption: "Morning Mist over Rara Mirror Lake", category: "lake" },
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
      { url: "https://images.unsplash.com/photo-1575550959106-5a7defe28b56?w=1200&q=80", caption: "One-Horned Rhinoceros in Grasslands", category: "wildlife" },
      { url: "https://images.unsplash.com/photo-1502786129293-79981df4e689?w=1200&q=80", caption: "Rapti River Sunset Canoe Ride", category: "lake" },
      { url: "https://images.unsplash.com/photo-1546182990-dffeafbe841d?w=1200&q=80", caption: "Bengal Tiger Track Safari", category: "wildlife" },
      { url: "https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1200&q=80", caption: "Tharu Cultural Stick Dance Performance", category: "culture" },
      { url: "https://images.unsplash.com/photo-1518709594023-6eab9bab7b23?w=1200&q=80", caption: "Gharial Crocodile Sanctuary", category: "wildlife" },
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
      { url: "https://images.unsplash.com/photo-1558981359-219d6364c9c8?w=1200&q=80", caption: "Maya Devi Temple & Sacred Pond", category: "temple" },
      { url: "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1200&q=80", caption: "Emperor Ashoka Pillar Inscription", category: "heritage" },
      { url: "https://images.unsplash.com/photo-1589308078058-c6dba4792c60?w=1200&q=80", caption: "World Peace Pagoda Lumbini", category: "temple" },
      { url: "https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1200&q=80", caption: "Eternal Peace Flame", category: "culture" },
      { url: "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&q=80", caption: "Monastic Zone Architecture", category: "temple" },
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
      { url: "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1200&q=80", caption: "55-Window Palace & Golden Gate", category: "heritage" },
      { url: "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&q=80", caption: "Nyatapola 5-Story Pagoda Temple", category: "temple" },
      { url: "https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1200&q=80", caption: "Pottery Square Clay Artisans", category: "culture" },
      { url: "https://images.unsplash.com/photo-1558981359-219d6364c9c8?w=1200&q=80", caption: "Dattatreya Square Ancient Wood Carvings", category: "heritage" },
      { url: "https://images.unsplash.com/photo-1568322445389-f64ac2515020?w=1200&q=80", caption: "Traditional Newari Brick Courtyards", category: "culture" },
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
      { url: "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&q=80", caption: "Krishna Mandir Stone Pagoda Architecture", category: "temple" },
      { url: "https://images.unsplash.com/photo-1558981359-219d6364c9c8?w=1200&q=80", caption: "Golden Temple (Hiranya Varna Mahavihar)", category: "temple" },
      { url: "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1200&q=80", caption: "Patan Museum Courtyard & Bronzes", category: "heritage" },
      { url: "https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1200&q=80", caption: "Mul Chowk Royal Bath Tusha Hiti", category: "heritage" },
      { url: "https://images.unsplash.com/photo-1568322445389-f64ac2515020?w=1200&q=80", caption: "Evening Oil Lamps at Durbar Square", category: "culture" },
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
      { url: "https://images.unsplash.com/photo-1570192977-f48187449e48?w=1200&q=80", caption: "Grand Janaki Temple (Naulakha Mandir)", category: "temple" },
      { url: "https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1200&q=80", caption: "Mithila Folk Painting Murals", category: "culture" },
      { url: "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1200&q=80", caption: "Ganga Sagar Holy Bathing Ghat", category: "lake" },
      { url: "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&q=80", caption: "Dhanush Sagar Temple Reflection", category: "temple" },
      { url: "https://images.unsplash.com/photo-1568322445389-f64ac2515020?w=1200&q=80", caption: "Vivah Mandap Monument", category: "culture" },
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
      { url: "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1200&q=80", caption: "Rolling Green Slopes of Kanyam Tea Estate", category: "landscape" },
      { url: "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1200&q=80", caption: "Horse Riding across Tea Plantations", category: "adventure" },
      { url: "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1200&q=80", caption: "Antu Danda Sunrise & Mt. Kanchenjunga", category: "viewpoint" },
      { url: "https://images.unsplash.com/photo-1439066615861-d1af74d74000?w=1200&q=80", caption: "Mai Pokhari Sacred Ramsar Wetland", category: "lake" },
      { url: "https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1200&q=80", caption: "Fresh Orthodox Tea Plucking Experience", category: "culture" },
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
      { url: "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1200&q=80", caption: "Nagarkot Sunrise over the Himalayan Range", category: "viewpoint" },
      { url: "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&q=80", caption: "View of 8 Himalayan Ranges from Tower", category: "mountain" },
      { url: "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1200&q=80", caption: "Pine Forest Nature Walking Trails", category: "nature" },
      { url: "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&q=80", caption: "Terraced Farmlands & Valley Clouds", category: "landscape" },
      { url: "https://images.unsplash.com/photo-1486870591958-9b9d0d1dda99?w=1200&q=80", caption: "Evening Golden Hour over Langtang", category: "viewpoint" },
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
      { url: "https://images.unsplash.com/photo-1439066615861-d1af74d74000?w=1200&q=80", caption: "One of the Highest Lakes in the World", category: "lake" },
      { url: "https://images.unsplash.com/photo-1483728642387-6c3bdd6c93e5?w=1200&q=80", caption: "Tilicho Peak (7,134m) Glacial Backdrop", category: "mountain" },
      { url: "https://images.unsplash.com/photo-1486870591958-9b9d0d1dda99?w=1200&q=80", caption: "High Landslide Scree Slope Trail", category: "adventure" },
      { url: "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=1200&q=80", caption: "Deep Indigo Blue Alpine Water", category: "lake" },
      { url: "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&q=80", caption: "Tilicho Base Camp Teahouses", category: "village" },
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
      { url: "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1200&q=80", caption: "Preserved 18th-Century Newari Main Street", category: "heritage" },
      { url: "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1200&q=80", caption: "Thani Mai Temple Sunrise Ridge", category: "viewpoint" },
      { url: "https://images.unsplash.com/photo-1518709594023-6eab9bab7b23?w=1200&q=80", caption: "Siddha Cave (Largest Cave in Nepal)", category: "nature" },
      { url: "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&q=80", caption: "Traditional Carved Wooden Balconies", category: "culture" },
      { url: "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1200&q=80", caption: "Silkworm Farm & Mountain Overlook", category: "landscape" },
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
      { url: "https://images.unsplash.com/photo-1546182990-dffeafbe841d?w=1200&q=80", caption: "Wild Royal Bengal Tiger in Riverbank", category: "wildlife" },
      { url: "https://images.unsplash.com/photo-1502786129293-79981df4e689?w=1200&q=80", caption: "Karnali River Rafting & Gangetic Dolphins", category: "lake" },
      { url: "https://images.unsplash.com/photo-1575550959106-5a7defe28b56?w=1200&q=80", caption: "Wild Asian Elephant Herd", category: "wildlife" },
      { url: "https://images.unsplash.com/photo-1518709594023-6eab9bab7b23?w=1200&q=80", caption: "Untamed Sal Hardwood Forests", category: "nature" },
      { url: "https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1200&q=80", caption: "Tharu Indigenous Community Homestay", category: "culture" },
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
      { url: "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=1200&q=80", caption: "Sacred Lake Dedicated to Lord Shiva", category: "lake" },
      { url: "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&q=80", caption: "Laurebina Pass (4,610m) View of Langtang", category: "mountain" },
      { url: "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1200&q=80", caption: "Surrounding Bhairav Kunda & Saraswati Kunda", category: "lake" },
      { url: "https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1200&q=80", caption: "Janai Purnima Pilgrim Festival Gathering", category: "culture" },
      { url: "https://images.unsplash.com/photo-1483728642387-6c3bdd6c93e5?w=1200&q=80", caption: "Snow-Dusted Glacial Basin", category: "landscape" },
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
      { url: "https://images.unsplash.com/photo-1483728642387-6c3bdd6c93e5?w=1200&q=80", caption: "Mt. Manaslu 'Mountain of the Spirit'", category: "mountain" },
      { url: "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=1200&q=80", caption: "Larkya La Pass (5,106m) Summit Crossing", category: "mountain" },
      { url: "https://images.unsplash.com/photo-1558981359-219d6364c9c8?w=1200&q=80", caption: "Samagaun Tibetan Buddhist Village", category: "village" },
      { url: "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=1200&q=80", caption: "Birendra Glacial Lake & Ice Falls", category: "lake" },
      { url: "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&q=80", caption: "Historic Mani Stone Walls & Chortens", category: "temple" },
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
      { url: "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=1200&q=80", caption: "Deep Turquoise Water of Shey Phoksundo", category: "lake" },
      { url: "https://images.unsplash.com/photo-1572953107300-18597face4ba?w=1200&q=80", caption: "Ringmo Bon Monastic Village", category: "culture" },
      { url: "https://images.unsplash.com/photo-1546484475-7f7bd55792da?w=1200&q=80", caption: "Suligad 167m High Waterfall", category: "nature" },
      { url: "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1200&q=80", caption: "Yak Caravans across Trans-Himalayan Pass", category: "landscape" },
      { url: "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&q=80", caption: "Shey Gompa Crystal Mountain Sanctuary", category: "temple" },
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
      { url: "https://images.unsplash.com/photo-1575550959106-5a7defe28b56?w=1200&q=80", caption: "Last Surviving Wild Water Buffaloes (Arna)", category: "wildlife" },
      { url: "https://images.unsplash.com/photo-1549366021-9f761d450615?w=1200&q=80", caption: "Wetland Birdwatching Paradise (500+ Species)", category: "wildlife" },
      { url: "https://images.unsplash.com/photo-1502786129293-79981df4e689?w=1200&q=80", caption: "Saptakoshi River Floodplain Sunset", category: "lake" },
      { url: "https://images.unsplash.com/photo-1518709594023-6eab9bab7b23?w=1200&q=80", caption: "Gangetic River Dolphin Observation", category: "nature" },
      { url: "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1200&q=80", caption: "Koshi Barrage & Migratory Flocks", category: "landscape" },
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
      { url: "https://images.unsplash.com/photo-1570192977-f48187449e48?w=1200&q=80", caption: "Pashupatinath Temple on the Holy Bagmati River", category: "temple" },
      { url: "https://images.unsplash.com/photo-1558981359-219d6364c9c8?w=1200&q=80", caption: "Boudhanath Stupa Prayer Wheels & Kora", category: "temple" },
      { url: "https://images.unsplash.com/photo-1589308078058-c6dba4792c60?w=1200&q=80", caption: "Swayambhunath Monkey Temple Hilltop", category: "temple" },
      { url: "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1200&q=80", caption: "Kathmandu Durbar Square Taleju Temple", category: "heritage" },
      { url: "https://images.unsplash.com/photo-1568322445389-f64ac2515020?w=1200&q=80", caption: "Evening Bagmati Ganga Aarti Ritual", category: "culture" },
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
  const [destinationsMedia, setDestinationsMedia] = useState(DESTINATIONS_MEDIA)

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
          const existingNames = new Set(DESTINATIONS_MEDIA.map((d) => d.name.toLowerCase()))
          const dynamicEntries = []
          list.forEach((dest) => {
            if (!dest.name || existingNames.has(dest.name.toLowerCase())) return
            existingNames.add(dest.name.toLowerCase())
            dynamicEntries.push({
              key: dest.slug || dest.id,
              name: dest.name,
              slug: dest.slug,
              location: `${dest.district || dest.city || "Nepal"}, ${dest.province || ""}`.replace(/, $/, ""),
              category: dest.category_name?.toLowerCase() || "landscape",
              tag: "🌿 Verified Nepal Destination",
              images: [
                {
                  url: getDestinationImageUrl(dest),
                  caption: dest.name,
                  category: dest.category_name?.toLowerCase() || "landscape",
                },
              ],
            })
          })
          setDestinationsMedia([...DESTINATIONS_MEDIA, ...dynamicEntries])
        }
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
          photographer: "Nepal Tourism Media Archive",
          license: "Creative Commons CC BY-SA 4.0",
        })
      })
    })
    setFlatPhotoList(all)
  }, [destinationsMedia])

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
          Explore over 100+ verified high-resolution photographs from Everest, Annapurna, Pokhara, Mustang, Rara, and all 7 Provinces with complete license and photographer attribution.
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
                      photographer: "Nepal Tourism Media Archive",
                      license: "Creative Commons CC BY-SA 4.0",
                    }, globalIdx)}
                  >
                    <div className="h-40 w-full relative overflow-hidden">
                      <img
                        src={img.url}
                        alt={img.caption}
                        loading="lazy"
                        onError={(e) => {
                          e.target.onerror = null;
                          e.target.src = "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&auto=format&fit=crop&q=80";
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
                      <p className="text-[9px] text-emerald-600 font-mono">✓ CC BY-SA 4.0</p>
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
                  e.target.onerror = null;
                  e.target.src = "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&auto=format&fit=crop&q=80";
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
                      e.target.onerror = null;
                      e.target.src = "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&auto=format&fit=crop&q=80";
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
