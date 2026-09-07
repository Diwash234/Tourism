// A sample dataset of real Nepal destinations used as a local fallback so the
// Explore/Recommendation/Trip Planner pages have rich content (images, budget
// estimates, heritage info) even before the backend dataset is fully wired up.
// Once the backend's `/destinations` and `/recommendations` endpoints return
// data, that data takes priority — this file is only used as a fallback.

const nepalDestinations = [
  {
    id: "np-ktm-durbar",
    name: "Kathmandu Durbar Square",
    location: "Kathmandu, Bagmati Province",
    category: "heritage",
    isHeritage: true,
    rating: 4.7,
    price: 15,
    image: "/images/destinations/kathmandu/durbar-square.jpg",
    gallery: [
      "/images/destinations/kathmandu/durbar-square.jpg",
      "/images/destinations/kathmandu/durbar-square.jpg",
    ],
    description:
      "A UNESCO World Heritage Site featuring ancient palaces, courtyards and temples that once housed Nepal's royal families.",
    localLanguage: "Nepali, Newari",
    heritageDescription:
      "Home to the Hanuman Dhoka Palace complex, the Kumari Ghar (residence of the Living Goddess), and dozens of pagoda-style temples dating back to the Malla era.",
    heritageSites: [
      { name: "Hanuman Dhoka Palace", image: "/images/destinations/kathmandu/durbar-square.jpg" },
      { name: "Kumari Ghar", image: "/images/destinations/nagarkot/sunrise-view.jpg" },
      { name: "Taleju Temple", image: "/images/destinations/manakamana/temple.jpg" },
    ],
    coordinates: { lat: 27.7040, lng: 85.3070 },
  },
  {
    id: "np-pokhara-phewa",
    name: "Phewa Lake, Pokhara",
    location: "Pokhara, Gandaki Province",
    category: "lakes",
    isHeritage: false,
    rating: 4.8,
    price: 25,
    image: "/images/destinations/pokhara/fewatal.jpg",
    gallery: [
      "/images/destinations/pokhara/fewatal.jpg",
      "/images/destinations/pokhara/fewatal.jpg",
    ],
    description:
      "A serene lake framed by the Annapurna range, popular for boating, lakeside cafes, and views of the Machapuchare peak reflected on the water.",
    localLanguage: "Nepali, Gurung",
    coordinates: { lat: 28.2096, lng: 83.9856 },
  },
  {
    id: "np-chitwan",
    name: "Chitwan National Park",
    location: "Chitwan, Bagmati Province",
    category: "adventure",
    isHeritage: false,
    rating: 4.6,
    price: 60,
    image: "/images/destinations/chitwan/safari.jpg",
    gallery: [
      "/images/destinations/chitwan/safari.jpg",
    ],
    description:
      "A UNESCO World Heritage jungle reserve known for one-horned rhino and Bengal tiger safaris, canoe rides, and Tharu cultural villages.",
    localLanguage: "Tharu, Nepali",
    coordinates: { lat: 27.5291, lng: 84.3542 },
  },
  {
    id: "np-lumbini",
    name: "Lumbini",
    location: "Lumbini, Province No. 5",
    category: "heritage",
    isHeritage: true,
    rating: 4.9,
    price: 20,
    image: "/images/destinations/manakamana/temple.jpg",
    description:
      "The birthplace of Lord Buddha, home to the sacred Maya Devi Temple and monasteries built by Buddhist communities from around the world.",
    localLanguage: "Awadhi, Bhojpuri, Nepali",
    heritageDescription:
      "A UNESCO World Heritage pilgrimage site with the Ashoka Pillar, the sacred garden, and the eternal flame for world peace.",
    heritageSites: [
      { name: "Maya Devi Temple", image: "/images/destinations/manakamana/temple.jpg" },
      { name: "Ashoka Pillar", image: "/images/destinations/everest/base-camp.jpg" },
    ],
    coordinates: { lat: 27.4833, lng: 83.2767 },
  },
  {
    id: "np-everest-base-camp",
    name: "Everest Base Camp Trek",
    location: "Solukhumbu, Province No. 1",
    category: "adventure",
    isHeritage: false,
    rating: 4.9,
    price: 900,
    image: "/images/destinations/everest/base-camp.jpg",
    description:
      "A multi-day trek through Sherpa villages, suspension bridges, and Himalayan monasteries to the base of the world's tallest mountain.",
    localLanguage: "Sherpa, Nepali",
    coordinates: { lat: 27.9881, lng: 86.9250 },
  },
  {
    id: "np-bhaktapur",
    name: "Bhaktapur Durbar Square",
    location: "Bhaktapur, Bagmati Province",
    category: "heritage",
    isHeritage: true,
    rating: 4.8,
    price: 15,
    image: "/images/destinations/kathmandu/durbar-square.jpg",
    description:
      "A beautifully preserved medieval city known for pottery squares, wood carvings, and the iconic Nyatapola Temple.",
    localLanguage: "Newari, Nepali",
    heritageDescription:
      "The best-preserved of Kathmandu Valley's three durbar squares, famous for its Peacock Window and traditional pottery-making community.",
    heritageSites: [
      { name: "Nyatapola Temple", image: "/images/destinations/manakamana/temple.jpg" },
      { name: "Pottery Square", image: "/images/destinations/kathmandu/durbar-square.jpg" },
    ],
    coordinates: { lat: 27.6710, lng: 85.4298 },
  },
  {
    id: "np-mustang",
    name: "Upper Mustang",
    location: "Mustang, Gandaki Province",
    category: "adventure",
    isHeritage: true,
    rating: 4.7,
    price: 450,
    image: "/images/destinations/everest/base-camp.jpg",
    description:
      "A remote former kingdom with dramatic desert-like cliffs, ancient cave monasteries, and the walled city of Lo Manthang.",
    localLanguage: "Tibetan, Nepali",
    coordinates: { lat: 29.1867, lng: 83.9642 },
  },
  {
    id: "np-rara",
    name: "Rara Lake",
    location: "Mugu, Karnali Province",
    category: "lakes",
    isHeritage: false,
    rating: 4.6,
    price: 300,
    image: "/images/destinations/pokhara/fewatal.jpg",
    description:
      "Nepal's largest lake, tucked inside Rara National Park — remote, pristine, and surrounded by pine forest.",
    localLanguage: "Nepali",
    coordinates: { lat: 29.5330, lng: 82.0850 },
  },
  {
    id: "np-patan",
    name: "Patan Durbar Square",
    location: "Lalitpur, Bagmati Province",
    category: "heritage",
    isHeritage: true,
    rating: 4.8,
    price: 15,
    image: "/images/destinations/kathmandu/durbar-square.jpg",
    description:
      "Known as the city of fine arts, famed for intricate metal and stone craftsmanship and the Patan Museum.",
    localLanguage: "Newari, Nepali",
    heritageDescription:
      "One of the three medieval royal cities of the Kathmandu Valley, celebrated for its Krishna Mandir and traditional Newari architecture.",
    heritageSites: [
      { name: "Krishna Mandir", image: "/images/destinations/manakamana/temple.jpg" },
      { name: "Patan Museum", image: "/images/destinations/kathmandu/durbar-square.jpg" },
    ],
    coordinates: { lat: 27.6727, lng: 85.3247 },
  },
  {
    id: "np-annapurna",
    name: "Annapurna Base Camp Trek",
    location: "Kaski, Gandaki Province",
    category: "adventure",
    isHeritage: false,
    rating: 4.9,
    price: 550,
    image: "/images/destinations/everest/base-camp.jpg",
    description:
      "A classic trek through rhododendron forests and Gurung villages, ending in a natural amphitheater surrounded by 7,000m peaks.",
    localLanguage: "Gurung, Nepali",
    coordinates: { lat: 28.5309, lng: 83.8792 },
  },
  {
    id: "np-janakpur",
    name: "Janakpur (Janaki Mandir)",
    location: "Dhanusha, Madhesh Province",
    category: "heritage",
    isHeritage: true,
    rating: 4.5,
    price: 10,
    image: "/images/destinations/manakamana/temple.jpg",
    description:
      "A major Hindu pilgrimage city and birthplace of Goddess Sita, famous for the ornate white Janaki Mandir temple.",
    localLanguage: "Maithili, Bhojpuri, Nepali",
    heritageDescription:
      "The Janaki Mandir blends Mughal and Rajput architectural styles and hosts the annual Vivaha Panchami celebration.",
    heritageSites: [
      { name: "Janaki Mandir", image: "/images/destinations/manakamana/temple.jpg" },
    ],
    coordinates: { lat: 26.7288, lng: 85.9247 },
  },
  {
    id: "np-ilam",
    name: "Ilam Tea Gardens",
    location: "Ilam, Koshi Province",
    category: "nature",
    isHeritage: false,
    rating: 4.6,
    price: 40,
    image: "/images/destinations/ilam/tea-gardens.jpg",
    description:
      "Rolling green tea estates in the eastern hills, known for organic tea production and misty mountain views.",
    localLanguage: "Nepali, Limbu, Rai",
    coordinates: { lat: 26.9088, lng: 87.9257 },
  },
]

export default nepalDestinations

export const searchDestinations = (query = "", category = "") => {
  const q = query.trim().toLowerCase()
  return nepalDestinations.filter((d) => {
    const matchesQuery =
      !q ||
      d.name.toLowerCase().includes(q) ||
      d.location.toLowerCase().includes(q) ||
      d.category.toLowerCase().includes(q)
    const matchesCategory = !category || d.category === category
    return matchesQuery && matchesCategory
  })
}

export const getDestinationById = (id) => nepalDestinations.find((d) => d.id === id)